from typing import Any

from .asset import AssetSecurityLevel, VectorFilter
from .connector import ConnectorTrustLevel
from .knowledge import Knowledge


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


def filter_knowledge_by_id(id: str, id_set: set[str]) -> bool | None:
    """
    check knowledge id is included in id_set.
    If '*' (wildcard) is in id_set, return true to any knowledge.
    If id_set is empty, return null.
    """
    if len(id_set) == 0:
        return None
    return ("*" in id_set) | (id in id_set)


def filter_knowledge_by_metadata(
    knowledge_metadata: dict[str, Any], metadata_match_expression: dict[str, str | list[str]]
) -> bool | None:
    """
    AND operation to multiple metadata match filters.
    If metadata_match_expression is empty, return null.
    """

    if len(metadata_match_expression) == 0:
        return None

    match_result = True
    for _key, _value in metadata_match_expression.items():
        if not isinstance(knowledge_metadata.get(_key), str):
            # _key not in knowledge metadata or not string type
            continue

        if isinstance(_value, str):  # exact match
            match_result &= knowledge_metadata[_key] == _value
        elif isinstance(_value, list):  # any match
            match_result &= knowledge_metadata[_key] in set(_value)
    return match_result


def filter_knowledge_vector(knowledge: Knowledge, filter: VectorFilter) -> bool:
    # (null, null) -> false
    # (false, null) -> false
    # (true, null) -> true
    # (null, false) -> false
    # (false, false) -> false
    # (true, false) -> false
    # (null, true) -> true
    # (false, true) -> false
    # (true, true) -> true

    matched_by_id = filter_knowledge_by_id(knowledge.id, filter.has_id)
    matched_by_metadata = filter_knowledge_by_metadata(knowledge.metadata, filter.has_metadata)

    if matched_by_id is None and matched_by_metadata is None:
        return False
    elif matched_by_id is None:
        return matched_by_metadata
    elif matched_by_metadata is None:
        return matched_by_id

    return matched_by_id and matched_by_metadata
