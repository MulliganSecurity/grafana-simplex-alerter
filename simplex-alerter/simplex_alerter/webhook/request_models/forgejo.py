from pydantic import BaseModel
from typing import Union, Optional
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

class ReviewRequest(BaseModel):
    action: str
    number: int
    pull_request: dict
    requested_reviewer: dict
    repository: dict
    sender: dict
    commit_id: str
    review: Optional[dict]


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Template("""
PR Review requested

Review of PR#{{pull_request["id"]}}({{ pull_request["title"] }})

{{pull_request["url"]}}

by {{sender.login}}

requested from:
{% for r in pull_request["requested_reviewers"] %}
- @{{r["login"]}}
{% endfor %}
""", enable_async = True)

    async def render(self):
        return await self.template.render_async(self.model_dump())


ForgeJoAlerts = Union [PushNotification, ReviewRequest]
