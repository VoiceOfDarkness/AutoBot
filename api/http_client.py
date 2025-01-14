from typing import Dict

from httpx import Client

from core.logger import log_api_response, logger
from core.agents import generate_random_user_agent
from utils import get_user_data


class GameApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = Client(follow_redirects=True, timeout=10)
        self.auth_token = None
        self._initialize_cookies()
        self.set_token(get_user_data())

    @staticmethod
    def get_headers(auth_token=None):
        headers = {
            "sec-ch-ua": '"Android WebView";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
            "user-agent": generate_random_user_agent(),
            "accept": "application/json, text/plain, */*",
            "content-type": "application/x-www-form-urlencoded",
            "x-requested-with": "org.telegram.messenger",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en,en-US;q=0.9,ru-RU;q=0.8,ru;q=0.7",
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _request(self, method: str, endpoint: str, data: Dict = None):
        try:
            response = self.client.request(
                method=method,
                url=f"{self.base_url}{endpoint}",
                headers=self.get_headers(self.auth_token),
                data=data,
            )
            response.raise_for_status()

            if endpoint != "/telegram":
                log_api_response(logger, endpoint, response.json())

            return response.json() if endpoint != "/telegram" else response
        except Exception as e:
            log_api_response(logger, endpoint, str(e), status="error")
            logger.error(f"API request failed: {endpoint} - {str(e)}")
            raise

    def _initialize_cookies(self):
        response = self.client.get(
            f"{self.base_url}/telegram",
            headers=self.get_headers(),
        )
        if response.status_code != 200:
            raise Exception("Failed to initialize cookies")

    def set_token(self, data):
        response = self._request("POST", "/api/auth/telegram", data)
        self.auth_token = response["token"]

    def get_user(self):
        return self._request("GET", "/api/user/get")

    def get_shield(self):
        return self._request("POST", "/api/boost/buy", {"id": 2, "method": "coin"})

    def get_shield_immunity(self):
        return self._request("POST", "/api/boost/buy", {"id": 3, "method": "coin"})

    def get_fuel(self):
        return self._request("POST", "/api/boost/buy", {"id": 1, "method": "coin"})

    def get_roulette(self):
        return self._request("POST", "/api/roulette/buy", {"method": "free"})

    def claim(self):
        return self._request("POST", "/api/game/claim")

    def get_daily(self):
        return self._request("POST", "/api/user/daily_claim", {"method": "ordinary"})

    def get_onclick_task(self):
        return self._request("POST", "/api/tasks/onclick")

    def get_tasks(self):
        return self._request("POST", "/api/tasks/get", {"category": "sponsors"})
