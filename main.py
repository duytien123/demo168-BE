from pydantic import ValidationError

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.utils.timeout_middleware import TimeoutMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

from app.config import Settings, get_settings
from app.routers import router
from app.routers.admin.sub_app import admin_api

from app.exceptions.exception_handlers import validation_exception_handler, http_exception_handler, \
    http_exception_internal_server_handler
from fastapi.exceptions import RequestValidationError, HTTPException

description = '''
'''

# tag sort
tags_metadata = []

settings: Settings = get_settings()
app = FastAPI(
    title='VN168',
    description=description,
    version='mock',
    openapi_tags=tags_metadata,
    swagger_ui_parameters={
        'operationsSorter': 'alpha',
        'docExpansion': 'none',
    },
    dependencies=[]
)

app.mount("/admin", admin_api)

origins = ['*', ]  # noqa

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(TimeoutMiddleware, timeout=settings.request_timeout)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, http_exception_internal_server_handler)

# app.include_router(health_check.router)


@app.exception_handler(HTTPException)
def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get(
    '/health_check/',
    tags=['health_check'],
    summary='health check'
)
def send_health_check():
    return {"status": "ok"}


# Include route root
app.include_router(router.router)
