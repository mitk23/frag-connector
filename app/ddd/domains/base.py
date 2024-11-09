import uuid

from pydantic import UUID4, BaseModel, ConfigDict


class ValueObject(BaseModel):
    model_config = ConfigDict(frozen=True)

    def __str__(self) -> str:
        return str(self.value)


class BaseUUID4(ValueObject):
    value: UUID4

    @staticmethod
    def generate_id() -> UUID4:
        return uuid.uuid4()

    @classmethod
    def generate(cls) -> "BaseUUID4":
        return cls(value=cls.generate_id())
