# Makefile for MWAA Blogpost Data Pipeline
# Provides convenient commands for testing and deployment

.PHONY: help test test-syntax test-imports test-unit install-deps clean deploy

# Default target
help:
	@echo "MWAA Blogpost Data Pipeline - Available Commands:"
	@echo "================================================"
	@echo "make test          - Run all tests (syntax, imports, unit tests)"
	@echo "make test-syntax   - Run Python syntax validation only"
	@echo "make test-imports  - Test DAG imports only"
	@echo "make test-unit     - Run unit tests only"
	@echo "make install-deps  - Install test dependencies"
	@echo "make clean         - Clean up temporary files"
	@echo "make deploy        - Deploy to AWS (after tests pass)"
	@echo ""
	@echo "Quick Start:"
	@echo "1. make install-deps"
	@echo "2. make test"
	@echo "3. make deploy (if tests pass)"

# Install test dependencies
install-deps:
	@echo "📦 Installing test dependencies..."
	pip install apache-airflow>=2.5.0 apache-airflow-providers-amazon>=8.0.0 boto3 requests

# Run all tests
test:
	@echo "🚀 Running comprehensive test suite..."
	python run_tests.py

# Run syntax check only
test-syntax:
	@echo "🔍 Running syntax checks..."
	python -m py_compile assets/mwaa_dags/dags/scripts/mwaa_blogpost_data_pipeline.py
	python -m py_compile assets/mwaa_dags/dags/custom/glue_trigger_crawler_operator.py
	@echo "✅ Syntax checks passed"

# Test imports only
test-imports:
	@echo "📥 Testing DAG imports..."
	@cd assets/mwaa_dags/dags && python -c "import sys; sys.path.insert(0, '.'); from unittest.mock import patch; patch('airflow.models.Variable.get', return_value='test').start(); from scripts.mwaa_blogpost_data_pipeline import dag; from custom.glue_trigger_crawler_operator import GlueTriggerCrawlerOperator; print('✅ All imports successful')"

# Run unit tests only
test-unit:
	@echo "🧪 Running unit tests..."
	python tests/test_mwaa_blogpost_data_pipeline.py

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Deploy to AWS (run validation first)
deploy: validate
	@echo "🚀 Deploying to AWS..."
	@echo "📋 Pre-deployment checklist:"
	@echo "   ✅ DAG validation passed"
	@echo "   ⚠️  Make sure you have AWS credentials configured"
	@echo "   ⚠️  Make sure you have the correct AWS account/region set"
	@echo ""
	@read -p "Continue with deployment? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo "Installing dependencies..."
	python3 -m venv .env || true
	. .env/bin/activate && pip install -r requirements.txt
	@echo "Updating AWS credentials..."
	ada credentials update --account=$(DEV_ACCOUNT_ID) --provider=isengard --role=Admin --once
	@echo "Bootstrapping CDK..."
	. .env/bin/activate && cdk bootstrap --context region=us-west-2
	@echo "Deploying stacks..."
	. .env/bin/activate && cdk deploy --all --context region=us-west-2
	@echo "🎉 Deployment complete!"

# Quick validation (faster than full test suite)
validate:
	@echo "⚡ Quick validation..."
	@make test-syntax
	@make test-imports
	@echo "✅ Quick validation passed"
