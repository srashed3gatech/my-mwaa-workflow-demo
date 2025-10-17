#!/usr/bin/env python3
"""
Dependency checker script for MWAA Workflow Demo
"""

import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_modules = ['boto3', 'aws_cdk', 'pytest', 'moto']
    missing = []
    
    print("🔍 Checking dependencies...")
    
    for module in required_modules:
        try:
            __import__(module)
            print(f'✅ {module}')
        except ImportError:
            missing.append(module)
            print(f'❌ {module} - MISSING')
    
    if missing:
        print(f'\n❌ Missing modules: {missing}')
        print('Run: make install')
        return False
    else:
        print('\n✅ All dependencies are installed')
        return True

if __name__ == '__main__':
    success = check_dependencies()
    sys.exit(0 if success else 1)
