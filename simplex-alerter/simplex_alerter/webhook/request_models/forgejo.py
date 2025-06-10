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
        return await self.template.render_async(self.model_dump())


class PullRequest(BaseModel):
    action: str
    number: int
    pull_request: dict
    requested_reviewer: dict
    repository: dict
    sender: dict
    commit_id: str
    review: Optional[dict] = None

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
            if kwargs["review"]["type"] == "pull_request_review_rejected":
                status = "successfully"
            else:
                status = "unsuccessfully"

            template_text = f"""
PR Reviewed!

PR#{{quest["id"]}}({{ pull_request["title"] }})
against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}

was reviewed {status}

{{review["content"]}}
            """

        self.template = Template(template_text, enable_async=True)

    async def render(self):
        return await self.template.render_async(self.model_dump())


class PROpened(BaseModel):
    action: str
    pull_request: dict


ForgeJoAlerts = Union[PushNotification, PullRequest]
