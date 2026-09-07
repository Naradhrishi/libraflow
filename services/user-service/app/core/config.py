from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url : str
    secret_key : str
    jwt_encode_algo : str
    access_token_expire_minutes : int 
    refresh_token_expire_minutes : int 

    model_config = SettingsConfigDict(case_sensitive=False, env_file=".env", extra="ignore")


settings = Settings();
