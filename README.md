README

Overview:

This project creates a serverless application for extracting image metadata from images uploaded to an S3 bucket. The creation of an object within the "images" directory in the S3 bucket triggers a Lambda function that extracts the metadata. If the metadata is successfully extracted, the Lambda function establishes a connection to an RDS MySQL instance and writes the metadata to a table named image_metadata.

The application leverages the AWS CDK for creating, updating, and deleting the resources associated with this application. Key components include AWS Lambda for serverless execution, Amazon S3 for object storage, and Amazon RDS for relational database management. The architecture ensures efficient data flow from image upload to metadata storage while incorporating error handling and logging to address potential issues during processing. Security measures, such as IAM roles and policies, ensure that only authorized access is granted to AWS resources.


Scalability Considerations and Improvements:

Batch Processing: Process multiple images simultaneously to reduce Lambda invocations and improve efficiency.

Asynchronous Processing: Implementing a queuing system like SQS allows us to batch events before invoking the Lambda function, enhancing efficiency during high traffic periods. Additionally, leveraging the asyncio library for asynchronous metadata extraction would significantly improve processing speed and responsiveness.

Retry Logic: Identify and implement error handling that should trigger retry logic.

Monitoring: Utilize AWS CloudWatch to monitor performance metrics and set alerts for issues like high error rates.

Type Hinting: We could add type hinting to our code to improve readability and help catch errors earlier by clearly defining the expected types for function arguments and return values.

Setup:

1. Ensure you have the following installed:

   - Node.js (for AWS CDK)
   - AWS CDK (run npm install -g aws-cdk)
   - Python 3.12
   - AWS CLI (for configuring AWS credentials)

2. Clone the repository:
   
   - git clone https://github.com/tylerscherzer31/penn-code-challenge.git 

3. Setup virtual environment (Optional):

   - python -m venv .venv
   - .venv\Scripts\activate

4. Install dependencies:
  
   - pip install -r requirements.txt

5. Create the lambda layer zip
   
   - mkdir python
   - cd python
   - pip install -r ../requirements.txt --target .
   - zip -r lambda_layer.zip python
      - if the above command does not work, open powershell, navigate to project directory, cd into the python directory, run below command 
         - Compress-Archive -Path * -DestinationPath ..\lambda_layer.zip

6. Configure AWS credentials:

   - aws configure

7. Synthesize the cloudFormation template (optional but recommended)

   - cdk synth

8. Deploy the stack:

   - cdk deploy

9. Testing:

   - pytest tests/unit/test_lambda_function.py

10. Run in region:

   - once deployed, you can run the process E2E by uploading an image to the images directory in the S3 bucket
   - the images directory will not be created automatically, please create the directory via AWS console

Useful Links:

- https://docs.aws.amazon.com/s3/
- https://docs.aws.amazon.com/lambda/
- https://docs.aws.amazon.com/rds/
- https://pillow.readthedocs.io/en/stable/index.html
   