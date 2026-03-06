from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


from app.routers.admin import ward
from app.routers.admin import province


admin_api = FastAPI(dependencies=[])


@admin_api.exception_handler(RequestValidationError)
async def handler(request: Request, exc: RequestValidationError):
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

admin_api.include_router(province.router, prefix="/province")
admin_api.include_router(ward.router, prefix="/ward")
