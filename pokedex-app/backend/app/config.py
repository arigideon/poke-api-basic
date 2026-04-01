from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pokeapi_base_url: str = "https://pokeapi.co/api/v2"
    cache_ttl_seconds: int = 3600

    model_config = {"env_file": ".env"}


settings = Settings()
