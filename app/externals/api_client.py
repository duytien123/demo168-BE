import requests
from fastapi import status
from app.config import Settings
from app.log import logger

settings = Settings()


class APIClient:
    def __init__(self, base_url: str, timeout: int = 300, default_headers: dict = None):
        """
        API Client for making HTTP requests.

        Args:
            base_url (str): Base URL of the API (e.g., "http://localhost:8000").
            timeout (int): Timeout for requests in seconds.
            default_headers (dict): Default headers to include in all requests.
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = default_headers or {"Content-Type": "application/json"}

    def call(self, method: str, endpoint: str, params=None, data=None, json=None, headers=None):
        """
        Make an HTTP request.

        Args:
            method (str): HTTP method ('GET', 'POST', 'PUT', 'DELETE').
            endpoint (str): API endpoint (e.g., '/v1/data').
            params (dict): Query parameters for GET requests.
            data (dict): Form data for POST requests.
            json (dict): JSON payload for POST/PUT requests.
            headers (dict): Optional headers to merge with defaults.

        Returns:
            dict: A response object with status, data, and error_message.
        """
        url = f"{self.base_url}{endpoint}"
        merged_headers = {**self.default_headers, **(headers or {})}

        try:
            response = requests.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=merged_headers,
                timeout=self.timeout
            )

            # Log request info
            req = response.request
            print(f"URL: {req.url}")
            print(f"Method: {req.method}")
            # print(f"Body: {req.body}")

            # Log response info
            print(f"Response Status: {response.status_code}")
            print(f"Response Body: {response.text}")

            response.raise_for_status()

            return {
                "status": status.HTTP_200_OK,
                "data": response,
                "error_message": ""
            }

        except requests.HTTPError as http_err:
            res = http_err.response
            try:
                error_detail = res.json()
            except ValueError:
                error_detail = res.text

            if isinstance(error_detail, dict):
                error_message = error_detail.get("message") or error_detail.get("msg") or str(error_detail)
            else:
                error_message = str(error_detail)
            logger.error(f"HTTP Error {res.status_code}: {error_message}")

            return {
                "status": res.status_code,
                "data": None,
                "error_message": error_message
            }

        except requests.ConnectionError:
            error_detail = f"[API ERROR] Cannot connect to {url}"
            logger.error(error_detail)
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "data": None,
                "error_message": error_detail
            }

        except Exception as err:
            error_detail = f"[API ERROR] Unexpected error: {err}"
            logger.error(error_detail)
            return {
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "data": None,
                "error_message": error_detail
            }
