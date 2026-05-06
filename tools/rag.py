import os
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vector_db = Chroma(persist_directory="./rag_db",
                   embedding_function=_embeddings)

_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def index_plan(plan: str, feature_slug: str) -> str:
    """
    Save an approved architectural plan to docs/plans/ and index it live
    into the RAG vector database. Returns the path of the saved file.
    """
    plans_dir = os.path.join("docs", "plans")
    os.makedirs(plans_dir, exist_ok=True)
    filename = f"{feature_slug}.md"
    filepath = os.path.join(plans_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Approved Architecture Plan: {feature_slug}\n\n{plan}\n")

    # Split and add directly to the live vector DB — no rebuild needed
    doc = Document(page_content=plan, metadata={
                   "source": filepath, "type": "approved_plan"})
    chunks = _splitter.split_documents([doc])
    vector_db.add_documents(chunks)

    return filepath


@tool
def search_company_knowledge_base(query: str) -> str:
    """
    Search the company Knowledge Base, Wiki, and Architecture guidelines.
    Use this tool whenever you need to know how the company implements specific features,
    coding patterns, or UI/UX rules.
    """
    print(f"\n🔍 [RAG SEARCH] Agent is looking up: '{query}'")
    results = vector_db.similarity_search(query, k=3)
    if not results:
        return "No relevant guidelines found."
    compiled = "Found the following company guidelines:\n\n"
    for doc in results:
        source = doc.metadata.get("source", "Unknown")
        compiled += f"--- Source: {source} ---\n{doc.page_content}\n\n"
    return compiled
