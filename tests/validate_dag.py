#!/usr/bin/env python3
"""
DAG Validation Script
Validates Airflow DAG files for syntax and import errors
"""

import sys
import os
from unittest.mock import patch


def validate_dag():
    """Validate the main DAG file"""
    try:
        # Add DAG path to sys.path
        dag_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'mwaa_dags', 'dags')
        sys.path.insert(0, dag_path)

        # Mock Airflow Variable to avoid dependency
        with patch('airflow.models.Variable.get', return_value='test-value'):
            from scripts.mwaa_blogpost_data_pipeline import dag

            print('✅ DAG import successful')
            print(f'✅ DAG ID: {dag.dag_id}')
            print(f'✅ Task count: {len(dag.tasks)}')

            # Validate DAG structure
            assert dag.dag_id == 'mwaa_blogpost_data_pipeline'
            assert len(dag.tasks) > 0

            return True

    except Exception as e:
        print(f'❌ DAG validation failed: {e}')
        return False


if __name__ == '__main__':
    success = validate_dag()
    sys.exit(0 if success else 1)
