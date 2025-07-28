#!/bin/bash


echo "Starting The Server..."


exec uvicorn server:app --host 0.0.0.0 --port 8000 --workers 1 