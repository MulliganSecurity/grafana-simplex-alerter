from jinja2 import Template
from pydantic import BaseModel
from typing import Union, Optional
import json


class SonarrAlert(BaseModel):
    eventType: str
    source: Optional[str] = None
    host: Optional[str] = None
    series: Optional[dict] = None
    movie: Optional[dict] = None
    remoteMovie: Optional[dict] = None
    episodes: Optional[list] = None
    release: Optional[dict] = None
    instanceName: Optional[str] = None
    trigger: Optional[str] = None
    applicationUrl: Optional[str] = None
    customFormatInfo: Optional[dict] = None
    downloadClient: Optional[str] = None
    downloadClientType: Optional[str] = None
    downloadId: Optional[str] = None
    template: str = None
    raw_values: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.raw_values = json.dumps(kwargs, indent = 4)
        self.template = Template(
            """
event: {{eventType}}
{% if series != None %}
{{series.title}}
{% endif %}
{% if release != None %}
{{ release.releaseTitle}} {% if release.indexer %}found on {{ release.indexer }} {% endif %}
{% endif %}
{% if episodes != None %}
    {% for ep in episodes %}
- S{{ep["seasonNumber"]}}E{{ep["episodeNumber"]}}
    {% endfor %}
{% endif %}
{% if movie != None %}
{{movie["title"]}}
{{movie["overview"]}}
{% endif %}

{% if eventType == "ManualInteractionRequired" %}
raw_json: {{raw_values}}
{% endif %}
""",
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def render(self):
        return await self.template.render_async(self.model_dump())


ServarrAlert = Union[SonarrAlert]
