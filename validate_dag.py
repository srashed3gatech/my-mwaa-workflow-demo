#!/usr/bin/env python3
"""
Pre-deployment DAG validation script
Run this before CDK deployment to catch DAG issues early
"""

import sys
import os
import ast
from pathlib import Path

def validate_syntax():
    """Validate Python syntax for DAG files"""
    print("🔍 Validating DAG syntax...")
    
    dag_files = [
        "assets/mwaa_dags/dags/scripts/mwaa_blogpost_data_pipeline.py",
        "assets/mwaa_dags/dags/custom/glue_trigger_crawler_operator.py"
    ]
    
    for file_path in dag_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    ast.parse(f.read())
                print(f"  ✅ {os.path.basename(file_path)}")
            except SyntaxError as e:
                print(f"  ❌ Syntax error in {file_path}: {e}")
                return False
        else:
            print(f"  ⚠️  File not found: {file_path}")
            return False
    
    return True

def validate_imports():
    """Test that DAG imports work correctly"""
    print("📥 Validating DAG imports...")
    
    # Add DAGs directory to path
    dags_path = os.path.join(os.getcwd(), "assets", "mwaa_dags", "dags")
    if dags_path not in sys.path:
        sys.path.insert(0, dags_path)
    
    try:
        # Mock Airflow Variables to avoid dependency issues
        import unittest.mock
        with unittest.mock.patch('airflow.models.Variable.get', return_value='test-value'):
            # Test custom operator
            from custom.glue_trigger_crawler_operator import GlueTriggerCrawlerOperator
            print("  ✅ Custom Glue operator")
            
            # Test main DAG
            from scripts.mwaa_blogpost_data_pipeline import dag
            print("  ✅ Main DAG")
            
            # Basic validation
            if dag.dag_id != 'mwaa_blogpost_data_pipeline':
                print(f"  ❌ Unexpected DAG ID: {dag.dag_id}")
                return False
            
            if len(dag.tasks) == 0:
                print("  ❌ No tasks found in DAG")
                return False
            
            print(f"  ✅ DAG structure (found {len(dag.tasks)} tasks)")
            
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def validate_requirements():
    """Check that requirements.txt includes necessary dependencies"""
    print("📦 Validating requirements...")
    
    req_file = "requirements.txt"
    if not os.path.exists(req_file):
        print(f"  ❌ {req_file} not found")
        return False
    
    with open(req_file, 'r') as f:
        requirements = f.read().lower()
    
    required_packages = [
        'apache-airflow-providers-amazon',
        'boto3'
    ]
    
    for package in required_packages:
        if package not in requirements:
            print(f"  ❌ Missing required package: {package}")
            return False
        else:
            print(f"  ✅ {package}")
    
    return True

def main():
    """Main validation function"""
    print("🚀 Pre-deployment DAG Validation")
    print("=" * 40)
    
    # Change to project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    all_passed = True
    
    # Run validations
    if not validate_syntax():
        all_passed = False
    
    if not validate_imports():
        all_passed = False
    
    if not validate_requirements():
        all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("✅ All validations passed! Ready for deployment.")
        return 0
    else:
        print("❌ Validation failed! Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
