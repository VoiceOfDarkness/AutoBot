import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_HOST: str = os.getenv("APP_HOST")


config = Config()
