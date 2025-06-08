from pydantic import BaseModel
from typing import Union

ServarrAlert = Union[Prowlarr]

class ProwlarrAlert(BaseModel):
    pass
