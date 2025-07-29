import boto3
from botocore.exceptions import ClientError
import os
import logging
from fastapi import Request

from src.config.settings import settings


logger = logging.getLogger(__name__)


class S3Handler:
    """
    A utility class for interacting with AWS S3: checking, uploading, downloading, and listing files.
    Loads credentials and configuration from a .env file.
    """

    def __init__(self):
        """
        Initialize the S3Handler by loading AWS credentials and setting up an S3 client.
        Credentials and bucket details are loaded from the .env file.
        """
        self.bucket_name = settings.S3_BUCKET_NAME
        access_key = settings.AWS_ACCESS_KEY_ID
        secret_key = settings.AWS_SECRET_ACCESS_KEY
        region = settings.AWS_REGION

        missing = []
        if not access_key:
            missing.append("AWS_ACCESS_KEY_ID")
        if not secret_key:
            missing.append("AWS_SECRET_ACCESS_KEY")
        if not region:
            missing.append("AWS_REGION")
        if not self.bucket_name:
            missing.append("S3_BUCKET_NAME")

        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Check if a specific file or folder prefix exists in the S3 bucket.

        :param s3_key: The key (file path or folder prefix) in the S3 bucket
        :return: True if exists, False if not
        """
        try:
            # If checking for a folder prefix
            if s3_key.endswith('/'):
                response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=s3_key, MaxKeys=1)
                return 'Contents' in response
            else:
                # Checking for a specific file
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise


    def upload_file(self, local_path: str, s3_key: str) -> bool:
        """
        Upload a file from the local filesystem to the specified S3 key.

        :param local_path: Path to the file on the local system
        :param s3_key: Destination key (path/filename) in the S3 bucket
        :return: True if upload is successful, False otherwise
        """
        try:
            # local_path = file
            # s3_key = objname
            self.s3_client.upload_file(local_path, self.bucket_name, s3_key)
            return True
        except ClientError as e:
            print(f"Upload error: {e}")
            return False

    def download_file(self, s3_key: str, local_path: str) -> bool:
        """
        Download a file from S3 to the local filesystem.

        :param s3_key: Key (path/filename) in the S3 bucket
        :param local_path: Destination path on the local system
        :return: True if download is successful, False otherwise
        """
        try:
            self.s3_client.download_file(self.bucket_name, s3_key, local_path)
            return True
        except ClientError as e:
            print(f"Download error: {e}")
            return False

    def list_files_in_s3_folder(self, folder_name: str):
        """
        List all file keys in the specified S3 folder (prefix).

        :param folder_name: Folder path (prefix) in the S3 bucket
        :return: List of file keys or False in case of an error
        """
        try:
            file_list = []
            paginator = self.s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=folder_name):
                for obj in page.get('Contents', []):
                    key = obj['Key']  # Corrected: should be 'Key', not 'key'
                    if not key.endswith('/'):
                        file_list.append(key)
            return file_list
        except ClientError as e:
            print(f"List error: {e}")
            return False
        
    def s3_handling(self,input_info,request:Request) -> str:
        """
        Handles downloading files from an S3 folder to a local directory.

        Args:
            input_info (dict): Dictionary containing:
                - 'S3_folder' (str): Path to folder in S3.
                - 'Local_folder' (str, optional): Local folder to save files to.
                - 'mode' (str): 'bulk' or 'single' to indicate download mode.
                - 'file_name' (List[str], optional): Required for 'single' mode.

        Returns:
            str: Absolute path to the local directory where files are downloaded.

        Raises:
            ValueError: If required fields are missing.
            FileNotFoundError: If S3 folder or expected files don't exist.
        """
        s3_folder = input_info.get('S3_folder')
        local_folder = input_info.get('Local_folder')

        if not s3_folder: 
            raise ValueError(" 'S3_folder' must be provided in request body.")

        if not local_folder:
            local_folder = s3_folder
            logger.warning("Local folder not specified. Using S3 folder path as fallback for local path.")

        if not self.file_exists(s3_folder):
            raise FileNotFoundError(f"S3 folder '{s3_folder}' does not exist.")

        # Set and prepare local dir
        request.state.source_directory=local_folder
        local_dir = os.path.abspath(os.path.join(os.getcwd(), local_folder))
        os.makedirs(local_dir, exist_ok=True)

        s3_files = list()

        if input_info['mode'] == 'bulk':
            s3_files = self.list_files_in_s3_folder(s3_folder)
        elif input_info['mode'] == 'single':
            files = input_info.get('file_name',[])
            if not files:
                raise ValueError(f"File name is missing in request!!.")
            for file in files:
                s3_files.append(os.path.join(s3_folder,file))
        
        if not s3_files:
            raise FileNotFoundError(f"No files found in S3 folder '{s3_folder}'.")

        logger.info(f"Files to download: {s3_files}")
        for s3_key in s3_files:
            filename = os.path.basename(s3_key)
            local_path = os.path.join(local_dir, filename)
            logger.info(f"Downloading {s3_key} to {local_path}")
            self.download_file(s3_key, local_path)

        return local_dir
    


# s3 = S3Handler()
# s3.upload_file(r'C:\final_push_code\ai-services\sample_qa.json','dataingestion-test/1/1.json')
# if s3.file_exists('dataingestion-test/1/1.json'):
#     print("ex")