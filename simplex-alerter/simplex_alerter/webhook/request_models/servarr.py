from jinja2 import Template
from pydantic import BaseModel
from typing import Union, Optional


class SonarrAlert(BaseModel):
    eventType: str
    source: Optional[str] = None
    host: Optional[str] = None
    series: Optional[dict]
    episodes: Optional[list]
    release: Optional[dict] = None
    instanceName: Optional[str] = None
    trigger: Optional[str] = None
    applicationUrl: Optional[str] = None
    customFormatInfo: Optional[dict] = None
    downloadClient: Optional[str] = None
    downloadClientType: Optional[str] = None
    downloadId: Optional[str] = None
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Template(
            """
event: {{eventType}}
{% if series != None %}
{{series.title}}
    {% for i in series.images%}
        {% if i["coverType"] == "poster" %}
{{i["remoteUrl"]}}
        {% endif %}
    {% endfor %}
{% endif %}
{% if release != None %}
{{ release.releaseTitle}} found on {{ release.indexer }}
{% endif %}
{% if episodes != None %}
    {% for ep in episodes %}
- S{{ep["seasonNumber"]}}E{{ep["episodeNumber"]}}
    {% endfor %}
{% endif %}
""",
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def render(self):
        return await self.template.render_async(self.model_dump())


ServarrAlert = Union[SonarrAlert]
