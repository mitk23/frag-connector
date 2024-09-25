from api.dependencies.settings import get_settings
from api.dependencies.usecase import get_authorization_usecase
from core.exceptions import ConnectorException
from core.settings import Settings
from ddd.usecases.authorization import AuthorizationUsecase
from fastapi import Depends, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

# API Key for Connector Management
api_key_header = APIKeyHeader(
    name="X-Management-Api-Key",
    scheme_name="Management API Key",
    description="API key to access connector management API",
    auto_error=True,
)


async def verify_api_key(api_key: str = Depends(api_key_header), settings: Settings = Depends(get_settings)) -> None:
    if api_key != settings.connector_api_key:
        raise ConnectorException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            description="Invalid management API key",
        )


# Inter-Connector Access Token
bearer_header = HTTPBearer(
    scheme_name="OAuth 2.0 Access Token",
    description="Access token to get resources via connector",
    auto_error=True,
)


async def get_bearer_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_header)) -> str:
    return credentials.credentials


async def verify_bearer_token(
    bearer_token: str = Depends(get_bearer_token),
    authorization_usecase: AuthorizationUsecase = Depends(get_authorization_usecase),
) -> None:
    is_active = await authorization_usecase.verify_token(bearer_token)
    if not is_active:
        raise ConnectorException(status_code=status.HTTP_401_UNAUTHORIZED, description="Invalid access token")
