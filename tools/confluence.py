import os
from langchain_core.tools import tool
from config import CONFLUENCE_PATH


@tool
def create_confluence_page(title: str, content: str, space_key: str) -> str:
    """Use this tool to create or update a Wiki page in Confluence for the PRD."""
    # In reality: requests.post("https://domain.atlassian.net/wiki/rest/api/content", ...)
    print(
        f"📝 [CONFLUENCE API CALLED] Published PRD Wiki Page: '{title}' in Space: {space_key}")

    os.makedirs(CONFLUENCE_PATH, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
    filename = f"{safe_title}_PRD.md"
    filepath = os.path.join(CONFLUENCE_PATH, filename)
    with open(filepath, "w") as f:
        f.write(f"# {title}\n\n**Space:** {space_key}\n\n{content}\n")
    print(f"📄 [CONFLUENCE FILE] Saved to {filepath}")

    return f"Confluence page '{title}' created successfully."
