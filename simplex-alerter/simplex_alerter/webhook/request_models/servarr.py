from jinja2 import Environment
from pydantic import BaseModel
from typing import Union, Optional

{
    "series": {
        "id": 1,
        "title": "Test Title",
        "path": "C:\\testpath",
        "tvdbId": 1234,
        "tvMazeId": 0,
        "tmdbId": 0,
        "type": "standard",
        "year": 0,
        "tags": [
            "test-tag"
        ]
    },
    "episodes": [
        {
            "id": 123,
            "episodeNumber": 1,
            "seasonNumber": 1,
            "title": "Test title",
            "seriesId": 0,
            "tvdbId": 0
        }
    ],
    "eventType": "Test",
    "instanceName": "Sonarr",
    "applicationUrl": ""
}

class SonarrAlert(BaseModel):
    series: dict
    episodes: list
    eventType: str
    downloadClient: Optional[str]
    instanceName: Optional[str]
    applicationUrl: Optional[str]
    customFormatInfo: Optional[dict]
    downloadClient: Optional[str]
    downloadClientType: Optional[str]
    downloadId: Optional[str]
    release: Optional[dict]

    def __init__(self, *args, **kwargs):
        self.template = """
{eventType}

{seriesTitle}

{$ for i in series.images%}
{% if i["coverType"] == "poster"%}
{{i["remoteUrl"]}}
{%endfor%}

{% for ep in episodes %}
- S{{ep["seasonNumber"]}}E{{ep["episodeNumber"]}}
{%endfor%}
"""

    def render(self):
        template = Environment.from_string(self.template)
        return template.render(self.__dict__)


ServarrAlert = Union[SonarrAlert]
