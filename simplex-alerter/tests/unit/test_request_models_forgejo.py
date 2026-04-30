import pytest
from simplex_alerter.webhook.request_models.forgejo import (
    PushNotification,
    PullRequest,
    IssueCreated,
    WorkflowNotification,
    CommentAdded,
)


async def test_push_render_repo(sample_forgejo_push_payload):
    model = PushNotification(**sample_forgejo_push_payload)
    result = await model.render()
    assert "alice/my-repo" in result


async def test_push_render_author(sample_forgejo_push_payload):
    model = PushNotification(**sample_forgejo_push_payload)
    result = await model.render()
    assert "Alice" in result


async def test_push_render_commit_message(sample_forgejo_push_payload):
    model = PushNotification(**sample_forgejo_push_payload)
    result = await model.render()
    assert "Add new feature" in result


async def test_pr_opened():
    payload = {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "Add cool feature",
            "html_url": "https://forgejo.example.com/pr/42",
            "base": {"repo": {"full_name": "alice/my-repo"}},
            "merged": False,
            "requested_reviewers": [],
        },
        "repository": {"full_name": "alice/my-repo"},
        "sender": {"login": "bob"},
        "commit_id": "abc123",
    }
    model = PullRequest(**payload)
    result = await model.render()
    assert "Add cool feature" in result
    assert "PR#42" in result


async def test_pr_closed_merged():
    payload = {
        "action": "closed",
        "number": 42,
        "pull_request": {
            "number": 42,
            "title": "Add cool feature",
            "html_url": "https://forgejo.example.com/pr/42",
            "base": {"repo": {"full_name": "alice/my-repo"}},
            "merged": True,
            "merged_by": {"login": "alice"},
            "requested_reviewers": [],
        },
        "repository": {"full_name": "alice/my-repo"},
        "sender": {"login": "alice"},
        "commit_id": "abc123",
    }
    model = PullRequest(**payload)
    result = await model.render()
    assert "merged" in result.lower() or "alice" in result


async def test_issue_opened():
    payload = {
        "action": "opened",
        "issue": {
            "number": 10,
            "title": "Bug report",
            "html_url": "https://forgejo.example.com/issues/10",
            "repository": {"full_name": "alice/my-repo"},
            "user": {"login": "carol"},
            "assignees": [],
        },
        "repository": {"full_name": "alice/my-repo"},
        "sender": {"login": "carol"},
        "commit_id": "",
    }
    model = IssueCreated(**payload)
    result = await model.render()
    assert "Bug report" in result
    assert "Issue #10" in result


async def test_workflow_in_progress():
    payload = {
        "action": "in_progress",
        "workflow_job": {
            "id": 1001,
            "run_id": 2002,
            "html_url": "https://forgejo.example.com/actions/runs/2002",
            "steps": [
                {"name": "Build", "conclusion": None},
                {"name": "Test", "conclusion": None},
            ],
        },
        "organization": {"login": "myorg"},
        "repository": {"full_name": "alice/my-repo"},
        "sender": {"login": "alice"},
    }
    model = WorkflowNotification(**payload)
    result = await model.render()
    assert "1001" in result
    assert "Build" in result


async def test_workflow_completed():
    payload = {
        "action": "completed",
        "workflow_job": {
            "id": 1001,
            "run_id": 2002,
            "html_url": "https://forgejo.example.com/actions/runs/2002",
            "conclusion": "success",
            "steps": [
                {"name": "Build", "conclusion": "success"},
            ],
        },
        "organization": {"login": "myorg"},
        "repository": {"full_name": "alice/my-repo"},
        "sender": {"login": "alice"},
    }
    model = WorkflowNotification(**payload)
    result = await model.render()
    assert "success" in result


async def test_comment_on_issue():
    payload = {
        "action": "created",
        "issue": {"number": 5},
        "comment": {
            "user": {"login": "dave"},
            "html_url": "https://forgejo.example.com/issues/5#comment-1",
            "body": "Looks good to me!",
        },
        "repository": {"full_name": "alice/my-repo"},
        "sender": {"login": "dave"},
        "is_pull": False,
    }
    model = CommentAdded(**payload)
    result = await model.render()
    assert "dave" in result
    assert "Looks good to me!" in result
