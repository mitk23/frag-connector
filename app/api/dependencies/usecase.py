from api.dependencies.infrastructure import (
    get_asset_repository,
    get_auth_repository,
    get_connector_repository,
    get_dataspace_asset_query_service,
)
from ddd.domains.asset import AssetRepositoryIF
from ddd.domains.authorization import AuthRepositoryIF
from ddd.domains.connector import ConnectorRepositoryIF
from ddd.domains.dataspace import DataspaceAssetQueryServiceIF
from ddd.usecases.asset import AssetUsecase
from ddd.usecases.authorization import AuthorizationUsecase
from ddd.usecases.connector import ConnectorUsecase
from ddd.usecases.dataspace import DataspaceUsecase
from fastapi import Depends


# Usecases
def get_asset_usecase(asset_repository: AssetRepositoryIF = Depends(get_asset_repository)) -> AssetUsecase:
    return AssetUsecase(asset_repository)


def get_connector_usecase(
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
) -> ConnectorUsecase:
    return ConnectorUsecase(connector_repository)


def get_authorization_usecase(
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
    connector_usecase: ConnectorUsecase = Depends(get_connector_usecase),
) -> AuthorizationUsecase:
    return AuthorizationUsecase(auth_repository, connector_usecase)


def get_dataspace_usecase(
    asset_query_service: DataspaceAssetQueryServiceIF = Depends(get_dataspace_asset_query_service),
):
    return DataspaceUsecase(asset_query_service)


# def get_llm_interface(settings: Settings = Depends(get_settings)):
#     service = settings.llm_service

#     if service == "openai":
#         return OpenAIInterface(
#             api_key=settings.llm_api_key,
#             api_base_url=settings.llm_api_base_url,
#         )
#     elif service == "ollama":
#         return OllamaInterface(
#             api_key=settings.llm_api_key,
#             api_base_url=settings.llm_api_base_url,
#         )
#     else:
#         raise ValueError(f"Unsupported vector db service: {service}")
