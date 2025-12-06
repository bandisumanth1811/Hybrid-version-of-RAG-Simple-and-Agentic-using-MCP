import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import queue
import sys
import os
from pathlib import Path

# Add parent dir to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.repo_manager import RepoManager
from core.simple_rag import SimpleRAG
from core.llm import GeminiClient
from core.router import Router
from core.agentic_client import AgenticClient

class GitAssistApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Assist AI")
        self.root.geometry("1200x800")
        
        # Data & Logic
        self.repo_mgr = RepoManager()
        self.rag = SimpleRAG()
        self.llm = GeminiClient()
        self.router = Router()
        self.agentic_client = AgenticClient()
        self.current_repo = tk.StringVar()
        
        # Message Queue for Thread-Safety
        self.msg_queue = queue.Queue()
        
        # UI Layout
        self.setup_ui()
        
        # Start queue listener
        self.root.after(100, self.process_queue)

    def setup_ui(self):
        # Configure Grid Weight
        self.root.columnconfigure(0, weight=1) # Sidebar
        self.root.columnconfigure(1, weight=3) # Chat
        self.root.columnconfigure(2, weight=2) # Inspector
        self.root.rowconfigure(0, weight=1)

        # --- Col 0: Sidebar ---
        self.sidebar = ttk.Frame(self.root, padding=10)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ttk.Label(self.sidebar, text="Repo Manager", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Repo List
        self.repo_combo = ttk.Combobox(self.sidebar)
        self.repo_combo.pack(fill="x", pady=5)
        self.refresh_repo_list()
        
        # URL Entry
        self.url_entry = ttk.Entry(self.sidebar)
        self.url_entry.pack(fill="x", pady=5)
        self.url_entry.insert(0, "https://github.com/...")
        
        # Buttons
        self.btn_clone = ttk.Button(self.sidebar, text="Clone Repo", command=self.on_clone)
        self.btn_clone.pack(fill="x", pady=5)
        
        self.btn_index = ttk.Button(self.sidebar, text="Index Docs", command=self.on_index)
        self.btn_index.pack(fill="x", pady=5)

        self.btn_clear = ttk.Button(self.sidebar, text="Clear Chat", command=self.on_clear)
        self.btn_clear.pack(fill="x", pady=5)
        
        self.lbl_status = ttk.Label(self.sidebar, text="Ready", relief="sunken", anchor="w")
        self.lbl_status.pack(fill="x", side="bottom", pady=10)

        # --- Col 1: Chat Area ---
        self.chat_frame = ttk.Frame(self.root, padding=10)
        self.chat_frame.grid(row=0, column=1, sticky="nsew")
        
        self.chat_display = scrolledtext.ScrolledText(self.chat_frame, state="disabled", font=("Consolas", 10))
        self.chat_display.pack(expand=True, fill="both", pady=(0, 10))
        self.chat_display.tag_config("user", foreground="blue", font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("ai", foreground="black")
        self.chat_display.tag_config("error", foreground="red")
        
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill="x")
        
        self.chat_input = ttk.Entry(input_frame)
        self.chat_input.pack(side="left", expand=True, fill="x", padx=(0, 5))
        self.chat_input.bind("<Return>", lambda e: self.on_send())
        
        self.btn_send = ttk.Button(input_frame, text="Send", command=self.on_send)
        self.btn_send.pack(side="right")

        # --- Col 2: Inspector Panel ---
        self.inspector_frame = ttk.Frame(self.root, padding=10)
        self.inspector_frame.grid(row=0, column=2, sticky="nsew")
        
        self.notebook = ttk.Notebook(self.inspector_frame)
        self.notebook.pack(expand=True, fill="both")
        
        # Tab 1: Evidence
        self.tab_evidence = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_evidence, text="Evidence")
        self.evidence_text = scrolledtext.ScrolledText(self.tab_evidence, font=("Consolas", 9))
        self.evidence_text.pack(expand=True, fill="both")
        
        # Tab 2: MCP Trace
        self.tab_trace = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_trace, text="MCP Trace")
        self.trace_text = scrolledtext.ScrolledText(self.tab_trace, font=("Consolas", 9), bg="#f0f0f0")
        self.trace_text.pack(expand=True, fill="both")
        
        # Tab 3: Debug
        self.tab_debug = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_debug, text="Debug")
        self.debug_text = scrolledtext.ScrolledText(self.tab_debug, font=("Consolas", 9))
        self.debug_text.pack(expand=True, fill="both")

    # --- Logic Methods ---

    def log(self, msg):
        self.msg_queue.put(("status", msg))

    def append_chat(self, sender, text, tag):
        self.msg_queue.put(("chat", (sender, text, tag)))

    def process_queue(self):
        try:
            while True:
                msg_type, content = self.msg_queue.get_nowait()
                if msg_type == "status":
                    self.lbl_status.config(text=content)
                elif msg_type == "chat":
                    sender, text, tag = content
                    self.chat_display.config(state="normal")
                    self.chat_display.insert("end", f"{sender}: {text}\n\n", tag)
                    self.chat_display.see("end")
                    self.chat_display.config(state="disabled")
                elif msg_type == "clear":
                    self.chat_display.config(state="normal")
                    self.chat_display.delete("1.0", "end")
                    self.chat_display.config(state="disabled")
                    
                    self.evidence_text.delete("1.0", "end")
                    self.trace_text.delete("1.0", "end")
                    self.debug_text.delete("1.0", "end")
                elif msg_type == "evidence":
                    self.evidence_text.delete("1.0", "end")
                    self.evidence_text.insert("end", content)
                elif msg_type == "trace":
                    self.trace_text.insert("end", content + "\n")
                    self.trace_text.see("end")
                elif msg_type == "debug":
                    self.debug_text.insert("end", content + "\n")
                    self.debug_text.see("end")
                elif msg_type == "repo_update":
                    self.refresh_repo_list()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def refresh_repo_list(self):
        repos = [d.name for d in self.repo_mgr.data_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        self.repo_combo['values'] = repos
        if repos:
            self.repo_combo.current(0)
            self.current_repo.set(repos[0])
            # Clear history when repo changes
            self.agentic_client.clear_history()

    def on_clone(self):
        url = self.url_entry.get()
        if not url: return
        
        self.log(f"Cloning {url}...")
        threading.Thread(target=self._clone_thread, args=(url,), daemon=True).start()

    def _clone_thread(self, url):
        try:
            self.repo_mgr.clone_repo(url)
            self.log("Clone complete.")
            self.msg_queue.put(("repo_update", None))
        except Exception as e:
            self.log(f"Clone Error: {e}")

    def on_index(self):
        repo = self.repo_combo.get()
        if not repo: return
        
        self.log(f"Indexing {repo}...")
        threading.Thread(target=self._index_thread, args=(repo,), daemon=True).start()

    def on_clear(self):
        self.msg_queue.put(("clear", None))
        self.agentic_client.clear_history()
        self.log("Chat cleared.")

    def _index_thread(self, repo):
        try:
            docs = self.repo_mgr.index_docs(repo)
            self.rag.ingest(docs)
            self.log(f"Indexed {len(docs)} documents.")
        except Exception as e:
            self.log(f"Index Error: {e}")

    def on_send(self):
        query = self.chat_input.get()
        if not query: return
        
        self.chat_input.delete(0, "end")
        self.append_chat("You", query, "user")
        self.log("Thinking...")
        
        repo = self.repo_combo.get()
        threading.Thread(target=self._ask_thread, args=(query, repo), daemon=True).start()

    def _ask_thread(self, query, repo):
        try:
            # 1. Route
            route = self.router.route(query)
            self.msg_queue.put(("debug", f"Query: '{query}' -> Route: {route.upper()}"))
            
            response_text = ""
            
            if route == "agentic":
                # Agentic Path
                if not repo:
                    self.append_chat("System", "Please select a repository first.", "error")
                    return

                repo_path = str(self.repo_mgr.get_repo_path(repo))
                
                def on_agent_log(msg):
                    self.msg_queue.put(("trace", msg))
                    
                response_text = self.agentic_client.ask(query, repo_path, on_log=on_agent_log)
                self.msg_queue.put(("evidence", "Agentic search performed. See Trace tab."))

            else:
                # Simple Path (RAG)
                context = self.rag.retrieve(query, repo_filter=repo if repo else None)
                
                # Show Evidence
                evidence_str = ""
                context_text = ""
                for doc in context:
                    evidence_str += f"File: {doc['id']}\n---\n{doc['text'][:200]}...\n\n"
                    context_text += f"Source: {doc['id']}\nContent: {doc['text']}\n\n"
                
                self.msg_queue.put(("evidence", evidence_str))
                
                if not context_text:
                    self.append_chat("System", "No relevant documentation found.", "error")
                    self.log("Done.")
                    return

                # Ask LLM
                prompt = f"Answer based on:\n{context_text}\n\nQuestion: {query}"
                response_text = self.llm.ask(prompt)
            
            self.append_chat("Git Assist", response_text, "ai")
            self.log("Ready.")
            
        except Exception as e:
            self.append_chat("System", f"Error: {e}", "error")
            self.log("Error.")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitAssistApp(root)
    root.mainloop()
