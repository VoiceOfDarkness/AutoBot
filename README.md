# GameBot

GameBot is an automated bot for interacting with a game API. It performs various actions such as claiming rewards,
refueling, obtaining shields, and more.

## Requirements

- Python 3.10+
- pip

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/VoiceOfDarkness/GameBot.git
    cd GameBot
    ```

2. Create a virtual environment and activate it:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

1. Create a configuration file `.env` in the directory with the following content:
    ```sh
    APP_HOST = "https://your-game-api-host.com"
    ```

2. Replace `"https://your-game-api-host.com"` with the actual API host URL.

## Usage

1. Run the bot:
    ```sh
    python main.py
    ```

2. The bot will start and display its status in the console using the `rich` library.

## Termux Installation

1. Install Python and git:
    ```sh
    pkg install python git # if not installed
    ```

2. Clone the repository:
    ```sh
    git clone https://github.com/VoiceOfDarkness/GameBot.git
    cd GameBot
    ```

3. Add the `query_id` in `user.txt`
    ```sh
    echo "query_id" > user.txt # Optional you can use nano "nano user.txt"
    ```

4. Add environmet variables in `.env` file:
    ```sh
    echo "APP_HOST = 'https://your-game-api-host.com'" > .env # Optional you can use nano "nano .env"
    ```

5. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

5. Follow the Configuration and Usage steps as mentioned above.

## Features

- **Claim Daily Rewards**: Automatically claims daily rewards.
- **Refuel**: Refuels the user's fuel.
- **Obtain Shields**: Obtains shields for the user.
- **Shield Immunity**: Obtains shield immunity.
- **Task Advertisements**: Starts and completes task advertisements.
- **Roulette**: Spins the roulette.

## Logging

The bot logs its activities and errors in the console. Recent activities are displayed in the status panel.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
