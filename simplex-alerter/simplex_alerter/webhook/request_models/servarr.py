from jinja2 import Environment
from pydantic import BaseModel
from typing import Union, Optional

class SonarrAlert(BaseModel):
    series: dict
    episodes: list
    eventType: str
    instanceName: Optional[str] = None
    applicationUrl: Optional[str] = None
    customFormatInfo: Optional[dict] = None
    downloadClient: Optional[str] = None
    downloadClientType: Optional[str] = None
    downloadId: Optional[str] = None
    release: Optional[dict] = None
    template: str = None


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Environment(enable_async = True).from_string("""
{eventType}

{series.title}

{% for i in series.images%}
{% if i["coverType"] == "poster" %}
{{i["remoteUrl"]}}
{%endfor%}

{% for ep in episodes %}
- S{{ep["seasonNumber"]}}E{{ep["episodeNumber"]}}
{%endfor%}
""")

    async def render(self):
        return await self.template.render_async(self.model_dump())


ServarrAlert = Union[SonarrAlert]
