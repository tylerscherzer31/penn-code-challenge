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

        # VPC for RDS with 2 availability zones 
        vpc = ec2.Vpc(self, "PennEntertainmentVpc", max_azs=2)

        # create MySQL RDS instance 
        rds_instance = rds.DatabaseInstance(self,
            "PennEntertainmentRdsInstance",

            # specify the MySQL engine and version 
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_39),
            # attach the RDS instance to the VPC 
            vpc=vpc,
            # instance type setup for small workloads
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            # genrate credentials for MySQL db with dbadmin as the username
            credentials=rds.Credentials.from_generated_secret("dbadmin"),
            # db name  
            database_name="metadataDB",
            # retain RDS instance and data on stack deletion 
            removal_policy=RemovalPolicy.RETAIN,  
            # enable deletion protection
            deletion_protection=True,
        )

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

        # define Lambda layer to house dependencies
        lambda_layer = _lambda.LayerVersion(self,
            "PennEntertainmentLayer",
            # path to the zip conaining dependencies
            code=_lambda.Code.from_asset("lambda_layer.zip"), 
            # specify compatible runtime to match lambda runtime 
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],  
            description="Layer containing dependencies"
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
                "RDS_ENDPOINT": rds_instance.db_instance_endpoint_address,
                "RDS_PORT": rds_instance.db_instance_endpoint_port,
                "DB_NAME": "metadataDB",
                "DB_USER": "dbadmin",
            },
            # attach lambda layer with dependencies
            layers=[lambda_layer]  
        )

        # give Lambda permissions to read from the s3 bucket
        bucket.grant_read(lambda_function)

        # give lambda permission to connect to rds
        rds_instance.grant_connect(lambda_function)

        # give lambda role full access to RDS
        lambda_function.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRDSFullAccess")
        )
        # give lambda role read only access to secret 
        lambda_function.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadOnly")
        )

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
