from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError
import os
import logging
from fastapi import Request
from src.config.settings import settings 

logger = logging.getLogger(__name__)


class AzureBlobHandler:
    """
    Utility class for interacting with Azure Blob Storage: checking, uploading, downloading, and listing blobs.
    """

    def __init__(self):
        connection_string = settings.AZURE_BLOB_CONNECTION_STRING  
        self.container_name = settings.AZURE_CONTAINER_NAME

        if not connection_string or not self.container_name:
            raise EnvironmentError("Missing Azure Blob Storage configuration.")

        self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        self.container_client = self.blob_service_client.get_container_client(self.container_name)

    def file_exists(self, blob_path: str) -> bool:
        """
        Check if a blob or blob prefix exists in the Azure container.
        """
        try:
            if blob_path.endswith('/'):
                blobs = self.container_client.list_blobs(name_starts_with=blob_path)
                return any(True for _ in blobs)
            else:
                self.container_client.get_blob_client(blob_path).get_blob_properties()
                return True
        except ResourceNotFoundError:
            return False

    def upload_file(self, local_path: str, blob_path: str) -> bool:
        """
        Upload a local file to Azure Blob Storage.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
            return True
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False

    def download_file(self, blob_path: str, local_path: str) -> bool:
        """
        Download a blob to the local filesystem.
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_path)
            with open(local_path, "wb") as f:
                download_stream = blob_client.download_blob()
                f.write(download_stream.readall())
            return True
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False

    def list_files_in_blob_folder(self, folder_prefix: str):
        """
        List all blob paths in a given folder prefix.
        """
        try:
            blob_list = [
                blob.name for blob in self.container_client.list_blobs(name_starts_with=folder_prefix)
                if not blob.name.endswith('/')
            ]
            return blob_list
        except Exception as e:
            logger.error(f"List error: {e}")
            return False

    def blob_handling(self, input_info, request: Request) -> str:
        """
        Handle downloading files from a blob folder to a local directory.
        """
        blob_folder = input_info.get('S3_folder')  # use same key for compatibility
        local_folder = input_info.get('Local_folder')

        if not blob_folder:
            raise ValueError("'S3_folder' must be provided in request body.")

        if not local_folder:
            local_folder = blob_folder
            logger.warning("Local folder not specified. Using blob folder path as fallback for local path.")

        if not self.file_exists(blob_folder):
            raise FileNotFoundError(f"Blob folder '{blob_folder}' does not exist.")

        # Prepare local directory
        request.state.source_directory = local_folder
        local_dir = os.path.abspath(os.path.join(os.getcwd(), local_folder))
        os.makedirs(local_dir, exist_ok=True)

        blob_files = []
        if input_info['mode'] == 'bulk':
            blob_files = self.list_files_in_blob_folder(blob_folder)
        elif input_info['mode'] == 'single':
            files = input_info.get('file_name', [])
            if not files:
                raise ValueError("File name is missing in request.")
            for file in files:
                blob_files.append(os.path.join(blob_folder, file).replace("\\", "/"))

        if not blob_files:
            raise FileNotFoundError(f"No files found in blob folder '{blob_folder}'.")

        logger.info(f"Files to download: {blob_files}")
        for blob_path in blob_files:
            filename = os.path.basename(blob_path)
            local_path = os.path.join(local_dir, filename)
            logger.info(f"Downloading {blob_path} to {local_path}")
            self.download_file(blob_path, local_path)

        return local_dir


# Blob = AzureBlobHandler()
# Blob.upload_file(r'C:\zorbit\AI-Services\1.json','dataingestion-test/1/1.json')
# if Blob.file_exists('dataingestion-test/1/1.json'):
#     print("ex")