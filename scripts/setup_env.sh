# !bin/bash

read -p "Please enter the Python version you want to use (e.g., 3.9): " PYTHON_VERSION

conda create --name git-loader python=$PYTHON_VERSION -y

conda activate git-loader

pip install -r requirements.txt
pip install -r requirements_test.txt
pip install -r requirements_dev.txt

