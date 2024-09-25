import json
import os

from core.exceptions import InternalException
from ddd.domains.connector import Connector, ConnectorId, ConnectorRepositoryIF
from ddd.usecases.schemas.connector import ConnectorDto


class JSONConnectorRepository(ConnectorRepositoryIF):
    def __init__(self, json_config_path: str):
        self.__json_config_path = json_config_path
        self.__connectors = self.__load_config()

    def __handle_error(self, error: Exception, description: str):
        raise InternalException(description=description, upstream_exc=error)

    def __validate_json(self, obj: object) -> bool:
        try:
            json.dumps(obj)
        except (TypeError, ValueError) as err:
            self.__handle_error(error=err, description="Invalid json object")
        return True

    def __load_config(self) -> dict[str, ConnectorDto]:
        if not os.path.isfile(self.__json_config_path):
            with open(self.__json_config_path, "w") as file:
                json.dump({}, file)

        with open(self.__json_config_path, "r") as file:
            connectors: dict[str, dict] = json.load(file)

        connectors_validated = {_id: ConnectorDto.model_validate(connector) for _id, connector in connectors.items()}
        return connectors_validated

    def __write_config(self, connectors: dict[str, ConnectorDto]) -> None:
        connectors_serialized = {str(_id): connector.model_dump() for _id, connector in connectors.items()}

        self.__validate_json(connectors_serialized)
        try:
            with open(self.__json_config_path, "w") as file:
                json.dump(connectors_serialized, file, ensure_ascii=False, indent=2)
        except OSError as err:
            self.__handle_error(error=err, description="Failed to write to connector json file")

        self.__connectors = connectors

    async def find_all(self) -> dict[ConnectorId, Connector]:
        return {ConnectorId(value=_id): connector.to_entity() for _id, connector in self.__connectors.items()}

    async def find_by_id(self, _id: ConnectorId) -> Connector | None:
        _id_str = str(_id)
        if _id_str not in self.__connectors:
            return None
        return self.__connectors.get(_id_str).to_entity()

    async def save(self, connector: Connector) -> Connector:
        # assign a new ID
        if connector.id is None:
            connector.id = ConnectorId.generate()

        new_connectors = {**self.__connectors}
        new_connectors[str(connector.id)] = ConnectorDto.from_entity(connector)

        self.__write_config(new_connectors)
        return connector

    async def delete(self, _id: ConnectorId) -> None:
        new_connectors = {**self.__connectors}
        result = new_connectors.pop(str(_id), None)
        if result is None:
            return
        self.__write_config(new_connectors)
