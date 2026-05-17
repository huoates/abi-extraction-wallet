from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List, Dict, Any, Optional


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
    created_at: datetime
    dimension_x: int
    dimension_y: int
    name: str
    name_in_raid: str | None
    thumbnail_url: str | None


class Opening(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    created_at: datetime
    difficulty_id: int
    zone_id: int
    container_id: int
    difficulty: Optional[Difficulty] = None
    zone: Optional[Zone] = None
    container: Optional[Container] = None


class GenaiItemDetails(BaseModel):
    quantity: int
    item_name: str


class GenaiOutputJson(BaseModel):
    items: List[GenaiItemDetails]
    container_name: str


class AiAddLootSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    created_at: datetime
    prompt_token_count: int
    candidates_token_count: int
    total_token_count: int
    difficulty: Optional[Difficulty]
    zone: Optional[Zone]


class AiAddLoot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    created_at: datetime
    image_path: str
    image_hash: str
    genai_output_json: GenaiOutputJson
    ai_add_loot_session: Optional[AiAddLootSession]
    review_status: str


class Loot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: int
    created_at: datetime
    opening_id: int
    quantity: int
    item_id: int
    opening: Optional[Opening] = None
    item: Optional[Item] = None
