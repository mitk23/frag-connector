from api.dependencies.auth import get_bearer_token
from api.dependencies.infrastructure import (
    get_asset_repository,
    get_auth_repository,
    get_connector_repository,
    get_dataspace_asset_catalog_query_service,
    get_dataspace_knowledge_query_service,
    get_dataspace_qa_service,
    get_knowledge_query_service,
    get_qa_service,
)
from ddd.domains.asset import AssetRepositoryIF
from ddd.domains.authorization import AuthRepositoryIF
from ddd.domains.connector import ConnectorRepositoryIF
from ddd.domains.dataspace import (
    DataspaceAssetCatalogQueryServiceIF,
    DataspaceKnowledgeQueryServiceIF,
    DataspaceQAServiceIF,
)
from ddd.domains.knowledge import KnowledgeQueryServiceIF
from ddd.domains.qa import QAServiceIF
from ddd.usecases.asset import AssetCatalogUsecase, AssetCommandUsecase, AssetQueryUsecase
from ddd.usecases.connector import ConnectorCommandUsecase, ConnectorQueryUsecase
from ddd.usecases.dataspace import DataspaceFRAGUsecase, DataspaceUsecase
from ddd.usecases.knowledge import KnowledgeQuerySecureUsecase, KnowledgeQueryUsecase
from ddd.usecases.qa import SimpleQAUsecase
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


def get_knowledge_query_usecase(
    knowledge_query_service: KnowledgeQueryServiceIF = Depends(get_knowledge_query_service),
) -> KnowledgeQueryUsecase:
    return KnowledgeQueryUsecase(knowledge_query_service)


def get_knowledge_query_secure_usecase(
    knowledge_query_service: KnowledgeQueryServiceIF = Depends(get_knowledge_query_service),
    asset_repository: AssetRepositoryIF = Depends(get_asset_repository),
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
    access_token: str = Depends(get_bearer_token),
) -> KnowledgeQuerySecureUsecase:
    return KnowledgeQuerySecureUsecase(
        knowledge_query_service, asset_repository, auth_repository, knowledge_access_token=access_token
    )


def get_simple_qa_usecase(qa_service: QAServiceIF = Depends(get_qa_service)) -> SimpleQAUsecase:
    return SimpleQAUsecase(qa_service=qa_service)


def get_dataspace_usecase(
    asset_catalog_query_service: DataspaceAssetCatalogQueryServiceIF = Depends(
        get_dataspace_asset_catalog_query_service
    ),
    knowledge_query_service: DataspaceKnowledgeQueryServiceIF = Depends(get_dataspace_knowledge_query_service),
    qa_service: DataspaceQAServiceIF = Depends(get_dataspace_qa_service),
) -> DataspaceUsecase:
    return DataspaceUsecase(asset_catalog_query_service, knowledge_query_service, qa_service)


def get_dataspace_frag_usecase(
    knowledge_query_service: DataspaceKnowledgeQueryServiceIF = Depends(get_dataspace_knowledge_query_service),
    qa_service: DataspaceQAServiceIF = Depends(get_dataspace_qa_service),
) -> DataspaceUsecase:
    return DataspaceFRAGUsecase(knowledge_query_service, qa_service)
