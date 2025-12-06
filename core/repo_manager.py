import os
import git
from pathlib import Path

# Define the data directory relative to this file
# core/repo_manager.py -> data/
DATA_DIR = Path(__file__).parent.parent / "data"

class RepoManager:
    def __init__(self, data_dir=DATA_DIR):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)

    def get_repo_path(self, repo_name):
        return self.data_dir / repo_name

    def clone_repo(self, url_or_path):
        """
        Clones a git repository from a URL OR imports a local directory.
        Returns the path to the cloned/imported repository.
        """
        # Check if input is a local path
        local_source = Path(url_or_path)
        if local_source.exists() and local_source.is_dir():
            repo_name = local_source.name
            repo_path = self.get_repo_path(repo_name)
            
            if repo_path.exists():
                print(f"Repo {repo_name} already exists at {repo_path}")
                return str(repo_path)
            
            print(f"Importing local repo from {local_source} to {repo_path}...")
            import shutil
            try:
                # Copy directory tree
                shutil.copytree(local_source, repo_path, ignore=shutil.ignore_patterns('.git', '__pycache__'))
                # If we want to keep it as a git repo, we might want .git, but copytree can be slow with big history.
                # For this app, we mostly need code + docs.
                print("Import complete.")
                return str(repo_path)
            except Exception as e:
                print(f"Error importing local repo: {e}")
                raise e

        # Fallback to Git Clone
        repo_name = url_or_path.rstrip("/").split("/")[-1].replace(".git", "")
        repo_path = self.get_repo_path(repo_name)
        
        if repo_path.exists():
            print(f"Repo {repo_name} already exists at {repo_path}")
            return str(repo_path)
            
        print(f"Cloning {url_or_path} to {repo_path}...")
        try:
            git.Repo.clone_from(url_or_path, repo_path)
            print("Clone complete.")
        except git.exc.GitCommandError as e:
            print(f"Error cloning repo: {e}")
            raise e
            
        return str(repo_path)

    def index_docs(self, repo_name):
        """
        Walks the repository and extracts content from .md and .txt files.
        Returns a list of dictionaries containing 'id', 'text', and 'metadata'.
        """
        repo_path = self.get_repo_path(repo_name)
        if not repo_path.exists():
            raise ValueError(f"Repo {repo_name} not found at {repo_path}.")

        documents = []
        
        print(f"Indexing docs in {repo_name}...")
        # Walk for .md and .txt
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file.lower().endswith((".md", ".txt")):
                    full_path = Path(root) / file
                    try:
                        # Use errors='ignore' to avoid crashing on binary/weird files
                        content = full_path.read_text(encoding="utf-8", errors="ignore")
                        if not content.strip():
                            continue
                            
                        # Relative path for ID/Display
                        rel_path = full_path.relative_to(repo_path)
                        
                        documents.append({
                            "id": f"{repo_name}/{rel_path}",
                            "text": content,
                            "metadata": {
                                "source": str(rel_path), 
                                "repo": repo_name,
                                "type": "documentation"
                            }
                        })
                    except Exception as e:
                        print(f"Error reading {full_path}: {e}")
        
        print(f"Found {len(documents)} documents.")
        return documents
