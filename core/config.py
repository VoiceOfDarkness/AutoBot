import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    APP_HOST: str = os.getenv("APP_HOST")


config = Config()
