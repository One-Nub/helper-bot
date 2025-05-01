from typing import Optional

from attrs import Factory, define, field


@define(kw_only=True)
class MessageComponentData:
    custom_id: str
    component_type: int
    id: Optional[str]
    values: Optional[list[str]] = field(default=Factory(list))
    resolved: Optional[dict] = field(default=Factory(dict))
