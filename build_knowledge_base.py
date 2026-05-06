# build_knowledge_base.py
import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


def build_rag_db():
    print("1. Loading Markdown files from ./docs...")
    loader = DirectoryLoader(
        './docs',
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()

    if not documents:
        print("❌ No .md files found in ./docs — nothing to index.")
        return

    print(f"2. Splitting {len(documents)} document(s) into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)
    print(f"   → {len(chunks)} chunks created.")

    if not chunks:
        print("❌ All documents were empty — nothing to index. Add content to your ./docs files.")
        return

    print("3. Generating embeddings and saving to local Chroma DB...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./rag_db",
    )
    print(
        f"✅ Knowledge Base built successfully at ./rag_db! ({len(chunks)} chunks indexed)")


if __name__ == "__main__":
    build_rag_db()
