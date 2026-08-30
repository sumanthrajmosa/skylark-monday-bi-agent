import os
import requests

MONDAY_API_URL = os.getenv(
    "MONDAY_API_URL",
    "https://api.monday.com/v2"
)


class MondayClient:
    def __init__(self, api_token=None):
        self.api_token = api_token or os.getenv("MONDAY_API_TOKEN")

        if not self.api_token:
            raise ValueError("MONDAY_API_TOKEN is not configured")

    def query(self, query, variables=None):
        response = requests.post(
            MONDAY_API_URL,
            headers={
                "Authorization": self.api_token,
                "Content-Type": "application/json",
            },
            json={
                "query": query,
                "variables": variables or {},
            },
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("errors"):
            messages = [
                e.get("message", "Monday API error")
                for e in payload["errors"]
            ]
            raise RuntimeError("; ".join(messages))

        return payload["data"]

    def get_board_items(self, board_id, limit=500):
        """
        Retrieve ALL active items from a Monday.com board.

        Monday uses cursor-based pagination. The first request uses
        boards -> items_page, and subsequent requests use
        next_items_page.
        """

        # First page: get board metadata + first items page
        first_query = """
        query($ids:[ID!], $limit:Int!) {
            boards(ids:$ids) {
                id
                name
                columns {
                    id
                    title
                    type
                }
                items_page(limit:$limit) {
                    cursor
                    items {
                        id
                        name
                        column_values {
                            id
                            text
                            value
                        }
                    }
                }
            }
        }
        """

        data = self.query(
            first_query,
            {
                "ids": [str(board_id)],
                "limit": min(limit, 500),
            },
        )

        boards = data.get("boards", [])

        if not boards:
            return None

        board = boards[0]

        first_page = board.get("items_page", {})
        all_items = list(first_page.get("items", []))
        cursor = first_page.get("cursor")

        # Continue fetching pages until Monday gives us no cursor.
        next_query = """
        query($cursor:String!, $limit:Int!) {
            next_items_page(
                cursor:$cursor,
                limit:$limit
            ) {
                cursor
                items {
                    id
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
        """

        while cursor:
            page_data = self.query(
                next_query,
                {
                    "cursor": cursor,
                    "limit": min(limit, 500),
                },
            )

            page = page_data.get("next_items_page", {})

            page_items = page.get("items", [])
            all_items.extend(page_items)

            new_cursor = page.get("cursor")

            # Safety check to prevent an accidental infinite loop.
            if not new_cursor or new_cursor == cursor:
                break

            cursor = new_cursor

        board["items_page"]["items"] = all_items

        return board