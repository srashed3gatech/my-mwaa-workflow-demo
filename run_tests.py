#!/usr/bin/env python3
"""
Test runner for MWAA Blogpost Data Pipeline
Run this script to validate your DAG before deployment
"""

import sys
import os
import subprocess
from pathlib import Path

def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "apache-airflow>=2.5.0",
            "apache-airflow-providers-amazon>=8.0.0",
            "boto3",
            "requests"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_syntax_check():
    """Run Python syntax check on DAG files"""
    print("\n🔍 Running syntax checks...")
    
    dag_files = [
        "assets/mwaa_dags/dags/scripts/mwaa_blogpost_data_pipeline.py",
        "assets/mwaa_dags/dags/custom/glue_trigger_crawler_operator.py"
    ]
    
    for file_path in dag_files:
        if os.path.exists(file_path):
            try:
                subprocess.check_call([sys.executable, "-m", "py_compile", file_path])
                print(f"✅ Syntax check passed: {file_path}")
            except subprocess.CalledProcessError:
                print(f"❌ Syntax error in: {file_path}")
                return False
        else:
            print(f"⚠️  File not found: {file_path}")
    
    return True

def run_import_test():
    """Test that DAG can be imported without errors"""
    print("\n📥 Testing DAG imports...")
    
    # Add the DAGs directory to Python path
    dags_path = os.path.join(os.getcwd(), "assets", "mwaa_dags", "dags")
    if dags_path not in sys.path:
        sys.path.insert(0, dags_path)
    
    try:
        # Mock Airflow Variables for testing
        import unittest.mock
        with unittest.mock.patch('airflow.models.Variable.get', return_value='test-value'):
            # Test custom operator import
            from custom.glue_trigger_crawler_operator import GlueTriggerCrawlerOperator
            print("✅ Custom Glue operator imported successfully")
            
            # Test main DAG import
            from scripts.mwaa_blogpost_data_pipeline import dag
            print("✅ Main DAG imported successfully")
            
            # Basic DAG validation
            assert dag.dag_id == 'mwaa_blogpost_data_pipeline'
            assert len(dag.tasks) > 0
            print(f"✅ DAG validation passed - Found {len(dag.tasks)} tasks")
            
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def run_unit_tests():
    """Run the comprehensive unit test suite"""
    print("\n🧪 Running unit tests...")
    
    test_file = "tests/test_mwaa_blogpost_data_pipeline.py"
    if os.path.exists(test_file):
        try:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Unit tests failed: {e}")
            return False
    else:
        print(f"⚠️  Test file not found: {test_file}")
        return False

def main():
    """Main test runner"""
    print("🚀 MWAA DAG Test Runner")
    print("=" * 50)
    
    # Change to the project directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    all_passed = True
    
    # Step 1: Install dependencies (optional, comment out if already installed)
    # if not install_test_dependencies():
    #     all_passed = False
    
    # Step 2: Syntax check
    if not run_syntax_check():
        all_passed = False
    
    # Step 3: Import test
    if not run_import_test():
        all_passed = False
    
    # Step 4: Unit tests
    if not run_unit_tests():
        all_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Your DAG is ready for deployment.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please fix the issues before deployment.")
        sys.exit(1)

if __name__ == "__main__":
    main()
