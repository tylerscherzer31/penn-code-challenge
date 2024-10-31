import boto3

from .logging_helpers import create_logger
from .s3_helpers import fetch_file_contents
from .db_helpers import write_to_rds
from .utils import extract_metadata


def handler(event):
    logger = create_logger()
    logger.info(f"Invoking image metadata extractor lambda...")

    s3_client = boto3.client('s3')

    # itterate through the records array from the triggering event
    for record in event['Records']:
        try:
            # extract the bucket name and object key from the record
            bucket_name = record['s3']['bucket']['name']
            object_key = record['s3']['object']['key']

            # use the bucket name and object key to fetch the file from s3 
            s3_response, s3_file_content = fetch_file_contents(s3_client, bucket_name, object_key, logger)

            # check to see if we got a response from s3
            # even if we got a response from s3 we want to ensure we also recieved the file contents (the image) 
            # if either is none, log an error and continue to the next record
            if s3_response is None or s3_file_content is None:
                logger.error(f"Skipping file {object_key}... Could not fetch file contents...")
                continue
            
            # extract the file metadata 
            image_metadata = extract_metadata(s3_response, s3_file_content, object_key, logger)

            # check if metadata extraction was successfull 
            # if unnsuccesful skip writing to rds, log an error and continue to the next record
            if image_metadata is None:
                logger.error(f"Skipping file {object_key}... Could not extract file metadata...")
                continue
            
            # write the image metadata to rds if extraction was successfull 
            write_to_rds(image_metadata, logger)
        
        except Exception as e:
            # handle any unexpected errors
            logger.error(f"Error processing file {object_key}: {e}...")

    return {
        'statusCode': 200,
        'body': 'Image metadata processing completed...'
    }
