from api.dependencies.auth import verify_api_key, verify_bearer_token
from fastapi import APIRouter, Depends

from . import assets, connectors, dataspace, inter_connector

api_router = APIRouter()

api_router.include_router(
    assets.router, prefix="/management/assets", tags=["Asset Management"], dependencies=[Depends(verify_api_key)]
)

api_router.include_router(
    connectors.router,
    prefix="/management/connectors",
    tags=["Counter Connector Management"],
    dependencies=[Depends(verify_api_key)],
)

api_router.include_router(
    dataspace.router, prefix="/dataspace", tags=["Dataspace"], dependencies=[Depends(verify_api_key)]
)

api_router.include_router(
    inter_connector.router,
    prefix="/inter-connector",
    tags=["Inter-Connector Protocol"],
    dependencies=[Depends(verify_bearer_token)],
    include_in_schema=False,
)
