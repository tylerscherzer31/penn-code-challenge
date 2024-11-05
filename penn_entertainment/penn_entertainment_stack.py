from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_s3_notifications as s3n,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_iam as iam,
    RemovalPolicy,
)
from constructs import Construct

class PennEntertainmentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create S3 bucket
        bucket = s3.Bucket(self,
            "PennEntertainmentBucket",
            # bucket name
            bucket_name="penn-entertainment-bucket",
            # enable versioning
            versioned=True,
            # retain the bucket on on stack deletion
            removal_policy=RemovalPolicy.RETAIN  
        )

        # create Lambda function
        lambda_function = _lambda.Function(self,
            "PennEntertainmentFunction",
            # set the runtime to python 3.12 per instructions
            runtime=_lambda.Runtime.PYTHON_3_12,
            # set the entry point for the lambda
            handler="lambda_function.handler",
            # specify the location of the lambda handler
            code=_lambda.Code.from_asset("lambda_code"),
            # add needed enviornment variables for db and bucket connection
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                # "RDS_ENDPOINT": rds_instance.db_instance_endpoint_address,
                # "RDS_PORT": rds_instance.db_instance_endpoint_port,
                # "DB_NAME": "metadataDB",
                # "DB_USER": "dbadmin",
                # "RDS_SECRET_NAME": rds_instance.secret.secret_name if rds_instance.secret else "",
            },
            # set the memory size to handle multiple simultaneous uploads
            memory_size=128
        )

        # give Lambda permissions to read from the s3 bucket
        bucket.grant_read(lambda_function)

        # give lambda permission to connect to rds
        # rds_instance.grant_connect(lambda_function)

        # give lambda role full access to RDS
        # lambda_function.role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRDSFullAccess")
        # )

        # grant Lambda role read only access to the automatically created secret
        # if rds_instance.secret: 
        #     rds_instance.secret.grant_read(lambda_function)

        # create S3 event notification for Lambda
        # this event notification is specefic to objects created within the images folder in s3
        bucket.add_event_notification(
            # trigger lambda when an object is created
            s3.EventType.OBJECT_CREATED,
            # define the lambda function that will be triggered as the one created above
            s3n.LambdaDestination(lambda_function),
            # only trigger when an object is created in the images folder
            s3.NotificationKeyFilter(prefix="images/")
        )
