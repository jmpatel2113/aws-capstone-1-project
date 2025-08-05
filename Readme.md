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

1. **Amazon S3** – File storage; users upload a ZIP file containing their KYC documents through a frontend application(not designed).
2. **AWS IAM** – Access control; used to grant secure permissions between services especially lambda.
3. **Amazon DynamoDB** – NoSQL database; stores extracted customer details after processing and validating.
4. **Amazon SNS** - Notifications; used to send email notifications to customers for failed/successful checks