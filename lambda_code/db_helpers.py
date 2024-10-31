import json
import pymysql
import boto3
import os


# get RDS credentials from secrets manager
def get_rds_credentials(secret_name, logger):
    try:
        # create secret client using boto3
        secrets_client = boto3.client('secretsmanager')
        logger.info(f"Getting RDS credentials from {secret_name}...")
        # make request to secrets manager using the secret name
        response = secrets_client.get_secret_value(SecretId=secret_name)
        # extract the and parse the secret string containing rds credentials
        credentials = json.loads(response['SecretString'])
        logger.info(f"Done getting RDS credentials from {secret_name}...")
        return credentials['username'], credentials['password'], credentials['host'], credentials['dbname']
    except secrets_client.exceptions.AccessDeniedException:
        # log an error if access to the secret was denied
        logger.error(f"Access denied for secret {secret_name}...")
        return None, None, None, None
    except secrets_client.exceptions.ResourceNotFoundException:
        # log an error if the secret was not found
        logger.error(f"Secret {secret_name} not found...")
        return None, None, None, None
    except Exception as e:
        # log an any other error
        logger.error(f"Error getting RDS credentials from {secret_name}: {e}...")
        return None, None, None, None
    

# write the image metadata to rds 
# potential improvement for scaling: when traffic is high we could consider batching the inserts instead of handling them one at a time
def write_to_rds(image_metadata, logger):
    # initialize connection to none
    connection = None 
    try:
        logger.info(f"Writing metadata to RDS...")
        
        # get the rds credentials from secrets manager
        db_user, db_password, db_host, db_name = get_rds_credentials(os.getenv('RDS_SECRET_NAME'), logger)

        # check if any of the credentials are none
        # if so the connection will not be possible, log error and exit 
        if any(value is None for value in [db_user, db_password, db_host, db_name]):
            logger.error(f"All or some of RDS credentials were not received from secrets manager...")
            return

        # create connection to rds mysql instance using credentials from secrets manager
        connection = pymysql.connect(
            host=db_host, 
            user=db_user, 
            password=db_password, 
            database=db_name
        )

        # write the image metadata to the image_metadata table 
        # use place holders for the data types (%s), the mysql driver should infer the data types
        # check to ensure the partition key (imageId) does not already exist in the table, if so overwrite the contents with the newly extracted contents
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO image_metadata (image_id, file_name, file_size, file_type, width, height, timestamp) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            file_name = VALUES(file_name),
            file_size = VALUES(file_size),
            file_type = VALUES(file_type),
            width = VALUES(width),
            height = VALUES(height),
            timestamp = VALUES(timestamp)
            """
            cursor.execute(sql, 
                image_metadata['imageId'],
                image_metadata['fileName'],
                image_metadata['fileSize'],
                image_metadata['fileType'],
                image_metadata['width'],
                image_metadata['height'],
                image_metadata['timestamp']
            )
            
            connection.commit() 
            logger.info(f"Metadata written to RDS successfully...")

    # catch any mysql errors and log them 
    except pymysql.MySQLError as e:
        logger.error(f"Error writing metadata to RDS: {e}")  
    # catch any general errors and log them 
    except Exception as e:
        logger.error(f"General error writing metadata to RDS: {e}")  
    # check if the connection was created
    # close the connection if it was created
    finally:
        if connection:  
            connection.close()
