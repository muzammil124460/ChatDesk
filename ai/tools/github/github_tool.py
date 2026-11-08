import json
import base64
import httpx

from typing import Optional, List
from langchain_core.tools import tool

from ai.tools.github.connection import GitHubConnection


# --------------------------------------------------
# COMMON HELPER
# --------------------------------------------------

async def get_github_api(method: str, endpoint: str, **kwargs):

    github = GitHubConnection()

    try:
        return await github.request(
            method=method,
            endpoint=endpoint,
            **kwargs
        )

    except httpx.HTTPStatusError as e:

        return {
            "error": True,
            "status_code": e.response.status_code,
            "message": e.response.text[:1000]
        }

    except Exception as e:

        return {
            "error": True,
            "message": str(e)
        }

    finally:
        await github.close()


# --------------------------------------------------
# OUTPUT HELPERS (token control)
# --------------------------------------------------

MAX_CHARS = 6000  # ~1.5-2k tokens, safety net only
MAX_PER_PAGE = 30  # hard upper limit for any list tool


def clamp(per_page: int) -> int:
    return min(max(per_page, 1), MAX_PER_PAGE)


def format_result(data):
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(text) > MAX_CHARS:
        return (
            text[:MAX_CHARS]
            + f"... [TRUNCATED, total {len(text)} chars. "
            "Do not call this tool again; answer from the data above.]"
        )
    return text


def is_error(data):
    return isinstance(data, dict) and data.get("error")


def slim_repo(r):
    return {
        "full_name": r.get("full_name"),
        "description": (r.get("description") or "")[:200],
        "private": r.get("private"),
        "html_url": r.get("html_url"),
        "language": r.get("language"),
        "default_branch": r.get("default_branch"),
        "updated_at": r.get("updated_at"),
    }


def slim_issue(i):
    return {
        "number": i.get("number"),
        "title": i.get("title"),
        "state": i.get("state"),
        "user": (i.get("user") or {}).get("login"),
        "labels": [l.get("name") for l in i.get("labels", [])],
        "html_url": i.get("html_url"),
        "created_at": i.get("created_at"),
        "body": (i.get("body") or "")[:300],
    }


def slim_pr(p):
    return {
        "number": p.get("number"),
        "title": p.get("title"),
        "state": p.get("state"),
        "draft": p.get("draft"),
        "user": (p.get("user") or {}).get("login"),
        "head": (p.get("head") or {}).get("ref"),
        "base": (p.get("base") or {}).get("ref"),
        "html_url": p.get("html_url"),
        "created_at": p.get("created_at"),
        "merged_at": p.get("merged_at"),
        "body": (p.get("body") or "")[:300],
    }


def slim_commit(c):
    commit = c.get("commit") or {}
    author = commit.get("author") or {}
    return {
        "sha": (c.get("sha") or "")[:7],
        "message": (commit.get("message") or "").split("\n")[0],
        "author": author.get("name"),
        "date": author.get("date"),
        "html_url": c.get("html_url"),
    }


def slim_created(data):
    """Small confirmation for create/update operations."""
    return {
        "number": data.get("number"),
        "title": data.get("title"),
        "state": data.get("state"),
        "html_url": data.get("html_url"),
    }


# ==================================================
# TOOLS
# ==================================================

async def get_tools():

    # ==================================================
    # 1. REPOSITORY MANAGEMENT (4 TOOLS)
    # ==================================================

    @tool
    async def search_repositories(query: str, per_page: int = 10) -> str:
        """
        Search GitHub repositories using keywords.
        Example: Search repositories related to Python AI agents.
        """

        data = await get_github_api(
            "GET",
            "/search/repositories",
            params={
                "q": query,
                "per_page": clamp(per_page)
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result({
            "total_count": data.get("total_count"),
            "items": [slim_repo(r) for r in data.get("items", [])]
        })


    @tool
    async def list_my_repositories(per_page: int = 10) -> str:
        """
        List repositories accessible to the authenticated GitHub user.
        """

        data = await get_github_api(
            "GET",
            "/user/repos",
            params={
                "sort": "updated",
                "direction": "desc",
                "per_page": clamp(per_page),
                "affiliation": "owner,collaborator,organization_member"
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result([slim_repo(r) for r in data])


    @tool
    async def get_repository(owner: str, repo: str) -> str:
        """
        Get details of a specific GitHub repository.
        Requires repository owner and repository name.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}"
        )

        if is_error(data):
            return format_result(data)

        info = slim_repo(data)
        info["open_issues_count"] = data.get("open_issues_count")
        info["stargazers_count"] = data.get("stargazers_count")
        info["forks_count"] = data.get("forks_count")

        return format_result(info)


    @tool
    async def create_repository(
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True
    ) -> str:
        """
        Create a new repository in the authenticated user's GitHub account.
        """

        data = await get_github_api(
            "POST",
            "/user/repos",
            json={
                "name": name,
                "description": description,
                "private": private,
                "auto_init": auto_init
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result(slim_repo(data))


    # ==================================================
    # 2. CODE MANAGEMENT (3 TOOLS)
    # ==================================================

    @tool
    async def read_file(owner: str, repo: str, path: str) -> str:
        """
        Read a file from a GitHub repository.
        Path example: README.md or src/main.py.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path}"
        )

        if isinstance(data, dict) and data.get("error"):
            return format_result(data)

        if isinstance(data, list):
            return "The provided path is a directory, not a single file."

        if not isinstance(data, dict):
            return format_result(data)

        if data.get("type") != "file":
            return "The requested path is not a regular file."

        if data.get("encoding") != "base64" or not data.get("content"):
            return (
                "File content is unavailable through this response. "
                "It may be too large or use another encoding."
            )

        try:
            content = base64.b64decode(data["content"]).decode(
                "utf-8",
                errors="replace"
            )

            truncated = len(content) > 4000
            content = content[:4000]

            return (
                f"File: {data.get('path')}\n"
                f"SHA: {data.get('sha')}\n\n"
                f"Content:\n{content}"
                + (
                    "\n\n[TRUNCATED: file is longer than 4000 chars. "
                    "Do not call this tool again for the same file.]"
                    if truncated else ""
                )
            )

        except Exception as e:
            return f"File decoding error: {str(e)}"


    @tool
    async def search_code(
        owner: str,
        repo: str,
        query: str,
        per_page: int = 10
    ) -> str:
        """
        Search code inside a specific GitHub repository.
        Example: Find JWT authentication code in a repository.
        """

        data = await get_github_api(
            "GET",
            "/search/code",
            params={
                "q": f"{query} repo:{owner}/{repo}",
                "per_page": clamp(per_page)
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result({
            "total_count": data.get("total_count"),
            "items": [
                {
                    "name": i.get("name"),
                    "path": i.get("path"),
                    "html_url": i.get("html_url")
                }
                for i in data.get("items", [])
            ]
        })


    @tool
    async def list_branches(
        owner: str,
        repo: str,
        per_page: int = 10
    ) -> str:
        """
        List branches of a GitHub repository.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={
                "per_page": clamp(per_page)
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result([
            {"name": b.get("name"), "protected": b.get("protected")}
            for b in data
        ])


    # ==================================================
    # 3. ISSUES MANAGEMENT (4 TOOLS)
    # ==================================================

    @tool
    async def list_issues(
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 10
    ) -> str:
        """
        List issues of a GitHub repository.
        State can be open, closed or all.
        Pull requests are excluded from the results.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": state,
                "per_page": clamp(per_page)
            }
        )

        if is_error(data):
            return format_result(data)

        issues = [
            issue for issue in data
            if "pull_request" not in issue
        ]

        return format_result([slim_issue(i) for i in issues])


    @tool
    async def get_issue(
        owner: str,
        repo: str,
        issue_number: int
    ) -> str:
        """
        Get details of a specific GitHub issue.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/issues/{issue_number}"
        )

        if is_error(data):
            return format_result(data)

        return format_result(slim_issue(data))


    @tool
    async def create_issue(
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None
    ) -> str:
        """
        Create a new issue in a GitHub repository.
        """

        payload = {
            "title": title,
            "body": body
        }

        if labels:
            payload["labels"] = labels

        data = await get_github_api(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json=payload
        )

        if is_error(data):
            return format_result(data)

        return format_result(slim_created(data))


    @tool
    async def update_issue(
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        state: Optional[str] = None
    ) -> str:
        """
        Update a GitHub issue's title, body or state.
        State can be open or closed.
        """

        payload = {}

        if title is not None:
            payload["title"] = title

        if body is not None:
            payload["body"] = body

        if state is not None:
            payload["state"] = state

        if not payload:
            return "No update fields provided."

        data = await get_github_api(
            "PATCH",
            f"/repos/{owner}/{repo}/issues/{issue_number}",
            json=payload
        )

        if is_error(data):
            return format_result(data)

        return format_result(slim_created(data))


    # ==================================================
    # 4. PULL REQUEST MANAGEMENT (3 TOOLS)
    # ==================================================

    @tool
    async def list_pull_requests(
        owner: str,
        repo: str,
        state: str = "open",
        per_page: int = 10
    ) -> str:
        """
        List pull requests of a GitHub repository.
        State can be open, closed or all.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": state,
                "per_page": clamp(per_page)
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result([slim_pr(p) for p in data])


    @tool
    async def get_pull_request(
        owner: str,
        repo: str,
        pull_number: int
    ) -> str:
        """
        Get details of a specific GitHub pull request.
        """

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}"
        )

        if is_error(data):
            return format_result(data)

        return format_result(slim_pr(data))


    @tool
    async def create_pull_request(
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: str = "",
        draft: bool = False
    ) -> str:
        """
        Create a pull request.
        Head is the source branch and base is the target branch.
        """

        data = await get_github_api(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json={
                "title": title,
                "head": head,
                "base": base,
                "body": body,
                "draft": draft
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result(slim_created(data))


    # ==================================================
    # 5. COMMITS AND COMMENTS (2 TOOLS)
    # ==================================================

    @tool
    async def list_commits(
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        per_page: int = 10
    ) -> str:
        """
        List commits of a GitHub repository.
        Optionally filter commits by branch or commit SHA.
        """

        params = {
            "per_page": clamp(per_page)
        }

        if branch:
            params["sha"] = branch

        data = await get_github_api(
            "GET",
            f"/repos/{owner}/{repo}/commits",
            params=params
        )

        if is_error(data):
            return format_result(data)

        return format_result([slim_commit(c) for c in data])


    @tool
    async def create_comment(
        owner: str,
        repo: str,
        issue_number: int,
        comment: str
    ) -> str:
        """
        Create a comment on a GitHub issue or pull request.
        """

        data = await get_github_api(
            "POST",
            f"/repos/{owner}/{repo}/issues/{issue_number}/comments",
            json={
                "body": comment
            }
        )

        if is_error(data):
            return format_result(data)

        return format_result({
            "id": data.get("id"),
            "html_url": data.get("html_url")
        })


    return [
        search_repositories,
        list_my_repositories,
        get_repository,
        create_repository,
        read_file,
        search_code,
        list_branches,
        list_issues,
        get_issue,
        create_issue,
        update_issue,
        list_pull_requests,
        get_pull_request,
        create_pull_request,
        list_commits,
        create_comment,
    ]