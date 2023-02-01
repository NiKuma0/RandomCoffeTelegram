from pydantic import BaseSettings


TESTING = True
BOT = None


class Config(BaseSettings):
    # DB settings
    POSTGRES_PASSWORD: str
    POSTGRES_USER: str
    POSTGRES_DB: str
    # Bot settings
    BOT_TOKEN: str
    ADMINS: str


def get_config(_env_file=None) -> Config:
    if TESTING:
        return Config(_env_file=_env_file or ".env")
    return Config()
