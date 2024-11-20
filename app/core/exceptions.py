import json


# TODO: upstream errorの渡し方を検討する
class ConnectorException(Exception):
    def __init__(self, status_code: int, description: str, upstream_exc: Exception | None = None, **kwargs):
        self.__status_code = status_code
        self.__message = {"description": description} | kwargs
        if upstream_exc is not None:
            self.__message |= {"upstream_error": str(upstream_exc)}

        self.__detail = {"status_code": status_code} | self.__message

    def __str__(self):
        return json.dumps(self.__detail)

    def status_code(self) -> int:
        return self.__status_code

    def message(self) -> dict:
        return self.__message


class InternalException(Exception):
    def __init__(self, description: str, upstream_exc: Exception | None = None, **kwargs):
        self.__message = {"description": description} | kwargs
        if upstream_exc is not None:
            self.__message |= {"upstream_error": str(upstream_exc)}

    def __str__(self):
        return json.dumps(self.__message)

    def message(self) -> dict:
        return self.__message
