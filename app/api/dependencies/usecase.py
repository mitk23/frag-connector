from api.dependencies.auth import get_bearer_token
from api.dependencies.infrastructure import (
    get_asset_repository,
    get_auth_repository,
    get_connector_repository,
    get_dataspace_asset_catalog_query_service,
)
from ddd.domains.asset import AssetRepositoryIF
from ddd.domains.authorization import AuthRepositoryIF
from ddd.domains.connector import ConnectorRepositoryIF
from ddd.domains.dataspace import DataspaceAssetCatalogQueryServiceIF
from ddd.usecases.asset import AssetCatalogUsecase, AssetCommandUsecase, AssetQueryUsecase
from ddd.usecases.connector import ConnectorCommandUsecase, ConnectorQueryUsecase
from ddd.usecases.dataspace import DataspaceUsecase
from fastapi import Depends


# Usecases
def get_asset_query_usecase(asset_repository: AssetRepositoryIF = Depends(get_asset_repository)) -> AssetQueryUsecase:
    return AssetQueryUsecase(asset_repository)


def get_asset_command_usecase(
    asset_repository: AssetRepositoryIF = Depends(get_asset_repository),
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
) -> AssetCommandUsecase:
    return AssetCommandUsecase(asset_repository, connector_repository, auth_repository)


def get_asset_catalog_usecase(
    asset_repository: AssetRepositoryIF = Depends(get_asset_repository),
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
    access_token: str = Depends(get_bearer_token),
) -> AssetCatalogUsecase:
    return AssetCatalogUsecase(asset_repository, auth_repository, catalog_access_token=access_token)


def get_connector_query_usecase(
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
) -> ConnectorQueryUsecase:
    return ConnectorQueryUsecase(connector_repository)


def get_connector_command_usecase(
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
) -> ConnectorCommandUsecase:
    return ConnectorCommandUsecase(connector_repository, auth_repository)


# def get_authorization_usecase(
#     auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
#     connector_usecase: ConnectorUsecase = Depends(get_connector_usecase),
# ) -> AuthorizationUsecase:
#     return AuthorizationUsecase(auth_repository, connector_usecase)


def get_dataspace_usecase(
    asset_catalog_query_service: DataspaceAssetCatalogQueryServiceIF = Depends(
        get_dataspace_asset_catalog_query_service
    ),
):
    return DataspaceUsecase(asset_catalog_query_service)


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
