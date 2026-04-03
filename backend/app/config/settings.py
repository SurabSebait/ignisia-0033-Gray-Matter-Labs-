from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "customer_support"
    gcs_bucket_name: str = "your-bucket-name"
    openai_api_key: str = ""
    ai_model: str = "gpt-4.1"
    ai_service_url: str = ""  # optional: external AI microservice endpoint

    class Config:
        env_file = ".env"

settings = Settings()