#!/bin/bash
# Enhanced deployment script with DAG validation
# This replaces your original deployment commands with built-in validation

set -e  # Exit on any error

echo "🚀 MWAA Deployment with DAG Validation"
echo "======================================"

# Step 1: Validate DAG before any deployment
echo "Step 1: Validating DAG..."
python3 validate_dag.py
if [ $? -ne 0 ]; then
    echo "❌ DAG validation failed! Aborting deployment."
    exit 1
fi
echo "✅ DAG validation passed!"
echo ""

# Step 2: Install global dependencies
echo "Step 2: Installing global dependencies..."
npm install -g aws-cdk
echo ""

# Step 3: Navigate to project directory
echo "Step 3: Setting up project environment..."
cd ~/environment/amazon-mwaa-workflow-demo || {
    echo "❌ Could not find project directory. Please adjust the path."
    exit 1
}

# Step 4: Create and activate virtual environment
echo "Step 4: Setting up Python environment..."
python3 -m venv .env
source .env/bin/activate

# Step 5: Install Python dependencies
echo "Step 5: Installing Python dependencies..."
pip install -r requirements.txt

# Step 6: Set up AWS credentials
echo "Step 6: Setting up AWS credentials..."
export DEV_ACCOUNT_ID=992382677689
ada credentials update --account=$DEV_ACCOUNT_ID --provider=isengard --role=Admin --once

# Step 7: Bootstrap CDK
echo "Step 7: Bootstrapping CDK..."
cdk bootstrap --context region=us-west-2

# Step 8: Deploy all stacks
echo "Step 8: Deploying CDK stacks..."
cdk deploy --all --context region=us-west-2

echo ""
echo "🎉 Deployment completed successfully!"
echo "✅ DAG validation: PASSED"
echo "✅ CDK deployment: COMPLETED"
echo ""
echo "Next steps:"
echo "1. Check the AWS Console for your MWAA environment"
echo "2. Upload your DAG files to the S3 DAGs bucket"
echo "3. Monitor the Airflow UI for any runtime issues"
