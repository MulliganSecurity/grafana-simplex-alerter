from pydantic import BaseModel
from typing import Union
from jinja2 import Template

class PushNotification(BaseModel):
    refs: str
    before: str
    after: str
    compare_url: str
    commits: list
    total_commits: int
    head_commit: dict
    repository: dict
    pusher: dict
    sender: dict
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Template("""
New content pushed to {{repository["full_name"}}!

{{head_commit["message"]}}""", enable_async = True)

    async def render(self):
        return await self.template.render_async(self.model_dump())
