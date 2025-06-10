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
        self.template = Template(
            """
New content pushed to {{repository["full_name"}}!

{{head_commit["message"]}}""",
            enable_async=True,
        )

    async def render(self):
        return await self.template.render_async(**self.model_dump())


class IssueCreated(BaseModel):
    action: str
    number: int
    issue: dict
    repository: dict
    sender: dict
    commit_id: str
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Template(
            """
New issue opened!

Issue #{{issue["id"}} ({{issue["title"]}}) opened on {{issue["repository"]["full_name"]}}

{{issue["url"]}}

was opened by {{issue["user"]["login"]}}
""",
            enable_async=True,
        )

    async def render(self):
        return await self.template.render_async(**self.model_dump())


class PullRequest(BaseModel):
    action: str
    number: int
    pull_request: dict
    requested_reviewer: Optional[dict] = None
    repository: dict
    sender: dict
    commit_id: str
    review: Optional[dict] = None
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        template_text = ""
        if kwargs["action"] == "opened":
            template_text = """
New PR Created
PR#{{pull_request["id"]}}({{ pull_request["title"] }})

{{pull_request["url"]}}

was opened against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}
"""
        elif kwargs["action"] == "review_requested":
            template_text = """
PR Review requested

Review of PR#{{pull_request["id"]}}({{ pull_request["title"] }})

{{pull_request["url"]}}

by {{sender.login}}

requested from:

{% for r in pull_request["requested_reviewers"] %}
- @{{r["login"]}}
{% endfor %}
            """

        elif kwargs["action"] == "reviewed":
            template_text = """
PR Reviewed!

PR#{{pull_request["id"]}}({{ pull_request["title"] }})
against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}

{{pull_request["url"]}}

was reviewed:

{{review["content"]}}
            """

        self.template = Template(template_text, enable_async=True)

    async def render(self):
        return await self.template.render_async(**self.model_dump())


ForgeJoAlerts = Union[PushNotification, PullRequest, IssueCreated]
