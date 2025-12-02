from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Website Q&A Chatbot"
    API_V1_PREFIX: str = "/api"

    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_EMBED_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4.1-mini"

    CRAWLER_USER_AGENT: str = "SimpleSiteBot/0.1"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
