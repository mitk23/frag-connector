from api.dependencies.usecase import get_connector_command_usecase, get_connector_query_usecase
from ddd.usecases.connector import ConnectorCommandUsecase, ConnectorQueryUsecase
from ddd.usecases.schemas.connector import ConnectorCreateDto, ConnectorUpdateDto
from fastapi import APIRouter, Depends, Request, Response, status
from schemas.connectors import (
    ConnectorCreateRequest,
    ConnectorResponse,
    ConnectorUpdateRequest,
)

router = APIRouter()


@router.get("", response_model=dict[str, ConnectorResponse])
async def list_registered_connectors(connector_usecase: ConnectorQueryUsecase = Depends(get_connector_query_usecase)):
    connector_dto_list = await connector_usecase.list_connectors()
    return {
        _id: ConnectorResponse.model_validate(connector, from_attributes=True)
        for _id, connector in connector_dto_list.items()
    }


@router.get("/{connector_id}", response_model=ConnectorResponse)
async def get_registered_connector(
    connector_id: str, connector_usecase: ConnectorQueryUsecase = Depends(get_connector_query_usecase)
):
    connector_dto = await connector_usecase.get_connector(connector_id)
    return ConnectorResponse.model_validate(connector_dto, from_attributes=True)


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_connector(
    connector: ConnectorCreateRequest,
    request: Request,
    response: Response,
    connector_usecase: ConnectorCommandUsecase = Depends(get_connector_command_usecase),
):
    connector_dto = ConnectorCreateDto.model_validate(connector, from_attributes=True)
    created_connector = await connector_usecase.create_connector(connector_dto)
    response.headers["Location"] = f"{str(request.url)}/{created_connector.id}"


@router.put("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_connector(
    connector_id: str,
    connector: ConnectorUpdateRequest,
    connector_usecase: ConnectorCommandUsecase = Depends(get_connector_command_usecase),
):
    connector_dto = ConnectorUpdateDto.model_validate(connector, from_attributes=True)
    await connector_usecase.update_connector(connector_id, connector_dto)


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unregister_connector(
    connector_id: str, connector_usecase: ConnectorCommandUsecase = Depends(get_connector_command_usecase)
):
    await connector_usecase.delete_connector(connector_id)
