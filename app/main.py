from api.api import api_router
from core.exceptions import ConnectorException, InternalException
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

app = FastAPI()

app.include_router(api_router, prefix="/api")


@app.exception_handler(ConnectorException)
async def connector_exception_handler(request: Request, exc: ConnectorException):
    return JSONResponse(
        status_code=exc.status_code(),
        content=exc.message(),
    )


@app.exception_handler(InternalException)
async def internal_exception_handler(request: Request, exc: InternalException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=exc.message(),
    )
