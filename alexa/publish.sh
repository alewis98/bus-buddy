#!/bin/bash

cd lambda
rm -r lambda_function.zip
zip -r -X lambda_function.zip lambda_function.py
aws lambda update-function-code --function-name 'busbuddy' --zip-file 'fileb://lambda_function.zip'