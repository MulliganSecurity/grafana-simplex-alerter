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


class CommentAdded(BaseModel):
    action: str
    issue: Optional[dict] = None
    pull_request: Optional[dict] = None
    comment: dict
    repository: dict
    sender: dict
    is_pull: bool
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Template(
            """
New comment on {% if issue %}issue#{{issue["number"]}}{% elif pull_request %}PR#{{pull_request["number"]}}{% endif %} by {{comment["user"]["login"]}}:
{{comment["body"]}}
{{comment["html_url"]}}""",
            enable_async=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    async def render(self):
        return await self.template.render_async(**self.model_dump())


class IssueCreated(BaseModel):
    action: str
    issue: dict
    comment: Optional[dict] = None
    number: Optional[int] = None
    repository: dict
    sender: dict
    commit_id: str
    template: str = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.template = Template(
            """Issue #{{issue["number"]}} ({{issue["title"]}}) opened on {{issue["repository"]["full_name"]}}!
{{issue["html_url"]}}

{% if action == "assigned" %}
Has been assigned to:
{% for a in issue["assignees"] %}
- @{{ a["login"] }}
{% endfor %}
{% elif action == "unassigned" %}
Has been unassigned
{% elif action == "opened" or action ==  "created" %}
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

PR#{{pull_request["number"]}}({{ pull_request["title"] }})
{{pull_request["html_url"]}}
was opened against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}
"""
        elif kwargs["action"] == "review_requested":
            template_text = """PR Review requested

Review of PR#{{pull_request["number"]}}({{ pull_request["title"] }})
{{pull_request["html_url"]}}
by {{sender.login}}
requested from:
- @{{requested_reviewer["login"]}}
{% for r in pull_request["requested_reviewers"] %}
- @{{r["login"]}}
{% endfor %}
            """

        elif kwargs["action"] == "reviewed":
            template_text = """PR Reviewed!

PR#{{pull_request["number"]}}({{ pull_request["title"] }})
against {{pull_request["base"]["repo"]["full_name"]}} by {{sender.login}}
{{pull_request["html_url"]}}
was reviewed by {{sender["login"]}}
{{review["content"]}}

            """

        elif kwargs["action"] == "closed":
            template_text = """PR closed!

PR#{{pull_request["number"]}}({{ pull_request["title"] }})
against {{pull_request["base"]["repo"]["full_name"]}}
{{pull_request["html_url"]}}
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
Workflow #{{workflow_job["id"]}}-{{workflow_job["run_id"]}} started on {{repository["full_name"]}}
{{workflow_job["html_url"]}}
Steps:
{% for s in workflow_job["steps"] %}
- {{s["name"]}}
{% endfor %}
            """
        elif kwargs["action"] == "completed":
            template_text = """Workflow completed
Workflow #{{workflow_job["id"]}}-{{workflow_job["run_id"]}} on {{repository["full_name"]}} completed
{{workflow_job["html_url"]}}
Result: {{workflow_job["conclusion"]}}
Steps:
{% for s in workflow_job["steps"] %}
- {{s["name"]}}: {{s["conclusion"]}}
{% endfor %}"""

        elif kwargs["action"] == "queued":
            template_text = """New workflow queued!
Workflow #{{workflow_job["id"]}}-{{workflow_job["run_id"]}} queued for {{repository["full_name"]}}
{{workflow_job["html_url"]}}
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


ForgeJoAlerts = Union[
    PushNotification, PullRequest, IssueCreated, WorkflowNotification, CommentAdded
]
