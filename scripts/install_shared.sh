#!/bin/bash
# install_shared.sh

echo "Installing shared library in development mode..."

# Install in auth service
cd auth-service
pip install -e ../shared-lib

# Install in employee service
cd ../employee-service
pip install -e ../shared-lib

# Install in payroll service
cd ../payroll-service
pip install -e ../shared-lib

# Install in attendance service
cd ../attendance-service
pip install -e ../shared-lib

echo "Shared library installed in all services!"