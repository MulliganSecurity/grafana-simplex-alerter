from jinja2 import Environment
from pydantic import BaseModel
from typing import Union, Optional

class SonarrAlert(BaseModel):
    series: dict
    episodes: list
    eventType: str
    instanceName: Optional[str]
    applicationUrl: Optional[str]
    customFormatInfo: Optional[dict]
    downloadClient: Optional[str]
    downloadClientType: Optional[str]
    downloadId: Optional[str]
    release: Optional[dict]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = """
{eventType}

{series.title}

{% for i in series.images%}
{% if i["coverType"] == "poster" %}
{{i["remoteUrl"]}}
{%endfor%}

{% for ep in episodes %}
- S{{ep["seasonNumber"]}}E{{ep["episodeNumber"]}}
{%endfor%}
"""

    def render(self):
        template = Environment.from_string(self.template)
        return template.render(self.model_dump())


ServarrAlert = Union[SonarrAlert]
