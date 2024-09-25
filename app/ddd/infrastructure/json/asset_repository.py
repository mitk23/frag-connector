import json
import os

from core.exceptions import InternalException
from ddd.domains.asset import Asset, AssetId, AssetRepositoryIF
from ddd.usecases.schemas.asset import AssetDto


class JSONAssetRepository(AssetRepositoryIF):
    def __init__(self, json_config_path: str):
        self.__json_config_path = json_config_path
        self.__assets = self.__load_config()

    def __validate_json(self, obj: object) -> bool:
        try:
            json.dumps(obj)
        except (TypeError, ValueError) as err:
            self.__handle_error(error=err, description="Invalid json object")
        return True

    def __load_config(self) -> dict[str, AssetDto]:
        if not os.path.isfile(self.__json_config_path):
            with open(self.__json_config_path, "w") as file:
                json.dump({}, file)

        with open(self.__json_config_path, "r") as file:
            assets: dict[str, dict] = json.load(file)

        assets_validated = {_id: AssetDto.model_validate(asset) for _id, asset in assets.items()}
        return assets_validated

    def __write_config(self, assets: dict[str, AssetDto]) -> None:
        assets_serialized = {str(_id): asset.model_dump() for _id, asset in assets.items()}

        self.__validate_json(assets_serialized)
        try:
            with open(self.__json_config_path, "w") as file:
                json.dump(assets_serialized, file, ensure_ascii=False, indent=2)
        except OSError as err:
            self.__handle_error(error=err, description="Failed to write to asset json file")

        self.__assets = assets

    async def find_all(self) -> dict[AssetId, Asset]:
        return {AssetId(value=_id): asset.to_entity() for _id, asset in self.__assets.items()}

    async def find_by_id(self, _id: AssetId) -> Asset | None:
        _id_str = str(_id)
        if _id_str not in self.__assets:
            return None
        return self.__assets.get(_id_str).to_entity()

    async def save(self, asset: Asset) -> Asset:
        # assign a new ID
        if asset.id is None:
            asset.id = AssetId.generate()

        new_assets = {**self.__assets}
        new_assets[str(asset.id)] = AssetDto.from_entity(asset)

        self.__write_config(new_assets)
        return asset

    async def delete(self, _id: AssetId) -> None:
        new_assets = {**self.__assets}
        result = new_assets.pop(str(_id), None)
        if result is None:
            return
        self.__write_config(new_assets)

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)
