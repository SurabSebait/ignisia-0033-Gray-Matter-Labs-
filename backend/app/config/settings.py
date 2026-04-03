from pydantic import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "customer_support"
    gcs_bucket_name: str = "your-bucket-name"

    class Config:
        env_file = ".env"

settings = Settings()