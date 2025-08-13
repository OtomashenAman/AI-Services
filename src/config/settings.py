from pydantic_settings import BaseSettings
from urllib.parse import quote_plus
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Service"
    DEBUG: bool = True
    ENV: str = "development"  # change to 'production' for prod
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")

    db_user: str = ""
    db_password: str = ""
    db_name: str = ""
    db_host: str = ""
    db_port: str = "5432"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""

    AZURE_COMMUNICATION_SERVICE_CONNECTION_STRING: str = ""
    DEFAULT_FILE_STORAGE: str = "storages"
    AZURE_ACCOUNT_NAME: str = ""
    AZURE_ACCOUNT_KEY: str = ""
    AZURE_CONTAINER_NAME: str = ""
    AZURE_SSL: bool = True

    AUTH_URL: str = ""
    REDIS_HOST :str = ""
    REDIS_PORT :str = ""

    tavily_api_key: str = ""

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

    @property
    def LOG_LEVEL(self) -> str:
        if self.ENV.lower() == "production" :
            return "INFO"
        return "DEBUG"

    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        return f"postgresql+psycopg2://{user}:{password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "forbid"

settings  = Settings()