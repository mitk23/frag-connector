from .asset import AssetSecurityLevel
from .connector import ConnectorTrustLevel


def check_asset_access_authority_by_level(
    asset_security_level: AssetSecurityLevel, connector_trust_level: ConnectorTrustLevel
) -> bool:
    return asset_security_level.to_number() <= connector_trust_level.to_number()


def list_connector_accessible_asset_security_levels(
    connector_trust_level: ConnectorTrustLevel,
) -> list[AssetSecurityLevel]:
    accessible_asset_levels = []

    all_asset_security_levels = AssetSecurityLevel.list_all()
    for sec_level in all_asset_security_levels:
        if check_asset_access_authority_by_level(sec_level, connector_trust_level):
            accessible_asset_levels.append(sec_level)

    return accessible_asset_levels
