# Hybrid-version-of-RAG-Simple-and-Agentic-using-MCP
# Git Assist AI

**Git Assist AI** is a powerful, agentic coding assistant that helps you explore, understand, and debug your git repositories. It combines **RAG (Retrieval-Augmented Generation)** for documentation queries with an **Agentic Workflow** (powered by Google Gemini and MCP) for deep code inspection.

## Features

*   **Dual-Mode Routing**: Automatically routes queries to the best strategy:
    *   **Simple Mode (RAG)**: Uses ChromaDB to answer "how-to" and conceptual questions based on documentation.
    *   **Agentic Mode**: Uses a custom **Model Context Protocol (MCP)** tool server to search code, read files, list symbols, and get git blame info for complex tasks like "Where is X defined?" or "Explain this file".
*   **Modern UI**: Built with **Streamlit** for a responsive, web-based chat interface.
*   **Inspector Panel**: 
    *   **Evidence**: Shows the raw documentation chunks retrieved (RAG).
    *   **Trace**: Displays the agent's step-by-step tool execution (Agentic).
    *   **Debug**: Shows internal routing logic and logs.
*   **Repository Management**: Easily clone and switch between local or remote git repositories.

## Architecture

*   **Frontend**: Streamlit (Python)
*   **LLM**: Google Gemini (via `google-genai` SDK)
*   **Vector DB**: ChromaDB
*   **Agent Protocol**: Model Context Protocol (MCP) - Custom FastMCP implementation
*   **Backend Core**:
    *   `Router`: LLM-based intelligent query classification.
    *   `AgenticClient`: Manages the agent loop and MCP connection.
    *   `SimpleRAG`: Handles document indexing and retrieval.
    *   `ToolServer`: Provides file system and git access to the agent.

## Getting Started

### Prerequisites

*   Python 3.10+
*   Git installed on your system.
*   A **Google Gemini API Key** (Get one at [aistudio.google.com](https://aistudio.google.com/)).

### Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd Git_Assist
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment**:
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```

### Running the App

Run the application using the main entry point:

```bash
python main.py
```
*Or directly via Streamlit:*
```bash
streamlit run ui/streamlit_app.py
```

The application will open in your default web browser (usually at `http://localhost:8501`).

## Usage Guide

1.  **Select/Clone a Repo**:
    *   Use the sidebar to **Clone** a new repository by URL.
    *   Select an existing repository from the dropdown.

2.  **Index Documents** (Optional but recommended):
    *   Click "Index Documents" to ingest `.md` and `.txt` files into the vector database. This powers the "Simple" RAG mode.

3.  **Ask Questions**:
    *   **Conceptual**: "What is this project about?", "How do I install it?" -> *Uses RAG*.
    *   **Code Exploration**: "Where is the `Router` class defined?", "Explain `core/agentic_client.py`", "Fix the bug in the main loop" -> *Uses Agentic Tools*.

4.  **Inspect**:
    *   Check the **Trace** tab in the sidebar to see exactly which files the agent read and what tools it called.

## Project Structure & File Details

### Root Directory
*   **`main.py`**: The entry point script. It uses `subprocess` to launch the Streamlit application (`ui/streamlit_app.py`).
*   **`requirements.txt`**: Lists all Python dependencies required to run the project (e.g., `streamlit`, `google-genai`, `mcp`, `chromadb`).
*   **`.env`**: Configuration file for environment variables (stores your `GEMINI_API_KEY`).
*   **`DIAGRAMS.md`**: Contains Mermaid.js diagrams visualizing the system architecture, user flow, class structure, and sequence diagrams.

### `core/` (Backend Logic)
*   **`agentic_client.py`**: The brain of the agentic workflow. It manages the chat history, connects to the `ToolServer` via MCP (stdio), converts MCP tools to Gemini function declarations, and executes the agent loop (Thought -> Action -> Observation).
*   **`llm.py`**: A wrapper around the Google GenAI SDK. It handles API authentication and provides a unified interface for generating content and embeddings.
*   **`repo_manager.py`**: Handles file system operations for repositories. It can clone remote git URLs, import local folders, and walk through files to index documentation.
*   **`router.py`**: An intelligent routing module. It uses an LLM prompt to classify user queries as either "simple" (general/conceptual) or "agentic" (code exploration/debugging).
*   **`simple_rag.py`**: Implements the RAG (Retrieval-Augmented Generation) pipeline using ChromaDB. It handles ingesting document chunks and retrieving relevant context for simple queries.

### `server/` (MCP Tooling)
*   **`tool_server.py`**: A standalone script that runs a FastMCP server. It exposes tools like `search_code`, `read_file_segment`, `list_files`, and `list_symbols` that the agent can call to interact with the file system.

### `ui/` (Frontend)
*   **`streamlit_app.py`**: The main user interface built with Streamlit. It handles:
    *   **Sidebar**: Repo selection, cloning, and inspector tabs (Evidence/Trace/Debug).
    *   **Chat**: Rendering the chat history and handling user input.
    *   **State Management**: Orchestrating the calls to the Router, Agent, and RAG backend.

### `data/`
*   **`repo/`**: Default location where repositories are cloned.
*   **`chroma_db/`**: Persistent storage for the ChromaDB vector embeddings.


## Tech Stack

*   **Language**: Python
*   **Web Framework**: Streamlit
*   **AI Models**: Gemini 1.5 Flash / Pro
*   **Embeddings**: Gemini Text Embedding 004
*   **Tooling**: MCP (Model Context Protocol)
