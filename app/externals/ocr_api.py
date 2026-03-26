from app.externals.api_client import APIClient

from app.config import get_settings


def call(
    method: str,
    # endpoint: str,
    params=None,
    data=None,
    json=None,
    headers={"Content-Type": "application/json"}
):
    try:
        settings = get_settings()
        ocr_api_client = APIClient(
            base_url=settings.qwen_api_base_url,
            timeout=settings.request_timeout
        )
        response = ocr_api_client.call(
            method=method,
            endpoint=settings.qwen_api_endpoint,
            params=params,
            data=data,
            json=json,
            headers=headers
        )
        return response
    except Exception as e:
        raise e
