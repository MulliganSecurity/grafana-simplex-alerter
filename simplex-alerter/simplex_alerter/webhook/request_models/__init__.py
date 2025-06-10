from typing import Union
from .grafana import GrafanaAlert
from .servarr import ServarrAlert
from .forgejo import ForgeJoAlerts

KnownModels = Union[GrafanaAlert, ServarrAlert, ForgeJoAlerts]
