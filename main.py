from api.http_client import GameApiClient
from bot.game_bot import GameBot
from core.config import config


def main():
    client = GameApiClient(config.APP_HOST)
    bot = GameBot(client)
    bot.run()


if __name__ == "__main__":
    main()
