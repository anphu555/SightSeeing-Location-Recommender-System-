#!/bin/bash

# Activate the virtual environment (venv). 
source .venv/bin/activate

# Change to the Backend directory to use uvicorn
cd Backend

# Start the server
uvicorn main:app --reload