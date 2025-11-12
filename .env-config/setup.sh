#!/bin/bash

# Install python and venv
# sudo apt install python3
# sudo apt install python3-pip
# sudo apt install python3-venv

#  Create .env file (with the format as .env.example) in Backend to fill in the API key 
cp ".env-config/.env.example" "backend/.env"

# Setup virtual environment (.venv)
python3 -m venv .venv

#  Activate the virtual environment (venv). 
source .venv/bin/activate

# Install defined package for virtual environment
pip install -r .env-config/requirements.txt

# Shut down the virtual environment
deactivate

# Add instruction to fill in the API key in backend folder
echo
echo
echo
echo "!!! Please fill in the Groq API key in backend/.env"
