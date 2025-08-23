"""Unix group tools - modern Unix tool implementations.

Provides access to modern Unix tools through the canonical group:operation interface.
Each tool is implemented as a real subprocess call with structured output.
"""

import subprocess
import json
import shutil
from typing import Dict, Any, List, Optional


def unix_grep(pattern: str, path: str = ".", recursive: bool = True, case_sensitive: bool = False, max_results: int = 100) -> Dict[str, Any]:
    """Modern grep using ripgrep (rg) - fast, intuitive grep alternative."""
    try:
        # Check if ripgrep is available
        if not shutil.which("rg"):
            return {"success": False, "error": "ripgrep (rg) not installed", "tool": "rg"}
        
        cmd = ["rg"]
        if not case_sensitive:
            cmd.append("-i")
        if not recursive:
            cmd.append("--max-depth=1")
        cmd.extend(["--json", "--max-count", str(max_results)])
        cmd.extend([pattern, path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        matches = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    match_data = json.loads(line)
                    if match_data.get('type') == 'match':
                        # Extract submatch text safely
                        submatch_texts = []
                        for sub in match_data['data']['submatches']:
                            if 'match' in sub and 'text' in sub['match']:
                                submatch_texts.append(sub['match']['text'])
                        
                        matches.append({
                            'file': match_data['data']['path']['text'],
                            'line_number': match_data['data']['line_number'],
                            'line_text': match_data['data']['lines']['text'].strip(),
                            'match_text': ''.join(submatch_texts)
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    continue
        
        return {
            "success": True,
            "tool": "ripgrep",
            "pattern": pattern,
            "path": path,
            "matches": matches,
            "total_matches": len(matches),
            "stderr": result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "rg"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "rg"}


def unix_find(pattern: str = "*", path: str = ".", file_type: str = "all", max_depth: int = 10) -> Dict[str, Any]:
    """Modern find using fd - simpler, faster find replacement."""
    try:
        # Check if fd is available
        if not shutil.which("fd"):
            return {"success": False, "error": "fd not installed", "tool": "fd"}
        
        cmd = ["fd"]
        if file_type == "file":
            cmd.append("-t=f")
        elif file_type == "directory":
            cmd.append("-t=d")
        
        cmd.extend(["--max-depth", str(max_depth)])
        
        # Use --glob for patterns with wildcards, otherwise treat as regex
        if '*' in pattern or '?' in pattern or '[' in pattern:
            cmd.extend(["--glob", pattern, path])
        else:
            cmd.extend([pattern, path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            return {
                "success": True,
                "tool": "fd",
                "pattern": pattern,
                "path": path,
                "files": files,
                "total_found": len(files),
                "stderr": result.stderr
            }
        else:
            return {"success": False, "error": result.stderr, "tool": "fd"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "fd"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "fd"}


def unix_cat(file_path: str, line_numbers: bool = True, syntax_highlight: bool = True) -> Dict[str, Any]:
    """Modern cat using bat - syntax-highlighted cat with Git integration."""
    try:
        # Check if bat is available
        if not shutil.which("bat"):
            return {"success": False, "error": "bat not installed", "tool": "bat"}
        
        cmd = ["bat"]
        if line_numbers:
            cmd.append("-n")
        if not syntax_highlight:
            cmd.append("--plain")
        cmd.append(file_path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                "success": True,
                "tool": "bat",
                "file_path": file_path,
                "content": result.stdout,
                "line_count": len(result.stdout.split('\n')) - 1,
                "stderr": result.stderr
            }
        else:
            return {"success": False, "error": result.stderr, "tool": "bat"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "bat"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "bat"}


def unix_ls(path: str = ".", show_hidden: bool = False, tree_view: bool = False, details: bool = True) -> Dict[str, Any]:
    """Modern ls using exa - modern replacement for ls with color and tree views."""
    try:
        # Check if exa is available
        if not shutil.which("exa"):
            return {"success": False, "error": "exa not installed", "tool": "exa"}
        
        cmd = ["exa"]
        if show_hidden:
            cmd.append("-a")
        if tree_view:
            cmd.append("--tree")
        if details:
            cmd.append("-l")
        cmd.append(path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return {
                "success": True,
                "tool": "exa",
                "path": path,
                "output": result.stdout,
                "entries": lines,
                "total_entries": len(lines),
                "stderr": result.stderr
            }
        else:
            return {"success": False, "error": result.stderr, "tool": "exa"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "exa"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "exa"}


def unix_fuzzy_find(query: str = "", path: str = ".", preview: bool = True) -> Dict[str, Any]:
    """Fuzzy finder using fzf - blazing-fast, general-purpose fuzzy finder."""
    try:
        # Check if fzf is available
        if not shutil.which("fzf"):
            return {"success": False, "error": "fzf not installed", "tool": "fzf"}
        
        # First get the list of files using fd or find
        if shutil.which("fd"):
            files_cmd = ["fd", ".", path]
        else:
            files_cmd = ["find", path, "-type", "f"]
        
        files_result = subprocess.run(files_cmd, capture_output=True, text=True, timeout=10)
        
        if files_result.returncode != 0:
            return {"success": False, "error": "Failed to list files", "tool": "fzf"}
        
        cmd = ["fzf", "--filter", query] if query else ["fzf", "--print-query"]
        if preview:
            cmd.extend(["--preview", "head -20 {}"])
        
        result = subprocess.run(cmd, input=files_result.stdout, capture_output=True, text=True, timeout=30)
        
        matches = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        
        return {
            "success": True,
            "tool": "fzf",
            "query": query,
            "path": path,
            "matches": matches,
            "total_matches": len(matches)
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "fzf"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "fzf"}


def unix_diff_highlighted(file1: str, file2: str, context_lines: int = 3) -> Dict[str, Any]:
    """Pretty highlighted diff using delta - more readable git diff."""
    try:
        # Check if delta is available
        if not shutil.which("delta"):
            return {"success": False, "error": "delta not installed", "tool": "delta"}
        
        # First create diff
        diff_cmd = ["diff", f"-U{context_lines}", file1, file2]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True)
        
        if not diff_result.stdout:
            return {
                "success": True,
                "tool": "delta",
                "file1": file1,
                "file2": file2,
                "diff": "Files are identical",
                "changes": 0
            }
        
        # Pipe through delta for highlighting
        delta_cmd = ["delta"]
        result = subprocess.run(delta_cmd, input=diff_result.stdout, capture_output=True, text=True, timeout=30)
        
        return {
            "success": True,
            "tool": "delta",
            "file1": file1,
            "file2": file2,
            "diff": result.stdout,
            "changes": diff_result.stdout.count('\n'),
            "stderr": result.stderr
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "delta"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "delta"}


def unix_cheatsheet(command: str, platform: str = "linux") -> Dict[str, Any]:
    """Quick cheat sheets using tldr - quick cheat sheets for common commands."""
    try:
        # Check if tldr is available
        if not shutil.which("tldr"):
            return {"success": False, "error": "tldr not installed", "tool": "tldr"}
        
        cmd = ["tldr", command]
        if platform != "linux":
            cmd.extend(["-p", platform])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                "success": True,
                "tool": "tldr",
                "command": command,
                "platform": platform,
                "cheatsheet": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {"success": False, "error": result.stderr or f"No cheatsheet found for '{command}'", "tool": "tldr"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "tldr"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "tldr"}


def unix_watch(command: str, path: str = ".", timeout: int = 10) -> Dict[str, Any]:
    """Run command when files change using entr - run commands when files change."""
    try:
        # Check if entr is available
        if not shutil.which("entr"):
            return {"success": False, "error": "entr not installed", "tool": "entr"}
        
        # For safety, we'll just show what would be watched rather than actually watching
        # Real watching would be interactive and not suitable for MCP
        
        # Get list of files to watch
        if shutil.which("fd"):
            files_cmd = ["fd", ".", path]
        else:
            files_cmd = ["find", path, "-type", "f"]
        
        files_result = subprocess.run(files_cmd, capture_output=True, text=True, timeout=5)
        
        if files_result.returncode != 0:
            return {"success": False, "error": "Failed to list files to watch", "tool": "entr"}
        
        files = [f.strip() for f in files_result.stdout.strip().split('\n') if f.strip()]
        
        return {
            "success": True,
            "tool": "entr", 
            "command": command,
            "path": path,
            "files_to_watch": files[:20],  # Show first 20 files
            "total_files": len(files),
            "message": f"Would monitor {len(files)} files and run '{command}' on changes",
            "note": "This is a preview mode - entr requires interactive session for actual monitoring"
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "entr"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "entr"}


def unix_http(url: str, method: str = "GET", headers: Dict[str, str] = None, data: str = None, json_data: bool = True) -> Dict[str, Any]:
    """HTTP requests using httpie - readable curl alternative for API calls."""
    try:
        # Check if httpie is available
        if not shutil.which("http"):
            return {"success": False, "error": "httpie (http) not installed", "tool": "httpie"}
        
        cmd = ["http", method, url]
        
        if headers:
            for key, value in headers.items():
                cmd.append(f"{key}:{value}")
        
        if data:
            if json_data:
                cmd.extend(["--json"])
                # Parse data as JSON key:value pairs
                try:
                    data_dict = json.loads(data)
                    for key, value in data_dict.items():
                        cmd.append(f"{key}={value}")
                except json.JSONDecodeError:
                    cmd.append(f"data={data}")
            else:
                cmd.extend(["--form", f"data={data}"])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        # Parse response
        response_parts = result.stdout.split('\n\n', 1)
        headers_part = response_parts[0] if response_parts else ""
        body_part = response_parts[1] if len(response_parts) > 1 else ""
        
        return {
            "success": True,
            "tool": "httpie",
            "method": method,
            "url": url,
            "status_code": result.returncode,
            "response_headers": headers_part,
            "response_body": body_part,
            "stderr": result.stderr
        }
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out", "tool": "httpie"}
    except Exception as e:
        return {"success": False, "error": str(e), "tool": "httpie"}


# Tool registry with group:operation names
UNIX_GROUP_TOOLS = {
    "unix:grep": {
        "handler": unix_grep,
        "description": "Fast search using ripgrep - intuitive grep alternative",
        "schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Pattern to search for"
                },
                "path": {
                    "type": "string", 
                    "description": "Path to search in",
                    "default": "."
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Search recursively",
                    "default": True
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Case sensitive search",
                    "default": False
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 100
                }
            },
            "required": ["pattern"]
        }
    },
    
    "unix:find": {
        "handler": unix_find,
        "description": "Find files using fd - simpler, faster find replacement",
        "schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Pattern to search for",
                    "default": "*"
                },
                "path": {
                    "type": "string",
                    "description": "Path to search in", 
                    "default": "."
                },
                "file_type": {
                    "type": "string",
                    "description": "Type of files to find",
                    "enum": ["all", "file", "directory"],
                    "default": "all"
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Maximum search depth",
                    "default": 10
                }
            }
        }
    },
    
    "unix:cat": {
        "handler": unix_cat,
        "description": "View files using bat - syntax-highlighted cat with Git integration",
        "schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file to display"
                },
                "line_numbers": {
                    "type": "boolean",
                    "description": "Show line numbers",
                    "default": True
                },
                "syntax_highlight": {
                    "type": "boolean", 
                    "description": "Enable syntax highlighting",
                    "default": True
                }
            },
            "required": ["file_path"]
        }
    },
    
    "unix:ls": {
        "handler": unix_ls,
        "description": "List files using exa - modern ls with color and tree views",
        "schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to list",
                    "default": "."
                },
                "show_hidden": {
                    "type": "boolean",
                    "description": "Show hidden files",
                    "default": False
                },
                "tree_view": {
                    "type": "boolean",
                    "description": "Show as tree",
                    "default": False
                },
                "details": {
                    "type": "boolean",
                    "description": "Show detailed info",
                    "default": True
                }
            }
        }
    },
    
    "unix:fuzzy_find": {
        "handler": unix_fuzzy_find,
        "description": "Fuzzy file finder using fzf - blazing-fast fuzzy finder",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query to search for",
                    "default": ""
                },
                "path": {
                    "type": "string",
                    "description": "Path to search in",
                    "default": "."
                },
                "preview": {
                    "type": "boolean",
                    "description": "Enable preview",
                    "default": True
                }
            }
        }
    },
    
    "unix:diff_highlighted": {
        "handler": unix_diff_highlighted,
        "description": "Pretty diff using delta - highlighted git diff",
        "schema": {
            "type": "object",
            "properties": {
                "file1": {
                    "type": "string",
                    "description": "First file to compare"
                },
                "file2": {
                    "type": "string", 
                    "description": "Second file to compare"
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines",
                    "default": 3
                }
            },
            "required": ["file1", "file2"]
        }
    },
    
    "unix:cheatsheet": {
        "handler": unix_cheatsheet,
        "description": "Command cheat sheets using tldr - quick reference for commands",
        "schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to get cheat sheet for"
                },
                "platform": {
                    "type": "string",
                    "description": "Target platform",
                    "enum": ["linux", "osx", "windows", "sunos"],
                    "default": "linux"
                }
            },
            "required": ["command"]
        }
    },
    
    "unix:watch": {
        "handler": unix_watch,
        "description": "Watch files for changes using entr - run commands when files change",
        "schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command to run when files change"
                },
                "path": {
                    "type": "string",
                    "description": "Path to watch",
                    "default": "."
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds", 
                    "default": 10
                }
            },
            "required": ["command"]
        }
    },
    
    "unix:http": {
        "handler": unix_http,
        "description": "HTTP requests using httpie - readable curl alternative",
        "schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to request"
                },
                "method": {
                    "type": "string",
                    "description": "HTTP method",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers",
                    "additionalProperties": {"type": "string"}
                },
                "data": {
                    "type": "string",
                    "description": "Request data (JSON string)"
                },
                "json_data": {
                    "type": "boolean",
                    "description": "Send as JSON",
                    "default": True
                }
            },
            "required": ["url"]
        }
    }
}