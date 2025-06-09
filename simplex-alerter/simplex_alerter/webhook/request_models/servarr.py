from jinja2 import Environment
from pydantic import BaseModel
from typing import Union


class SonarrAlert(BaseModel):
    downloadClient: str
    eventType: str
    instanceName: str
    applicationUrl: str
    customFormatInfo: dict
    downloadClient: str
    downloadClientType: str
    downloadId: str
    release: dict
    episodes: list
    series: dict

    def __init__(self):
        self.template = """
{eventType}

{seriesTitle}:

{% for ep in episodes %}
- S{{ep.seasonNumber}}E{{ep.episodeNumber}}
{%endfor%}
"""

    def render(self):
        template = Environment.from_string(self.template)
        return template.render(self.__dict__)


ServarrAlert = Union[SonarrAlert]
