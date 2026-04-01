from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    auth_service_url: str = "http://auth-service:8000"
    backend_url: str = "http://backend:8000"
    # Must match auth-service SECRET_KEY — used only for cookie name consistency,
    # actual validation is delegated to auth-service /auth/verify.
    secret_key: str = "change-me-in-production-use-a-long-random-string"

    model_config = {"env_file": ".env"}


settings = Settings()
