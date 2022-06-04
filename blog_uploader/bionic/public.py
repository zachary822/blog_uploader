import secrets

import requests

import blog_uploader.bionic


class Bionic(blog_uploader.bionic.BionicBase, requests.Session):
    @staticmethod
    def get_rand_hex(n: int) -> str:
        return secrets.token_bytes(n).hex()

    def __init__(self, api_key: str):
        super().__init__()

        self.api_key = api_key
        self.bionic_client_id = "-".join(map(self.get_rand_hex, [4, 2, 2, 2, 6]))

        self.headers.update(
            {
                "BionicClientId": self.bionic_client_id,
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:100.0) Gecko/20100101 Firefox/100.0",
            }
        )

        self.refresh_session()

    def refresh_session(self):
        resp = self.get(
            "https://api.bionic-reading.com/client/v1/bionic",
            headers={
                "Authorization": "Bearer",
                "clientId": self.bionic_client_id,
                "id": self.api_key,
            },
        )

        self.headers["Authorization"] = f"Bearer {resp.text.strip()}"

    def convert(self, value: str) -> requests.Response:
        return self.post(
            "https://api.bionic-reading.com/v1/convert",
            headers={"Origin": "https://api.bionic-reading.com"},
            data={
                "content": value,
                "request_type": "html",
                "response_type": "html",
                "saccade": "20",
                "fixation": "2",
            },
        )
