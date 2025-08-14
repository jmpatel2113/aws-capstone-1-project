# AWS Cloud Capstone Project: Customer Onboarding (KYC) Application

## Project Overview

This AWS Cloud Capstone Project implements a serverless customer onboarding solution. The system is designed to validate Know Your Customer (KYC) documents submitted by a user, such as a CSV file with user details, a selfie image, and a driver's license image. These files are uploaded to an S3 bucket and automatically processed using a fully serverless backend orchestrated with AWS Step Functions and powered by AWS Lambda.

## Problem-Solution

**Problem**: Financial institutions must perform KYC checks to verify the identity of customers to prevent fraud, money laundering, and non-compliance. Manual processing of documents is time-consuming and prone to human error.

**Solution**: This project automates the KYC document validation workflow using AWS services. When a customer uploads their documents to an S3 bucket, the application automatically verifies document contents (e.g., name and date of birth), compares the selfie against the ID image, and stores the validated data in a database. If all validations pass, a message is sent to a queue for downstream processing.

## Use Cases and Industry Applications

This solution can be applied across a variety of industries where KYC, identity verification, or document validation is needed:

* **Banking and Financial Services**: Automating customer onboarding and fraud prevention.
* **Insurance**: Verifying identities for claims or policy issuance.
* **Healthcare**: Verifying patient documents during registration.

## AWS Services Used&#x20;

1. **AWS Lambda** – Serverless compute; used for all backend logic such as file unzipping, data extraction, image comparison, and data validation.
2. **Amazon S3** – File storage; users upload a ZIP file containing their KYC documents through a frontend application(not designed).
3. **AWS IAM** – Access control; used to grant secure permissions between services especially lambda.
4. **Amazon CloudWatch** – Observability; used to monitor Lambda execution and application health with metrics and logs.
5. **Amazon DynamoDB** – NoSQL database; stores extracted customer details after processing and validating.
6. **Amazon Rekognition** – Image analysis; used to compare the selfie photo with the driver’s license photo.
7. **Amazon Textract** - Text extraction; used to extract related information from the ID.
8. **AWS SAM** - Serverless build & deploy; used for building & deploying serverless resources like lambda functions, S3 storage bucket & prefixes, API, DynamoDB tables and sns topic
9. **Amazon SNS** - Notifications; used to send email notifications to customers for failed/successful checks
10. **Amazon API Gateway** – API management; used  for testing/invoking Lambda functions via HTTP calls for 3rd party ID verification.

## Steps:

1. Created an encrypted S3 bucket (documentbucket) to securely store customer application zip files and its unzipped content. Applied bucket policies to enforce TLS-only connections and prevent public access.
2. Created the IAM role with least-privilege permissions to allow Lambda functions to read, write, and delete objects from the document bucket.
3. Created the IAM role for cloudwatch permissions(needed for lambda function logging), the lambda function for extracting the files from zip folder and putting it into another "unzipped" prefix.
4. Created the sam configuration file for automatic resource build and deployment as well as the lambda function that parses customer details from csv file and puts it in dynamodb table.
5. Created the IAM role for rekognition permissions and wrote the lambda function code for comparing selfie of customer and ID photo and update dynamodb table accordingly.
6. Created the IAM role for textract permissions and wrote the lambda function code for extracting details from ID and comparing it with customer input details + update dynammdb table & sns notification accordingly
7. Created the lambda function that mimics a third-party DL/ID validation service and it is invoked by an HTTP API that is created using Amazon API Gateway.