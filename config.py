"""Configuration settings for the Halifax Bar sentiment analysis project."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str = "Halifax Bar Sentiment Bot"

    postgres_dbname: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432


settings = Settings() 