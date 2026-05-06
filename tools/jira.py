import os
from langchain_core.tools import tool
from config import JIRA_PATH


@tool
def create_jira_ticket(title: str, description: str, project_key: str) -> str:
    """Use this tool to create a Jira ticket for the engineering team."""
    # In reality: requests.post("https://your-domain.atlassian.net/rest/api/3/issue", auth=...)
    print(f"🎫 [JIRA API CALLED] Created ticket: [{project_key}] {title}")

    os.makedirs(JIRA_PATH, exist_ok=True)
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in title)
    filename = f"{project_key}_{safe_title}.md"
    filepath = os.path.join(JIRA_PATH, filename)
    with open(filepath, "w") as f:
        f.write(f"# [{project_key}] {title}\n\n{description}\n")
    print(f"📄 [JIRA FILE] Saved to {filepath}")

    return f"Ticket '{title}' created successfully in project {project_key}."
