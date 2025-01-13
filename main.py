from bot.game_bot import GameBot
from api.http_client import GameApiClient
from core.config import config


def main():
    client = GameApiClient(config.APP_HOST)
    bot = GameBot(client)
    bot.run()
    # print(client.get_user())


if __name__ == "__main__":
    main()
