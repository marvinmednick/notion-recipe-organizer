"""Notion API utilities for common operations."""

from typing import Dict, Any


def extract_notion_text_content(prop_data: Dict[str, Any], prop_type: str = "rich_text") -> str:
    """Extract text content from any Notion text property.
    
    Args:
        prop_data: Property data from Notion API
        prop_type: Type of property ("rich_text", "title", or "auto" to detect)
        
    Returns:
        Extracted text content as string
    """
    # Handle simple string case
    if isinstance(prop_data, str):
        return prop_data
    
    if not prop_data or not isinstance(prop_data, dict):
        return ""
    
    # Auto-detect property type if not specified
    if prop_type == "auto":
        if "title" in prop_data:
            prop_type = "title"
        elif "rich_text" in prop_data:
            prop_type = "rich_text"
        else:
            return ""
    
    # Get the text array based on property type
    if prop_type == "title" and "title" in prop_data:
        text_array = prop_data["title"]
    elif prop_type == "rich_text" and "rich_text" in prop_data:
        text_array = prop_data["rich_text"]
    else:
        return ""
    
    # Validate array structure
    if not isinstance(text_array, list):
        return ""
    
    # Extract content from text blocks
    content_parts = []
    for text_block in text_array:
        if isinstance(text_block, dict) and "text" in text_block:
            content_parts.append(text_block["text"].get("content", ""))
    
    return "".join(content_parts)


def create_notion_text_property(content: str, prop_type: str = "rich_text") -> Dict[str, Any]:
    """Create a Notion text property structure.
    
    Args:
        content: Text content to wrap
        prop_type: Type of property ("rich_text" or "title")
        
    Returns:
        Property structure for Notion API
    """
    text_block = {"text": {"content": content}}
    
    if prop_type == "title":
        return {"title": [text_block]}
    else:  # rich_text
        return {"rich_text": [text_block]}