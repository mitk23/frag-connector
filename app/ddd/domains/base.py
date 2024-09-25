from pydantic import BaseModel, ConfigDict


class ValueObject(BaseModel):
    model_config = ConfigDict(frozen=True)

    def __str__(self) -> str:
        return str(self.value)
