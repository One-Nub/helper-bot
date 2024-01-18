import logging

import aiohttp
from attr import define

instance: "LinearAPI" = None
LINEAR_URL = "https://api.linear.app/graphql"

logger = logging.getLogger("LINEAR_GQL")


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

    async def get_teams(self):
        """Get Linear teams, necessary for issue creation."""
        req = await self.session.get(LINEAR_URL, params={"query": "{teams{nodes{id,name,key}}}"})

        return await req.json()

    async def create_issue(self, team_id: str, title: str, description: str = None):
        """Create an issue in the triage panel"""
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
                }
                success
            }
        }
        """

        req = await self.session.post(LINEAR_URL, json={"query": query, "variables": variables})

        return await req.json()

    async def get_issues(self, query_filter: str = None) -> list[dict]:
        """Get all issues that optionally match a filter string."""
        variables: dict = {
            "filter": {
                "or": [
                    {"title": {"containsIgnoreCase": query_filter}},
                    {"description": {"containsIgnoreCase": query_filter}},
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
                raise InterruptedError()

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

        return matching_nodes
