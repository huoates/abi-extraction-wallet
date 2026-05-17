from pydantic import BaseModel, ConfigDict


class Zone(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    name: str


class Difficulty(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    name: str


class Container(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    name: str


class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    name: str
    thumbnail_url: str | None


class Opening(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
