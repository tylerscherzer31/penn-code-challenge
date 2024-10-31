from botocore.exceptions import ClientError

# fetch file contents from S3
def fetch_file_contents(s3_client, bucket_name, object_key, logger):
    try:
        logger.info(f"Fetching file contents from {bucket_name}/{object_key}...")
        # fetch the file from s3 and assign the request response to s3_response variable
        s3_response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        # extract the file contents from the s3_response 
        s3_file_contents = s3_response['Body'].read()
        logger.info(f"File {object_key} read successfully from {bucket_name}... Size: {len(s3_file_contents)} bytes...")
        return s3_response, s3_file_contents
    except ClientError as e:
        # check to see if the error was due to lack of permissions
        if e.response['Error']['Code'] == 'AccessDenied':
            logger.error(f"Access denied for {object_key} in {bucket_name}...")
            return None, None
        else:
            logger.error(f"Error fetching file {object_key} from {bucket_name}: {e}...")
            return None, None