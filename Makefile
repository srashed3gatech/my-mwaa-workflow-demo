# MWAA Workflow Demo - Build and Test Makefile
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

.PHONY: help install test test-unit test-integration lint validate build deploy clean

# Default target
help:
	@echo "MWAA Workflow Demo - Build and Test Commands"
	@echo "============================================="
	@echo ""
	@echo "Setup Commands:"
	@echo "  install          Install all dependencies"
	@echo "  setup-env        Setup Python virtual environment"
	@echo ""
	@echo "Testing Commands:"
	@echo "  test             Run all tests (unit + integration + validation)"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-dag         Test DAG syntax and imports"
	@echo ""
	@echo "Validation Commands:"
	@echo "  lint             Run code linting (flake8, pylint)"
	@echo "  validate         Validate CDK templates and configuration"
	@echo "  validate-dag     Validate Airflow DAG files"
	@echo ""
	@echo "Build Commands:"
	@echo "  build            Build and validate everything (recommended before deploy)"
	@echo "  synth            Synthesize CDK templates"
	@echo ""
	@echo "Deployment Commands:"
	@echo "  deploy           Deploy all stacks (runs build first)"
	@echo "  deploy-dry-run   Show what would be deployed"
	@echo "  destroy          Destroy all stacks"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  check-deps       Check if all dependencies are installed"

# Setup Commands
install: check-python
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed successfully"

setup-env:
	@echo "🐍 Setting up Python virtual environment..."
	python3 -m venv .env
	@echo "✅ Virtual environment created"
	@echo "💡 Activate with: source .env/bin/activate"

# Testing Commands
test: test-unit test-integration validate-dag
	@echo "🎉 All tests passed!"

test-unit:
	@echo "🧪 Running unit tests..."
	python -m pytest tests/test_mwaa_automation.py -v
	python -m pytest tests/test_mwaa_blogpost_data_pipeline.py -v
	@echo "✅ Unit tests completed"

test-integration:
	@echo "🔗 Running integration tests..."
	python -c "from tests.integration_test import run_integration_tests; run_integration_tests()"
	@echo "✅ Integration tests completed"

test-dag:
	@echo "🌊 Testing DAG syntax and imports..."
	python tests/validate_dag.py
	@echo "✅ DAG tests completed"

# Validation Commands
lint:
	@echo "🔍 Running code linting..."
	@echo "Checking Python files with flake8..."
	-flake8 --max-line-length=120 --ignore=E501,W503 cdk_mwaa_blogpost/ post_scripts/ tests/
	@echo "Checking Python files with pylint..."
	-pylint --disable=C0114,C0115,C0116 cdk_mwaa_blogpost/ post_scripts/
	@echo "✅ Linting completed"

validate:
	@echo "✅ Validating CDK templates and configuration..."
	cdk synth --quiet > /dev/null
	@echo "✅ CDK validation completed"

validate-dag:
	@echo "🌊 Validating Airflow DAG files..."
	@python -c "\
import sys; \
sys.path.insert(0, 'assets/mwaa_dags/dags'); \
from unittest.mock import patch; \
try: \
    with patch('airflow.models.Variable.get', return_value='test'): \
        from scripts.mwaa_blogpost_data_pipeline import dag; \
        print('✅ DAG import successful'); \
        print(f'✅ DAG ID: {dag.dag_id}'); \
        print(f'✅ Task count: {len(dag.tasks)}'); \
except Exception as e: \
    print(f'❌ DAG validation failed: {e}'); \
    sys.exit(1)"
	@echo "✅ DAG validation completed"

# Build Commands
build: check-deps lint test validate
	@echo "🏗️  Building project..."
	cdk synth --quiet
	@echo "✅ Build completed successfully"
	@echo "🚀 Ready for deployment!"

synth:
	@echo "🏗️  Synthesizing CDK templates..."
	cdk synth
	@echo "✅ CDK synthesis completed"

# Deployment Commands
deploy: build
	@echo "🚀 Deploying MWAA workflow demo..."
	@echo "⚠️  This will create AWS resources that may incur charges"
	@read -p "Continue with deployment? [y/N] " confirm && [ "$$confirm" = "y" ]
	cdk deploy --all --require-approval never
	@echo "✅ Deployment completed!"
	@echo "📋 Next steps:"
	@echo "   1. Check MWAA environment status in AWS Console"
	@echo "   2. Variables should be automatically loaded"
	@echo "   3. DAGs should be automatically enabled"

deploy-dry-run:
	@echo "🔍 Showing deployment plan (dry run)..."
	cdk diff --all

destroy:
	@echo "💥 Destroying all stacks..."
	@echo "⚠️  This will delete all AWS resources created by this demo"
	@read -p "Are you sure you want to destroy everything? [y/N] " confirm && [ "$$confirm" = "y" ]
	cdk destroy --all --force

# Utility Commands
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf cdk.out/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
	rm -f post_scripts/mwaa_demo_variables.json
	@echo "✅ Cleanup completed"

check-deps:
	@python scripts/check_deps.py

check-python:
	@echo "� Checking Python version..."
	@python3 --version | grep -E "Python 3\.(8|9|10|11|12)" || (echo "❌ Python 3.8+ required" && exit 1)
	@echo "✅ Python version OK"

# Development workflow targets
dev-setup: setup-env install
	@echo "🎯 Development environment setup complete!"
	@echo "💡 Run 'source .env/bin/activate' to activate virtual environment"

pre-commit: lint test-unit validate-dag
	@echo "✅ Pre-commit checks passed!"

ci-test: install test validate
	@echo "✅ CI tests completed!"

# Quick commands for common workflows
quick-test: test-unit validate-dag
	@echo "⚡ Quick tests completed!"

full-test: test
	@echo "🎯 Full test suite completed!"
