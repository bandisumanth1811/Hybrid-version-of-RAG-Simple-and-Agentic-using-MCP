from mcp.server.fastmcp import FastMCP
import os
from pathlib import Path
import git

# Create the FastMCP server
mcp = FastMCP("git_assist_tools")

@mcp.tool()
def search_code(repo_path: str, query: str) -> str:
    """
    Searches for a text query in the code files of a repository.
    Returns top 20 matching lines with context.
    """
    results = []
    repo_path_obj = Path(repo_path)
    
    if not repo_path_obj.exists():
        return f"Error: Path {repo_path} does not exist."

    count = 0
    MAX_RESULTS = 20
    
    # Walk through files
    for root, _, files in os.walk(repo_path_obj):
        for file in files:
            # Skip .git and other hidden files
            if ".git" in root:
                continue
                
            file_path = Path(root) / file
            rel_path = file_path.relative_to(repo_path_obj)
            
            # Check if filename matches query
            if query.lower() in file.lower():
                results.append(f"{rel_path}:[FILENAME MATCH]: {file}")
                count += 1
                if count >= MAX_RESULTS:
                    break
            
            try:
                # Read file safely
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                for i, line in enumerate(lines):
                    if query in line:
                        # Return relative path
                        rel_path = file_path.relative_to(repo_path_obj)
                        results.append(f"{rel_path}:{i+1}: {line.strip()}")
                        count += 1
                        if count >= MAX_RESULTS:
                            break
            except Exception:
                continue
        
        if count >= MAX_RESULTS:
            break
            
    if not results:
        return "No matches found."
        
    return "\n".join(results)

@mcp.tool()
def read_file_segment(repo_path: str, file_path: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    Reads a segment of a file. Line numbers are 1-based.
    If end_line is -1, reads to the end.
    """
    # Handle both absolute and relative paths
    # If file_path is relative, join it with repo_path
    path_obj = Path(file_path)
    if not path_obj.is_absolute():
        path = Path(repo_path) / file_path
    else:
        path = path_obj
        
    if not path.exists():
        return f"Error: File {file_path} not found at {path}."
        
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        # Adjust for 0-based index
        start_idx = max(0, start_line - 1)
        if end_line == -1:
            end_idx = len(lines)
        else:
            end_idx = min(len(lines), end_line)
            
        segment = lines[start_idx:end_idx]
        return "".join(segment)
    except Exception as e:
        return f"Error reading file: {e}"

@mcp.tool()
def list_files(repo_path: str, relative_path: str = ".") -> str:
    """
    Lists all files and directories in the given directory (non-recursive).
    relative_path is relative to the repo root.
    """
    path = Path(repo_path) / relative_path
    if not path.exists():
        return f"Error: Path {path} does not exist."
    
    if not path.is_dir():
        return f"Error: {relative_path} is not a directory."
        
    try:
        items = []
        for item in path.iterdir():
            # Skip hidden files/dirs like .git
            if item.name.startswith('.'):
                continue
                
            type_str = "DIR " if item.is_dir() else "FILE"
            items.append(f"[{type_str}] {item.name}")
            
        # Sort: directories first, then files
        items.sort(key=lambda x: (x.startswith("[FILE]"), x.lower()))
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

import re

@mcp.tool()
def list_symbols(repo_path: str, file_path: str) -> str:
    """
    Lists functions and classes defined in the file using regex patterns.
    Supports Python, JavaScript, TypeScript, Java, C++, etc.
    """
    path_obj = Path(file_path)
    if not path_obj.is_absolute():
        path = Path(repo_path) / file_path
    else:
        path = path_obj
        
    if not path.exists():
        return f"Error: File {file_path} not found at {path}."
        
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        ext = path.suffix.lower()
        symbols = []
        
        # Python Patterns
        if ext == ".py":
            # Match "class ClassName" or "def func_name"
            patterns = [
                (r'^class\s+(\w+)', "Class"),
                (r'^def\s+(\w+)', "Function")
            ]
            
            for line in content.splitlines():
                line = line.strip()
                for pattern, type_label in patterns:
                    match = re.search(pattern, line)
                    if match:
                        symbols.append(f"[{type_label}] {match.group(1)}")
                        
        # JS/TS/Java/C++ Patterns
        elif ext in [".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".cs"]:
            # Match "class ClassName", "function funcName", "const func = () =>"
            # This is basic regex, won't catch everything but covers 80%
            
            # 1. Classes
            class_matches = re.finditer(r'class\s+(\w+)', content)
            for m in class_matches:
                symbols.append(f"[Class] {m.group(1)}")
                
            # 2. Functions (traditional)
            func_matches = re.finditer(r'function\s+(\w+)', content)
            for m in func_matches:
                symbols.append(f"[Function] {m.group(1)}")
                
            # 3. Arrow/Const functions (JS/TS) -> const myFunc = ...
            # Look for "const|let|var name = ... =>" or "... function("
            arrow_matches = re.finditer(r'(const|let|var)\s+(\w+)\s*=\s*[(\w]', content)
            for m in arrow_matches:
                # Heuristic: Assume it's a function/variable definition
                symbols.append(f"[Variable/Function] {m.group(2)}")
                
            # 4. Methods in classes (public foo() {}) - simplified
            # This is hard with regex, skipping for simplicity to avoid noise
            
        else:
            return "Unsupported file type for symbol navigation."
            
        if not symbols:
            return "No symbols found (or file type not fully supported)."
            
        return "\n".join(symbols)

    except Exception as e:
        return f"Error parsing symbols: {e}"

@mcp.tool()
def get_git_blame(repo_path: str, relative_file_path: str, line_number: int) -> str:
    """
    Gets git blame information for a specific line in a file.
    """
    try:
        repo = git.Repo(repo_path)
        # Blame returns a list of [commit, list of lines]
        # We need to handle the complex return type of repo.blame
        # Easier way: use git command directly via gitpython
        val = repo.git.blame("-L", f"{line_number},{line_number}", relative_file_path)
        return val
    except Exception as e:
        return f"Error getting blame: {e}"

if __name__ == "__main__":
    # Start the server on stdio
    mcp.run()
