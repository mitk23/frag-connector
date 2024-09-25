from api.dependencies.usecase import get_connector_usecase
from ddd.usecases.connector import ConnectorUsecase
from ddd.usecases.schemas.connector import ConnectorCreateDto, ConnectorUpdateDto
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import UUID4
from schemas.management import (
    ConnectorCreateRequest,
    ConnectorResponse,
    ConnectorUpdateRequest,
)

router = APIRouter()


@router.get("", response_model=dict[str, ConnectorResponse])
async def list_registered_connectors(connector_usecase: ConnectorUsecase = Depends(get_connector_usecase)):
    connector_dto_list = await connector_usecase.list_connectors()
    return {_id: ConnectorResponse.from_dict(conn_dto.model_dump()) for _id, conn_dto in connector_dto_list.items()}


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_registered_connector(
    connector_id: UUID4, connector_usecase: ConnectorUsecase = Depends(get_connector_usecase)
):
    connector_dto = await connector_usecase.get_connector(connector_id)
    return ConnectorResponse.from_dict(connector_dto.model_dump())


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_connector(
    connector: ConnectorCreateRequest,
    request: Request,
    response: Response,
    connector_usecase: ConnectorUsecase = Depends(get_connector_usecase),
):
    connector_dto = ConnectorCreateDto.model_validate(connector.to_dict())
    created_connector = await connector_usecase.create_connector(connector_dto)
    response.headers["Location"] = f"{str(request.url)}/{created_connector.id}"


@router.put("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_connector(
    connector_id: UUID4,
    connector: ConnectorUpdateRequest,
    connector_usecase: ConnectorUsecase = Depends(get_connector_usecase),
):
    connector_id_str = str(connector_id)
    connector_dto = ConnectorUpdateDto.model_validate(connector.to_dict())

    await connector_usecase.update_connector(connector_id_str, connector_dto)


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_connector(
    connector_id: UUID4, connector_usecase: ConnectorUsecase = Depends(get_connector_usecase)
):
    connector_id_str = str(connector_id)
    await connector_usecase.delete_connector(connector_id_str)
