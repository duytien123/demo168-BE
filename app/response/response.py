from typing import Optional, Union

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def handle_response(
    status_code: int, message: str = None, data: Optional[Union[dict, list, str]] = None
):
    if status_code in {status.HTTP_200_OK, status.HTTP_201_CREATED}:
        return JSONResponse(
            status_code=status_code,
            content={
                "data": jsonable_encoder(data) or data,
                "message": message or "Success",
            },
        )
    else:
        return handle_error(status_code, message, data)


def handle_error(
    status_code: int, message: str = None, data: Optional[Union[dict, list, str]] = None
):
    return JSONResponse(
        status_code=status_code,
        content={
            "message": message or "",
            "errors": jsonable_encoder(data) or data,
        },
    )


def handle_response_pagination(
    status_code: int,
    message: str = None,
    content: Optional[Union[dict, list, str]] = None,
):
    if status_code in {status.HTTP_200_OK, status.HTTP_201_CREATED}:
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(content),
        )
    else:
        return handle_error(status_code, message, content)
