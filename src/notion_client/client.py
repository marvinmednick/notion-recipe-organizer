"""Notion API client wrapper.

Version: v2
Last updated: Database operations with ID cleaning and validation
"""

import logging
from typing import Dict, List, Optional, Any

from notion_client import Client, APIResponseError, APIErrorCode
from rich.console import Console

from ..config import config

logger = logging.getLogger(__name__)
console = Console()


class NotionClient:
    """Wrapper for Notion API client with error handling and utilities."""

    def __init__(self, token: Optional[str] = None):
        """Initialize Notion client."""
        self.token = token or config.notion_token
        if not self.token:
            raise ValueError("Notion token is required")

        self.client = Client(auth=self.token)

    def _clean_id(self, notion_id: str) -> str:
        """Clean a Notion ID by removing query parameters and formatting consistently.

        Warns if the ID needed cleaning to help users learn the correct format.
        """
        original_id = notion_id

        # Remove everything after ? (view parameters, etc.)
        clean_id = notion_id.split("?")[0]

        # Remove any remaining URL fragments
        clean_id = clean_id.split("#")[0]

        # Check if we had to clean anything
        if clean_id != original_id:
            console.print(
                f"[yellow]⚠️  ID contained extra parameters and was cleaned:[/yellow]"
            )
            console.print(f"   Original: {original_id}")
            console.print(f"   Cleaned:  {clean_id}")
            console.print(
                f"[dim]   Tip: Use just the database ID (before the '?') in your .env file[/dim]"
            )

        # Remove hyphens if present and add them back in standard format
        clean_id = clean_id.replace("-", "")

        # Add hyphens in standard UUID format if it's 32 characters
        if len(clean_id) == 32:
            clean_id = f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"

        return clean_id

    def test_connection(self) -> bool:
        """Test the Notion API connection."""
        try:
            # Try to get user info to test connection
            user = self.client.users.me()
            console.print(
                f"✅ Connected to Notion as: [bold green]{user.get('name', 'Unknown')}[/bold green]"
            )
            return True
        except APIResponseError as e:
            if e.code == APIErrorCode.Unauthorized:
                console.print(
                    f"❌ Authentication Error: [bold red]Invalid or expired token[/bold red]"
                )
            elif e.code == APIErrorCode.RateLimited:
                console.print(
                    f"❌ Rate Limited: [bold red]Too many requests[/bold red]"
                )
            else:
                console.print(
                    f"❌ Notion API Error: [bold red]{e.code} - {e}[/bold red]"
                )
            return False
        except Exception as e:
            console.print(f"❌ Connection Error: [bold red]{e}[/bold red]")
            return False

    def get_page(self, page_id: str) -> Optional[Dict[str, Any]]:
        """Get a single page by ID."""
        try:
            return self.client.pages.retrieve(page_id)
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                logger.error(f"Page {page_id} not found or not shared with integration")
            elif e.code == APIErrorCode.Unauthorized:
                logger.error(f"No permission to access page {page_id}")
            else:
                logger.error(f"Failed to get page {page_id}: {e.code} - {e}")
            return None

    def get_database(self, database_id: str) -> Optional[Dict[str, Any]]:
        """Get database information and schema."""
        try:
            clean_id = self._clean_id(database_id)
            return self.client.databases.retrieve(clean_id)
        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                logger.error(
                    f"Database {database_id} not found or not shared with integration"
                )
            elif e.code == APIErrorCode.Unauthorized:
                logger.error(f"No permission to access database {database_id}")
            else:
                logger.error(f"Failed to get database {database_id}: {e.code} - {e}")
            return None

    def get_database_records(
        self, database_id: str, max_records: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all records from a database."""
        records = []

        try:
            clean_id = self._clean_id(database_id)

            # Query database with pagination
            response = self.client.databases.query(database_id=clean_id)

            for record in response.get("results", []):
                records.append(record)

                # Limit results if specified
                if max_records and len(records) >= max_records:
                    break

            # Handle pagination if there are more results
            while response.get("has_more") and (
                not max_records or len(records) < max_records
            ):
                response = self.client.databases.query(
                    database_id=clean_id, start_cursor=response.get("next_cursor")
                )

                for record in response.get("results", []):
                    records.append(record)

                    if max_records and len(records) >= max_records:
                        break

        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                logger.error(f"Database {database_id} not found or not accessible")
            elif e.code == APIErrorCode.RateLimited:
                logger.error(f"Rate limited while querying database {database_id}")
            else:
                logger.error(f"Failed to query database {database_id}: {e.code} - {e}")

        return records

    def search_pages(
        self, query: str = "", filter_dict: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Search for pages in the workspace."""
        try:
            search_params = {}

            if query:
                search_params["query"] = query

            if filter_dict:
                search_params["filter"] = filter_dict

            response = self.client.search(**search_params)
            return response.get("results", [])

        except APIResponseError as e:
            if e.code == APIErrorCode.ValidationError:
                logger.error(f"Search validation error: {e}")
            else:
                logger.error(f"Search failed: {e.code} - {e}")
            return []

    def get_record_content(self, record_id: str) -> Dict[str, Any]:
        """Get full content of a database record including page content."""
        # Get the record (which is also a page)
        record_info = self.get_page(record_id)
        if not record_info:
            return {}

        # Get page blocks/content
        blocks = self.get_page_children(record_id)

        # Extract properties from the record
        properties = self._extract_record_properties(record_info)

        return {
            "record_info": record_info,
            "blocks": blocks,
            "properties": properties,
            "title": properties.get("Name", "Untitled"),
            "url": properties.get("URL", ""),
            "tags": properties.get("Tags", []),
            "created_time": record_info.get("created_time", ""),
            "last_edited_time": record_info.get("last_edited_time", ""),
        }

    def _extract_record_properties(self, record_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract properties from a database record."""
        properties = record_info.get("properties", {})
        extracted = {}

        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get("type")

            if prop_type == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    extracted[prop_name] = title_array[0].get("plain_text", "")
                else:
                    extracted[prop_name] = ""

            elif prop_type == "url":
                extracted[prop_name] = prop_data.get("url", "")

            elif prop_type == "multi_select":
                tags = prop_data.get("multi_select", [])
                extracted[prop_name] = [tag.get("name", "") for tag in tags]

            elif prop_type == "select":
                select_data = prop_data.get("select")
                if select_data:
                    extracted[prop_name] = select_data.get("name", "")
                else:
                    extracted[prop_name] = ""

            elif prop_type == "created_time":
                extracted[prop_name] = prop_data.get("created_time", "")

            elif prop_type == "last_edited_time":
                extracted[prop_name] = prop_data.get("last_edited_time", "")

            elif prop_type == "rich_text":
                rich_text_array = prop_data.get("rich_text", [])
                if rich_text_array:
                    extracted[prop_name] = rich_text_array[0].get("plain_text", "")
                else:
                    extracted[prop_name] = ""

            else:
                # For any other types, try to extract some reasonable value
                extracted[prop_name] = str(prop_data)

        return extracted

    def get_page_children(
        self, page_id: str, max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all children of a page (for getting page content blocks)."""
        children = []

        try:
            # Get direct children
            response = self.client.blocks.children.list(block_id=page_id)

            for block in response.get("results", []):
                children.append(block)

                # Limit results if specified
                if max_pages and len(children) >= max_pages:
                    break

            # Handle pagination if there are more results
            while response.get("has_more") and (
                not max_pages or len(children) < max_pages
            ):
                response = self.client.blocks.children.list(
                    block_id=page_id, start_cursor=response.get("next_cursor")
                )

                for block in response.get("results", []):
                    children.append(block)

                    if max_pages and len(children) >= max_pages:
                        break

        except APIResponseError as e:
            if e.code == APIErrorCode.ObjectNotFound:
                logger.error(f"Page {page_id} not found or not accessible")
            elif e.code == APIErrorCode.RateLimited:
                logger.error(f"Rate limited while getting children of page {page_id}")
            else:
                logger.error(
                    f"Failed to get children of page {page_id}: {e.code} - {e}"
                )

        return children

    def _extract_title(self, page_info: Dict[str, Any]) -> str:
        """Extract title from page info."""
        properties = page_info.get("properties", {})

        # Look for title property
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    return title_array[0].get("plain_text", "Untitled")

        return "Untitled"

