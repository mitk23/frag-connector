from api.dependencies.settings import get_settings
from core.settings import Settings
from ddd.domains.asset import AssetRepositoryIF
from ddd.domains.authorization import AuthConfig, AuthRepositoryIF
from ddd.domains.connector import ConnectorRepositoryIF
from ddd.domains.dataspace import (
    DataspaceAssetCatalogQueryServiceIF,
    DataspaceKnowledgeQueryServiceIF,
    DataspaceQAServiceIF,
)
from ddd.domains.knowledge import KnowledgeQueryServiceIF
from ddd.domains.qa import QAServiceIF
from ddd.infrastructure.dataspace.asset_catalog_query_service import DataspaceAssetCatalogQueryServiceImpl
from ddd.infrastructure.dataspace.knowledge_query_service import DataspaceKnowledgeQueryServiceImpl
from ddd.infrastructure.dataspace.qa_service import DataspaceQAServiceImpl
from ddd.infrastructure.json.connector_repository import JSONConnectorRepository
from ddd.infrastructure.keycloak.asset_repository import JSONandKeycloakAssetRepository
from ddd.infrastructure.keycloak.authorization_repository import KeycloakAuthRepository
from ddd.infrastructure.ollama.qa_service import OllamaQAService
from ddd.infrastructure.pinecone.knowledge_query_service import PineconeKnowledgeQueryService
from ddd.infrastructure.qdrant.knowledge_query_service import QdrantKnowledgeQueryService
from fastapi import Depends


# Repositories
def get_asset_repository(settings: Settings = Depends(get_settings)) -> AssetRepositoryIF:
    json_config_path = settings.assets_config_path
    auth_config = AuthConfig(
        server_url=settings.oauth_server_url,
        realm_name=settings.oauth_realm_name,
        client_id=settings.oauth_client_id,
        client_secret=settings.oauth_client_secret,
        grant_type="client_credentials",
    )
    return JSONandKeycloakAssetRepository(json_config_path, auth_config)


def get_connector_repository(settings: Settings = Depends(get_settings)) -> ConnectorRepositoryIF:
    json_config_path = settings.connectors_config_path
    return JSONConnectorRepository(json_config_path)


def get_auth_repository(settings: Settings = Depends(get_settings)) -> AuthRepositoryIF:
    config = AuthConfig(
        server_url=settings.oauth_server_url,
        realm_name=settings.oauth_realm_name,
        client_id=settings.oauth_client_id,
        client_secret=settings.oauth_client_secret,
        grant_type="client_credentials",
    )
    return KeycloakAuthRepository(config)


def get_knowledge_query_service(settings: Settings = Depends(get_settings)) -> KnowledgeQueryServiceIF:
    service = settings.vector_db_service
    if service == "pinecone":
        return PineconeKnowledgeQueryService(
            api_key=settings.vector_db_api_key,
            index_name=settings.vector_db_index_name,
            text_key_in_metadata=settings.vector_db_metadata_text_key,
        )
    elif service == "qdrant":
        return QdrantKnowledgeQueryService(
            url=settings.vector_db_url,
            api_key=settings.vector_db_api_key,
            index_name=settings.vector_db_index_name,
            text_key_in_metadata=settings.vector_db_metadata_text_key,
        )
    else:
        raise ValueError(f"Unsupported vector db service: {service}")


def get_qa_service(settings: Settings = Depends(get_settings)) -> QAServiceIF:
    llm_service = settings.llm_service
    if llm_service == "ollama":
        return OllamaQAService(api_base_url=settings.llm_api_base_url)
    elif llm_service == "openai":
        raise NotImplementedError
    else:
        raise ValueError(f"Unsupported LLM service: {llm_service}")


async def get_dataspace_asset_catalog_query_service(
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
) -> DataspaceAssetCatalogQueryServiceIF:
    access_token = await auth_repository.authenticate()

    return DataspaceAssetCatalogQueryServiceImpl(
        dataspace_access_token=access_token, connector_repository=connector_repository
    )


async def get_dataspace_knowledge_query_service(
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
) -> DataspaceKnowledgeQueryServiceIF:
    access_token = await auth_repository.authenticate()

    return DataspaceKnowledgeQueryServiceImpl(
        dataspace_access_token=access_token, connector_repository=connector_repository
    )


async def get_dataspace_qa_service(
    auth_repository: AuthRepositoryIF = Depends(get_auth_repository),
    connector_repository: ConnectorRepositoryIF = Depends(get_connector_repository),
) -> DataspaceQAServiceIF:
    access_token = await auth_repository.authenticate()

    return DataspaceQAServiceImpl(dataspace_access_token=access_token, connector_repository=connector_repository)
