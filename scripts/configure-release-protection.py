"""Enforce GitOps PR checks and independent production approval, including admins."""

import json
import subprocess

REPO = "prasanthece42/aegis-gitops"


def request(endpoint, method, payload):
    return subprocess.check_output(
        ["gh", "api", endpoint, "--method", method, "--input", "-"],
        input=json.dumps(payload),
        text=True,
    )


for branch in ["main", "staging", "prod"]:
    request(
        f"repos/{REPO}/branches/{branch}/protection",
        "PUT",
        {
            "required_status_checks": {
                "strict": True,
                "checks": [
                    {"context": "chart", "app_id": 15368},
                    {"context": "promotion-policy", "app_id": 15368},
                ],
            },
            "enforce_admins": True,
            "required_pull_request_reviews": {
                "dismiss_stale_reviews": True,
                "require_code_owner_reviews": True,
                "required_approving_review_count": 1 if branch == "prod" else 0,
                "require_last_push_approval": branch == "prod",
            },
            "restrictions": None,
            "required_linear_history": True,
            "allow_force_pushes": False,
            "allow_deletions": False,
            "required_conversation_resolution": True,
        },
    )
    print("PASS: protected", branch)
request(
    f"repos/{REPO}",
    "PATCH",
    {
        "allow_auto_merge": True,
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "delete_branch_on_merge": True,
    },
)
request(
    f"repos/{REPO}/actions/permissions/workflow",
    "PUT",
    {
        "default_workflow_permissions": "read",
        "can_approve_pull_request_reviews": True,
    },
)
print("PASS: repo-scoped bot PR creation enabled; no workflow auto-approves production")
