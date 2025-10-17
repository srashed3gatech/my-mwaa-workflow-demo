# Build and Test Guide

This guide explains how to build, test, and validate the MWAA Workflow Demo before deployment.

## 🚀 Quick Start

```bash
# 1. Setup environment and install dependencies
make dev-setup
source .env/bin/activate

# 2. Run full build and test suite
make build

# 3. Deploy (only after successful build)
make deploy
```

## 📋 Available Commands

### Setup Commands
```bash
make help              # Show all available commands
make setup-env         # Create Python virtual environment
make install           # Install all dependencies
make dev-setup         # Complete development setup
make check-deps        # Verify all dependencies are installed
```

### Testing Commands
```bash
make test              # Run all tests (recommended)
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-dag          # Test DAG syntax and imports
make quick-test        # Run essential tests quickly
```

### Validation Commands
```bash
make validate          # Validate CDK templates
make validate-dag      # Validate Airflow DAG files
make lint              # Run code linting (flake8, pylint)
```

### Build Commands
```bash
make build             # Complete build process (recommended before deploy)
make synth             # Synthesize CDK templates only
```

### Deployment Commands
```bash
make deploy-dry-run    # Show what would be deployed
make deploy            # Deploy all stacks (runs build first)
make destroy           # Destroy all stacks
```

### Utility Commands
```bash
make clean             # Clean build artifacts and cache
make pre-commit        # Run pre-commit checks
```

## 🔍 Detailed Testing Strategy

### 1. Unit Tests
Tests individual components in isolation:
- **MWAAStack creation and configuration**
- **Variable generation from CloudFormation**
- **MWAA API integration classes**
- **DAG structure and task validation**

```bash
make test-unit
```

### 2. Integration Tests
Tests component interactions:
- **CDK stack integration**
- **CloudFormation output parsing**
- **MWAA API workflow simulation**
- **End-to-end workflow validation**

```bash
make test-integration
```

### 3. DAG Validation
Tests Airflow DAG files:
- **DAG import and syntax validation**
- **Task dependency verification**
- **Airflow compatibility checks**

```bash
make test-dag
```

### 4. Code Quality
Ensures code quality and standards:
- **flake8**: Style and syntax checking
- **pylint**: Code quality analysis
- **CDK template validation**

```bash
make lint
make validate
```

## 🏗️ Build Process

The `make build` command runs the complete validation pipeline:

1. **Dependency Check** - Verifies all required packages
2. **Code Linting** - Checks code quality and style
3. **Unit Tests** - Tests individual components
4. **Integration Tests** - Tests component interactions
5. **DAG Validation** - Validates Airflow DAGs
6. **CDK Validation** - Validates CloudFormation templates
7. **Template Synthesis** - Generates final CDK templates

```bash
make build
```

**Output Example:**
```
🔍 Checking dependencies...
✅ All dependencies are installed

🔍 Running code linting...
✅ Linting completed

🧪 Running unit tests...
✅ Unit tests completed

🔗 Running integration tests...
✅ Integration tests completed

🌊 Validating Airflow DAG files...
✅ DAG validation completed

✅ Validating CDK templates and configuration...
✅ CDK validation completed

🏗️  Building project...
✅ Build completed successfully
🚀 Ready for deployment!
```

## 🧪 Test Coverage

### Unit Test Coverage
- ✅ MWAAStack import and initialization
- ✅ MWAA execution role creation
- ✅ Security group configuration
- ✅ MWAA environment setup
- ✅ Variable generation functions
- ✅ MWAA API integration classes
- ✅ DAG enablement functions

### Integration Test Coverage
- ✅ CloudFormation stack integration
- ✅ MWAA API workflow simulation
- ✅ CDK stack component integration
- ✅ DAG import and validation
- ✅ End-to-end workflow simulation

### Validation Coverage
- ✅ CDK template synthesis
- ✅ CloudFormation template validation
- ✅ Airflow DAG syntax checking
- ✅ Python code quality (flake8, pylint)
- ✅ Import dependency verification

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Problem: ModuleNotFoundError
# Solution: Install dependencies
make install
```

#### 2. CDK Synthesis Errors
```bash
# Problem: CDK template validation fails
# Solution: Check CDK code and run validation
make validate
```

#### 3. DAG Import Errors
```bash
# Problem: Airflow DAG import fails
# Solution: Validate DAG syntax
make validate-dag
```

#### 4. Test Failures
```bash
# Problem: Tests are failing
# Solution: Run specific test categories
make test-unit        # Check unit tests
make test-integration # Check integration tests
```

### Debug Mode

For detailed debugging, run individual components:

```bash
# Test specific functionality
python -c "from cdk_mwaa_blogpost.MWAAStack import MWAAStack; print('✅ MWAAStack OK')"

# Test DAG import
python -c "
import sys
sys.path.insert(0, 'assets/mwaa_dags/dags')
from unittest.mock import patch
with patch('airflow.models.Variable.get', return_value='test'):
    from scripts.mwaa_blogpost_data_pipeline import dag
    print(f'✅ DAG OK: {dag.dag_id}')
"

# Test variable generation
python -c "from post_scripts.CreateMWAAVariables import generate_variables_from_stacks; print('✅ Variables OK')"
```

## 📊 Performance Benchmarks

### Expected Test Times
- **Unit Tests**: ~30 seconds
- **Integration Tests**: ~45 seconds  
- **DAG Validation**: ~15 seconds
- **Code Linting**: ~20 seconds
- **CDK Synthesis**: ~30 seconds
- **Total Build Time**: ~2-3 minutes

### Expected Deployment Times
- **VPC Stack**: ~2-3 minutes
- **S3/Data Lake Stack**: ~1-2 minutes
- **IAM Stack**: ~2-3 minutes
- **MWAA Stack**: ~15-20 minutes
- **Total Deployment**: ~20-25 minutes

## 🔒 Security Considerations

### Pre-Deployment Checks
- ✅ IAM roles have minimal required permissions
- ✅ Security groups follow least privilege principle
- ✅ S3 buckets have proper access controls
- ✅ MWAA environment uses private subnets
- ✅ No hardcoded credentials in code

### Validation Steps
```bash
# Check for security issues
make lint                    # Includes security linting
make validate               # Validates IAM policies
grep -r "password\|secret" . # Check for hardcoded secrets
```

## 📈 Continuous Integration

### Recommended CI Pipeline
```yaml
# Example GitHub Actions workflow
name: Build and Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: make ci-test
```

### Pre-Commit Hooks
```bash
# Setup pre-commit validation
make pre-commit
```

This runs essential checks before each commit:
- Code linting
- Unit tests
- DAG validation

## 🎯 Best Practices

### Before Every Deployment
1. **Always run full build**: `make build`
2. **Review deployment plan**: `make deploy-dry-run`
3. **Verify AWS credentials**: `aws sts get-caller-identity`
4. **Check AWS region**: Ensure correct region is configured

### Development Workflow
1. **Make changes**
2. **Run quick tests**: `make quick-test`
3. **Run full build**: `make build`
4. **Deploy to test environment**: `make deploy`
5. **Validate functionality**
6. **Clean up**: `make destroy`

### Code Quality
- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include type hints where appropriate
- Write tests for new functionality
- Keep functions small and focused

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [Amazon MWAA Documentation](https://docs.aws.amazon.com/mwaa/)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
