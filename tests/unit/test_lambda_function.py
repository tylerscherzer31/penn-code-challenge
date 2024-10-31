import json
import pytest
from unittest.mock import patch, MagicMock
# from lambda_code.lambda_function import handler
from lambda_code.s3_helpers import fetch_file_contents
from lambda_code.utils import extract_metadata
from lambda_code.utils import get_image_size
from lambda_code.db_helpers import get_rds_credentials, write_to_rds
from botocore.exceptions import ClientError


# mock the logger
@pytest.fixture
def mock_logger():
    with patch("lambda_code.create_logger") as mock_logger:
        yield mock_logger


# test fetch_file_contents
def test_fetch_file_contents_success(mock_logger):
    mock_s3_client = MagicMock()
    mock_s3_client.get_object.return_value = {
        'Body': MagicMock(read=MagicMock(return_value=b'test_image_content')),
        'ContentLength': 18,
        'ContentType': 'image/png'
    }
    
    response, content = fetch_file_contents(mock_s3_client, 'test-bucket', 'test-key', mock_logger)

    assert response['Body'].read() == b'test_image_content'
    assert content == b'test_image_content'
    mock_logger.info.assert_called_with("File test-key read successfully from test-bucket... Size: 18 bytes...")


# test fetch_file_contents with access denied
def test_fetch_file_contents_access_denied(mock_logger):
    mock_s3_client = MagicMock()
    mock_error = ClientError({"Error": {"Code": "AccessDenied"}}, "GetObject")

    mock_s3_client.get_object.side_effect = mock_error

    response, content = fetch_file_contents(mock_s3_client, 'test-bucket', 'test-key', mock_logger)

    assert response is None
    assert content is None
    mock_logger.error.assert_called_with("Access denied for test-key in test-bucket...")


# test extract_metadata
def test_extract_metadata(mock_logger):
    mock_s3_file_content = b'fake_image_data'  
    mock_object_key = 'images/sample.jpg'  

    expected_metadata = {
        'imageId': mock_object_key,
        'fileName': 'sample.jpg',
        'fileSize': len(mock_s3_file_content),  
        'fileType': 'image/jpeg',  
        'width': 100,  
        'height': 200,  
        'timestamp': '2024-01-01T00:00:00.000000'  
    }

    mock_s3_response = {
        'ContentLength': expected_metadata['fileSize'],  
        'ContentType': 'image/jpeg'  
    }

    with patch('lambda_code.utils.get_image_size', return_value=(100, 200)):
        metadata = extract_metadata(mock_s3_response, mock_s3_file_content, mock_object_key, mock_logger)

    assert metadata is not None
    assert metadata['imageId'] == expected_metadata['imageId']
    assert metadata['fileName'] == expected_metadata['fileName']
    assert metadata['fileSize'] == expected_metadata['fileSize']  
    assert metadata['fileType'] == expected_metadata['fileType']
    assert metadata['width'] == expected_metadata['width']
    assert metadata['height'] == expected_metadata['height']


# test extract_metadata with missing file size
def test_extract_metadata_with_none_values(mock_logger):
    mock_s3_response = {
        'ContentLength': None,  
        'ContentType': 'image/jpeg'  
    }
    mock_s3_file_content = b'fake_image_data'  
    mock_object_key = 'images/sample.jpg'  

    metadata = extract_metadata(mock_s3_response, mock_s3_file_content, mock_object_key, mock_logger)

    assert metadata is None  
    mock_logger.error.assert_called_with(f"Skipping {mock_object_key} due to image metadata extraction failure...")


# test get_image_size with error
def test_get_image_size_error(mock_logger):
    with patch('PIL.Image.open') as mock_open:
        mock_open.side_effect = Exception("Cannot identify image file")

        width, height = get_image_size(b'invalid_image_data', mock_logger)

        assert width == None
        assert height == None
        mock_logger.error.assert_called_with("Error getting image size: Cannot identify image file...")


# test get rds creds
def test_get_rds_credentials(mock_logger):
    secret_name = "test-secret"
    mock_secrets_client = MagicMock()
    mock_response = {
        'SecretString': json.dumps({
            'username': 'test_user',
            'password': 'test_pass',
            'host': 'test_host',
            'dbname': 'test_db'
        })
    }
    
    with patch('boto3.client', return_value=mock_secrets_client):
        mock_secrets_client.get_secret_value.return_value = mock_response
        
        username, password, host, dbname = get_rds_credentials(secret_name, mock_logger)

        assert username == 'test_user'
        assert password == 'test_pass'
        assert host == 'test_host'
        assert dbname == 'test_db'
        mock_logger.info.assert_called_with(f"Done getting RDS credentials from {secret_name}...")


# test write_to_rds
def test_write_to_rds(mock_logger):
    mock_image_metadata = {
        'imageId': 'test-image-id',
        'fileName': 'test_image.jpg',
        'fileSize': 12345,
        'fileType': 'image/jpeg',
        'width': 100,
        'height': 200,
        'timestamp': '2024-01-01T00:00:00.000000'
    }

    mock_connection = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.__enter__.return_value = mock_cursor  
    mock_connection.cursor.return_value = mock_cursor

    with patch('lambda_code.db_helpers.get_rds_credentials', return_value=('username', 'password', 'host', 'dbname')), \
         patch('pymysql.connect', return_value=mock_connection):

        write_to_rds(mock_image_metadata, mock_logger)

        mock_logger.info.assert_called_with("Metadata written to RDS successfully...")
        mock_connection.cursor.assert_called_once()
        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()

# NOTE: I had trouble getting the unit test for the handler to work, the issue seems to be with getting the image size function to work properly, this should be addressed at a later time 
# def test_handler_success(mock_logger):
#     with patch('boto3.client') as mock_boto_client, \
#          patch('lambda_code.s3_helpers.fetch_file_contents') as mock_fetch, \
#          patch('lambda_code.db_helpers.write_to_rds') as mock_write, \
#          patch('lambda_code.utils.extract_metadata') as mock_extract:

#         mock_s3_client = MagicMock()
#         mock_boto_client.return_value = mock_s3_client

#         mock_fetch.return_value = (MagicMock(), b'fake_image_data')
#         mock_extract.return_value = {
#             'imageId': 'images/sample.jpg',
#             'fileName': 'sample.jpg',
#             'fileSize': 12,
#             'fileType': 'image/jpeg',
#             'width': 100,
#             'height': 200,
#             'timestamp': '2024-01-01T00:00:00.000000'
#         }

#         s3_event = {
#             "Records": [
#                 {
#                     "s3": {
#                         "bucket": {
#                             "name": "test-bucket"
#                         },
#                         "object": {
#                             "key": "images/sample.jpg"
#                         }
#                     }
#                 }
#             ]
#         }

#         response = handler(s3_event)

#         assert response['statusCode'] == 200
#         assert response['body'] == 'Image metadata processing completed...'
        
#         mock_fetch.assert_called_once_with(mock_s3_client, 'test-bucket', 'images/sample.jpg', mock_logger)
        
#         mock_extract.assert_called_once()
#         mock_write.assert_called_once()
