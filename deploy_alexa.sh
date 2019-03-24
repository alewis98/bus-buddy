#!/bin/bash

cp handlers.py alexa-serverless/handler.py
echo "Updated lambda function"
cd alexa-serverless
serverless deploy