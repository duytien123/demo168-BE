from app.externals.api_client import APIClient

from app.config import Settings


settings = Settings()


def call(
    method: str,
    # endpoint: str,
    params=None,
    data=None,
    json=None,
    headers={"Content-Type": "application/json"}
):
    try:
        ocr_api_client = APIClient(
            base_url="https://b811-2001-ee0-4dbe-dae0-2049-4dff-fe02-1838.ngrok-free.app/api/",
            # base_url=f"{settings.sokucom_api_host}:{settings.sokucom_api_port}",
            timeout=settings.request_timeout
        )
        response = ocr_api_client.call(
            method=method,
            endpoint="/generate",
            params=params,
            data=data,
            json=json,
            headers=headers
        )
        return response
    except Exception as e:
        raise e
