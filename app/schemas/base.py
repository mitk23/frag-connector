from pydantic import BaseModel


class BaseApiSchema(BaseModel):
    def to_dict(self):
        return self.model_dump(mode="json")

    @classmethod
    def from_dict(cls, dic: dict):
        return cls.model_validate(dic)
