import logging

import aiohttp
from attr import define

instance: "LinearAPI" = None
LINEAR_URL = "https://api.linear.app/graphql"

logger = logging.getLogger("LINEAR_GQL")


class LinearError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@define
class IssueState:
    name: str


@define
class LinearTeam:
    id: str
    name: str
    key: str


@define
class LinearIssue:
    id: str = None
    identifier: str = None

    number: int = None
    url: str = None

    title: str = None
    description: str = None

    team: LinearTeam = None
    state: IssueState = None

    @classmethod
    def parse_extras(cls, issue_data: dict):
        team = None
        state = None

        if issue_data.get("team"):
            team = LinearTeam(**issue_data.pop("team"))

        if issue_data.get("state"):
            state = IssueState(**issue_data.pop("state"))

        return cls(**issue_data, team=team, state=state)


class LinearAPI:
    session: aiohttp.ClientSession

    def __init__(self, token: str) -> "LinearAPI":
        self.session = aiohttp.ClientSession(headers={"Authorization": token})
        global instance
        instance = self

    @classmethod
    def connect(cls, token: str = None):
        if instance:
            return instance

        return cls(token)

    async def get_teams(self) -> list[LinearTeam]:
        """Get Linear teams, necessary for issue creation."""
        req = await self.session.get(LINEAR_URL, params={"query": "{teams{nodes{id,name,key}}}"})

        resp_json = await req.json()
        if resp_json.get("errors", []):
            logger.error(resp_json)
            raise LinearError()

        team_nodes = resp_json["data"]["teams"]["nodes"]
        return [LinearTeam(**team) for team in team_nodes]

    async def create_issue(self, team_id: str, title: str, description: str = None) -> LinearIssue | None:
        """Create an issue in the triage panel for a team"""
        variables = {
            "input": {
                "title": title,
                "description": description,
                "teamId": team_id,
            }
        }
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                issue {
                    identifier
                    url
                    description
                    title
                    state {
                        name
                    }
                }
                success
            }
        }
        """

        req = await self.session.post(LINEAR_URL, json={"query": query, "variables": variables})

        resp_json = await req.json()
        if resp_json.get("errors", []):
            logger.error(resp_json)
            raise LinearError()

        if not resp_json["data"]["issueCreate"]["success"]:
            return None

        created_issue = resp_json["data"]["issueCreate"]["issue"]
        return LinearIssue.parse_extras(created_issue)

    async def get_issues(self, query_filter: str = None) -> list[LinearIssue]:
        """Get all issues that optionally match a filter string."""

        number_opt = 0
        try:
            number_opt = int(query_filter)
        except ValueError:
            pass

        variables: dict = {
            "filter": {
                "or": [
                    {"title": {"containsIgnoreCase": query_filter}},
                    {"description": {"containsIgnoreCase": query_filter}},
                    {"number": {"eq": number_opt}},
                ],
            },
            "first": 50,
        }

        query = """
        query Issues($filter: IssueFilter, $first: Int, $after: String) {
            issues(filter: $filter, first: $first, after: $after) {
                pageInfo {
                    endCursor
                    hasNextPage
                }
                nodes {
                    id
                    identifier
                    number
                    url
                    title
                    description
                }
            }
        }
        """

        post_data = {"query": query}
        if query_filter:
            post_data["variables"] = variables
        else:
            variables.pop("filter")

        async def make_request() -> tuple[dict, dict]:
            req = await self.session.post(LINEAR_URL, json=post_data)

            resp_json = await req.json()
            if resp_json.get("errors", []):
                logger.error(resp_json)
                raise LinearError()

            page_info = resp_json["data"]["issues"]["pageInfo"]
            nodes = resp_json["data"]["issues"]["nodes"]
            return (page_info, nodes)

        page_info, nodes = await make_request()

        matching_nodes: list = nodes

        has_next_page = page_info.get("hasNextPage", False)

        while has_next_page:
            variables["after"] = page_info["endCursor"]
            post_data["variables"] = variables

            page_info, nodes = await make_request()
            matching_nodes.extend(nodes)
            has_next_page = page_info.get("hasNextPage", False)

        return [LinearIssue.parse_extras(issue) for issue in matching_nodes]

    async def get_issue(self, key: str) -> LinearIssue:
        """Get a single issue from Linear based on the ID of the issue."""

        variables: dict = {
            "issueId": key,
        }

        query = """
        query Issue($issueId: String!) {
            issue(id: $issueId) {
                id
                identifier
                number
                url
                title
                description
            }
        }
        """

        post_data = {"query": query, "variables": variables}

        req = await self.session.post(LINEAR_URL, json=post_data)

        resp_json = await req.json()
        if resp_json.get("errors", []):
            logger.error(resp_json)
            raise LinearError()

        return LinearIssue.parse_extras(resp_json["data"]["issue"])

    async def search_for_issues(self, query: str) -> list[LinearIssue]:
        """Search for an issue on Linear using the *right* query for it..."""
        variables = {
            "first": 25,
            "term": query,
        }

        query = """
        query Issue($term: String!, $first: Int, $after: String) {
            searchIssues(term: $term, first: $first, after: $after) {
                nodes {
                    id
                    identifier
                    number
                    url
                    title
                    description
                    state {
                        name
                    }
                }
            }
        }
        """

        post_data = {"query": query, "variables": variables}

        req = await self.session.post(LINEAR_URL, json=post_data)
        resp_json = await req.json()
        if resp_json.get("errors", []):
            logger.error(resp_json)
            raise LinearError()

        issue_list = resp_json["data"]["searchIssues"]["nodes"]
        return [LinearIssue.parse_extras(issue) for issue in issue_list]
