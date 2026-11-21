
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    # AWS S3 Configuration
    aws_region: str = "ap-southeast-2"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_bucket: str = ""

    # Database
    database_url: str = ""

    # Groq LLM Configuration
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"

    # Local Embedding Configuration
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embed_dim: int = 384

    # Application Configuration
    max_upload_bytes: int = 10485760

    # Pinecone Configuration
    pinecone_api_key: str = ""
    pinecone_index_name: str = "atlas-enterprise-ai-index"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    pinecone_ready_timeout: int = 180

    # RAG Configuration
    min_relevance: float = 0.25

    # HITL and Memory
    hitl_enabled: bool = True
    memory_turns: int = 6


@lru_cache
def settings() -> Settings:
    return Settings()
