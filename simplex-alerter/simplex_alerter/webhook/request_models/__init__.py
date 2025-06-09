from typing import Union
from .grafana import GrafanaAlert
from .servarr import ServarrAlert

KnownModels = Union[GrafanaAlert, ServarrAlert]
