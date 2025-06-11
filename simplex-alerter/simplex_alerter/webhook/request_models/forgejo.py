from pydantic import BaseModel
import json
from typing import Union, Optional
from jinja2 import Template


class PushNotification(BaseModel):
    ref: str
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
            """New content pushed to {{repository["full_name"]}} by {{head_commit["author"]["name"]}}!
- {{head_commit["message"]}}""",
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
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
            """Issue #{{issue["id"]}} ({{issue["title"]}}) opened on {{issue["repository"]["full_name"]}}!
{{issue["url"]}}

{% if action == "assigned" %}
Has been assigned to:
{% for a in issue["assignees"] %}
- @{{ a["login"] }}
{% endfor %}
{% elif action == "unassigned" %}
Has been unassigned
{% elif action == "opened" %}
Has been opened by {{issue["user"]["login"]}}
{% elif action == "closed" %}
Has been closed by {{sender["login"]}}
{% else %}
Unknown action: {{action}}
{% endif %}

""",
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
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
            template_text = """New PR Created!

PR#{{pull_request["id"]}}({{ pull_request["title"] }})
{{pull_request["url"]}}
was opened against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}
"""
        elif kwargs["action"] == "review_requested":
            template_text = """PR Review requested

Review of PR#{{pull_request["id"]}}({{ pull_request["title"] }})
{{pull_request["url"]}}
by {{sender.login}}
requested from:
{% for r in pull_request["requested_reviewers"] %}
- @{{r["login"]}}
{% endfor %}
            """

        elif kwargs["action"] == "reviewed":
            template_text = """PR Reviewed!

PR#{{pull_request["id"]}}({{ pull_request["title"] }})
against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}
{{pull_request["url"]}}
was reviewed by {{sender["login"]}}
{{review["content"]}}

            """

        elif kwargs["action"] == "closed":
            template_text = """PR closed!

PR#{{pull_request["id"]}}({{ pull_request["title"] }})
against {{pull_request["base"]["repo"]["full_name"]}}
{{pull_request["url"]}}
{% if pull_request["merged"] %}
{{ pull_request["merged_by"]["login"] }} merged it into {{pull_request["base"]["repo"]["full_name"]}}
{% else %}
{{sender.login}} closed it
{% endif %}
            """
        else:
            template_text = json.dumps(kwargs)
        self.template = Template(
            template_text,
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def render(self):
        return await self.template.render_async(**self.model_dump())


class WorkflowNotification(BaseModel):
    action: str
    workflow_job: dict
    organization: dict
    repository: dict
    sender: dict
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if kwargs["action"] == "in_progress":
            template_text = """New workflow started!
Workflow #{{workflow_job["id"]}}-{{wokflow_job["run_id"]}} started on {{repository["full_name"]}}
Steps:
{% for s in workflow_job["steps"] %}
- {{s["name"]}}
{% endfor %}
            """
        elif kwargs["action"] == "completed":
            template_text = """Workflow completed
Workflow #{{workflow_job["id"]}}-{{wokflow_job["run_id"]}} on {{repository["full_name"]}} completed
Result: {{workflow_job["conclusion"]}}
Steps:
{% for s in workflow_job["steps"] %}
- {{s["name"]}}: {{s["conclusion"]}}
{% endfor %}"""

        else:
            template_text = json.dumps(kwargs)

        self.template = Template(
            template_text,
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def render(self):
        return await self.template.render_async(**self.model_dump())


ForgeJoAlerts = Union[PushNotification, PullRequest, IssueCreated, WorkflowNotification]
