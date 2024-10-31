from datetime import datetime, timedelta, timezone
from PIL import Image
import io
import pdb

# use pillow library to get the height and width of an image
def get_image_size(s3_file_contents, logger):
    try:
        logger.info(f"Getting image height and width...")
        # read the s3 file contents as an image using pillow
        image = Image.open(io.BytesIO(s3_file_contents))
        # get the width and height of the image
        width, height = image.size
        logger.info(f"Image height: {height} and width: {width}...")
        return width, height
    except Exception as e:
        # log an errors occur while attempting to get the image size
        logger.error(f"Error getting image size: {e}...")
        return None, None


# calculate current time in EST
def get_current_est_timestamp():
    # set UTC offset to -5 which represents the EST, get the current time in EST
    eastern_time = datetime.now(timezone(timedelta(hours=-5)))
    # format the time to desired format
    time_stamp = eastern_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
    return time_stamp


# extract image metadata from S3 response
def extract_metadata(s3_response, s3_file_contents, object_key, logger):
    logger.info(f"Extracting metadata from {object_key}...")
    
    # extract the image metadata
    image_id = object_key # set the image_id to the s3 object key per instructions
    file_name = object_key.split('/')[-1] # extract the file name from the object key (assuming the file is within the images folder)
    file_size = s3_response['ContentLength'] # get the file size from s3 response
    file_type = s3_response['ContentType'] # get the file type from s3 response
    time_stamp = get_current_est_timestamp() # get the current time 
    width, height = get_image_size(s3_file_contents, logger) # get the width and height of the image
    
    # check if any metadata values are none, if so log an error and skip the file
    if any(value is None for value in [image_id, file_name, file_size, file_type, time_stamp, width, height]):
        logger.error(f"Skipping {object_key} due to image metadata extraction failure...")
        return None
    
    logger.info(f"Extracting metadata from {object_key}...")

    # return the image metadata as dict
    return {
        'imageId': image_id,
        'fileName': file_name,
        'fileSize': file_size,
        'fileType': file_type,
        'width': width,
        'height': height,
        'timestamp': time_stamp
    }
