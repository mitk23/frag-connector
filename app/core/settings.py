import json
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # model_config = SettingsConfigDict(env_file=".env")

    # Connector Infomation
    connector_name: str = Field(alias="MY_CONNECTOR_NAME", default="my-frag-connector")
    connector_fqdn: str = Field(alias="MY_CONNECTOR_FQDN", default="http://localhost")
    connector_port: int = Field(alias="MY_CONNECTOR_PORT", default=8000)
    connector_origin: str = f"{connector_fqdn}:{connector_port}"
    participant_id: str = Field(alias="MY_PARTICIPANT_ID", default="test")
    connector_api_key: str = Field(alias="MY_CONNECTOR_API_KEY", default="DefaultApiKey")

    # Authentication / Authorization
    oauth_server_url: str = "http://localhost:8080"
    oauth_realm_name: str = "realm"
    oauth_client_id: str
    oauth_client_secret: str

    # Vector DB
    vector_db_service: Literal["pinecone", "qdrant"] | None = None
    vector_db_url: str | None = None
    vector_db_api_key: str | None = None
    vector_db_index_name: str = "test-index"
    vector_db_metadata_text_key: str | None = "text"

    # LLM
    llm_service: Literal["openai", "ollama"] | None = None
    llm_api_key: str | None = None
    llm_api_base_url: str = "http://localhost:11434"

    # JSON File Paths
    assets_config_path: str = "assets.json"
    connectors_config_path: str = "connectors.json"


def load_connectors_config() -> list[dict]:
    settings = Settings()

    with open(settings.connectors_config_path, "r") as file:
        connectors_config: list[dict] = json.load(file)
    return connectors_config
