# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Service"
    DEBUG: bool = True
    ENV: str = "development"
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = ""
    LOG_LEVEL : str = "DEBUG"
    AWS_ACCESS_KEY_ID : str =""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION : str = ""
    S3_BUCKET_NAME : str =""

    # Add all the missing ones
    qdrant_host: str = "http://localhost"
    qdrant_port: str = "6333"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    db_host: str = ""
    db_port: str = "5432"
    admin_username: str = ""
    admin_password: str = ""

     # ✅ Azure Blob Storage
    AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING: str = ""
    DEFAULT_FILE_STORAGE: str = "storages"
    AZURE_ACCOUNT_NAME: str = ""
    AZURE_ACCOUNT_KEY: str = ""
    AZURE_CONTAINER_NAME: str = ""
    AZURE_SSL: bool = True
    
    @property
    def AZURE_BLOB_CONNECTION_STRING(self) -> str:
        return (
            f"DefaultEndpointsProtocol={'https' if self.AZURE_SSL else 'http'};"
            f"AccountName={self.AZURE_ACCOUNT_NAME};"
            f"AccountKey={self.AZURE_ACCOUNT_KEY};"
            f"EndpointSuffix=core.windows.net"
        )
        
    @property
    def AZURE_CUSTOM_DOMAIN(self) -> str:
        return f"{self.AZURE_ACCOUNT_NAME}.blob.core.windows.net"
    
    class Config:
        env_file = ".env"

settings = Settings()
