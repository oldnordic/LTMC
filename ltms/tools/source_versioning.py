#!/usr/bin/env python3
"""
LTMC Source Code Versioning System
World-class source code version management with rollback, diff, and tracking
"""

import os
import json
import difflib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

class SourceVersionManager:
    """World-class source code versioning system integrated with LTMC memory"""
    
    def __init__(self, memory_action_func):
        """Initialize with LTMC memory action function"""
        self.memory_action = memory_action_func
        self.conversation_id = "source_code_versioning"
        
    async def store_version(self, file_path: str, content: str, version: str = None, 
                          tags: List[str] = None, change_summary: str = None) -> Dict[str, Any]:
        """Store a new version of source code with complete metadata
        
        Args:
            file_path: Path to the source file (e.g., "ltms/tools/core/mcp_base.py")
            content: Full source code content
            version: Version string (e.g., "v1.0.0", auto-incremented if None)
            tags: List of tags (e.g., ["refactor", "performance_fix"])
            change_summary: Summary of what changed
            
        Returns:
            Dictionary with storage results and version metadata
        """
        
        # Auto-increment version if not provided
        if version is None:
            version = await self._get_next_version(file_path)
        
        # Create comprehensive metadata
        version_metadata = {
            "file_path": file_path,
            "version": version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tags": tags or [],
            "change_summary": change_summary or f"Version {version} stored",
            "line_count": len(content.split('\n')),
            "size_bytes": len(content.encode('utf-8')),
            "storage_type": "source_version"
        }
        
        # Create version-specific file name
        version_file_name = f"{file_path}@{version}"
        
        # Store in LTMC memory with version metadata
        result = await self.memory_action(
            action="store",
            file_name=version_file_name,
            content=content,
            session_id="source_versioning",
            conversation_id=self.conversation_id,
            resource_type="source_code",
            context_tags=tags or [] + [f"version_{version}", "source_versioning"]
        )
        
        # Store version index entry for easy listing
        await self._update_version_index(file_path, version, version_metadata)
        
        return {
            "success": result.get("success", False),
            "version": version,
            "version_file_name": version_file_name,
            "metadata": version_metadata,
            "storage_result": result
        }
    
    async def list_versions(self, file_path: str) -> List[Dict[str, Any]]:
        """List all versions of a source file
        
        Args:
            file_path: Path to the source file
            
        Returns:
            List of version metadata dictionaries sorted by version
        """
        
        index_file_name = f"{file_path}@INDEX"
        
        # Retrieve version index
        result = await self.memory_action(
            action="retrieve",
            query=index_file_name,
            conversation_id=self.conversation_id,
            k=1
        )
        
        if result.get("success") and result["data"]["documents"]:
            try:
                index_data = json.loads(result["data"]["documents"][0]["content"])
                return sorted(index_data.get("versions", []), 
                            key=lambda x: x["timestamp"], reverse=True)
            except (json.JSONDecodeError, KeyError):
                return []
        
        return []
    
    async def retrieve_version(self, file_path: str, version: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve a specific version of source code
        
        Args:
            file_path: Path to the source file
            version: Version to retrieve (latest if None)
            
        Returns:
            Dictionary with version content and metadata
        """
        
        if version is None:
            # Get latest version
            versions = await self.list_versions(file_path)
            if not versions:
                return None
            version = versions[0]["version"]
        
        version_file_name = f"{file_path}@{version}"
        
        result = await self.memory_action(
            action="retrieve",
            query=version_file_name,
            conversation_id=self.conversation_id,
            k=1
        )
        
        if result.get("success") and result["data"]["documents"]:
            doc = result["data"]["documents"][0]
            return {
                "version": version,
                "content": doc["content"],
                "file_name": doc["file_name"],
                "created_at": doc.get("created_at"),
                "metadata": self._parse_metadata_from_content(doc["content"])
            }
        
        return None
    
    async def diff_versions(self, file_path: str, version1: str, version2: str) -> Dict[str, Any]:
        """Generate diff between two versions
        
        Args:
            file_path: Path to the source file
            version1: First version (older)
            version2: Second version (newer)
            
        Returns:
            Dictionary with diff information
        """
        
        v1_data = await self.retrieve_version(file_path, version1)
        v2_data = await self.retrieve_version(file_path, version2)
        
        if not v1_data or not v2_data:
            return {"success": False, "error": "One or both versions not found"}
        
        # Generate unified diff
        diff_lines = list(difflib.unified_diff(
            v1_data["content"].splitlines(keepends=True),
            v2_data["content"].splitlines(keepends=True),
            fromfile=f"{file_path}@{version1}",
            tofile=f"{file_path}@{version2}",
            lineterm=""
        ))
        
        # Calculate diff statistics
        added_lines = len([line for line in diff_lines if line.startswith('+')])
        removed_lines = len([line for line in diff_lines if line.startswith('-')])
        
        return {
            "success": True,
            "file_path": file_path,
            "version1": version1,
            "version2": version2,
            "diff": "".join(diff_lines),
            "statistics": {
                "added_lines": added_lines,
                "removed_lines": removed_lines,
                "total_changes": added_lines + removed_lines
            }
        }
    
    async def rollback_to_version(self, file_path: str, target_version: str, 
                                write_to_disk: bool = False) -> Dict[str, Any]:
        """Rollback to a specific version
        
        Args:
            file_path: Path to the source file
            target_version: Version to rollback to
            write_to_disk: Whether to write the rolled-back version to disk
            
        Returns:
            Dictionary with rollback results
        """
        
        # Retrieve target version
        version_data = await self.retrieve_version(file_path, target_version)
        if not version_data:
            return {"success": False, "error": f"Version {target_version} not found"}
        
        result = {
            "success": True,
            "file_path": file_path,
            "target_version": target_version,
            "content": version_data["content"],
            "written_to_disk": False
        }
        
        # Optionally write to disk
        if write_to_disk:
            try:
                # Ensure directory exists
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                
                # Write content to file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(version_data["content"])
                
                result["written_to_disk"] = True
                result["disk_path"] = os.path.abspath(file_path)
                
            except Exception as e:
                result["disk_write_error"] = str(e)
        
        return result
    
    async def _get_next_version(self, file_path: str) -> str:
        """Get next version number for a file"""
        versions = await self.list_versions(file_path)
        
        if not versions:
            return "v1.0.0"
        
        # Parse latest version and increment
        latest_version = versions[0]["version"]
        if latest_version.startswith('v'):
            try:
                major, minor, patch = map(int, latest_version[1:].split('.'))
                return f"v{major}.{minor}.{patch + 1}"
            except ValueError:
                pass
        
        # Fallback to timestamp-based versioning
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"
    
    async def _update_version_index(self, file_path: str, version: str, metadata: Dict[str, Any]):
        """Update the version index for a file"""
        index_file_name = f"{file_path}@INDEX"
        
        # Get existing index
        result = await self.memory_action(
            action="retrieve",
            query=index_file_name,
            conversation_id=self.conversation_id,
            k=1
        )
        
        # Parse existing index or create new
        if result.get("success") and result["data"]["documents"]:
            try:
                index_data = json.loads(result["data"]["documents"][0]["content"])
            except json.JSONDecodeError:
                index_data = {"file_path": file_path, "versions": []}
        else:
            index_data = {"file_path": file_path, "versions": []}
        
        # Add new version to index
        index_data["versions"].append(metadata)
        index_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # Store updated index
        await self.memory_action(
            action="store",
            file_name=index_file_name,
            content=json.dumps(index_data, indent=2),
            session_id="source_versioning",
            conversation_id=self.conversation_id,
            resource_type="version_index",
            context_tags=["version_index", "source_versioning"]
        )
    
    def _parse_metadata_from_content(self, content: str) -> Dict[str, Any]:
        """Extract metadata from stored content"""
        lines = content.split('\n')
        metadata = {}
        
        # Look for metadata in comments at the top
        for line in lines[:10]:  # Check first 10 lines
            if 'Version:' in line or 'Lines:' in line or 'Purpose:' in line:
                try:
                    key, value = line.split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
                except ValueError:
                    continue
        
        return metadata


# Example usage and testing functions
async def demo_source_versioning_workflow():
    """Demonstrate the complete source versioning workflow"""
    from ltms.tools.memory.memory_actions import memory_action
    
    # Initialize version manager
    vm = SourceVersionManager(memory_action)
    
    # Test file path and content
    test_file = "demo_example.py"
    
    # Version 1.0.0
    v1_content = '''#!/usr/bin/env python3
"""
Demo Example - Version 1.0.0
Basic implementation
"""

def hello():
    return "Hello World v1.0.0"

if __name__ == "__main__":
    print(hello())
'''
    
    # Store version 1.0.0
    print("🔄 Storing version 1.0.0...")
    result = await vm.store_version(
        test_file, v1_content, "v1.0.0",
        tags=["initial", "demo"],
        change_summary="Initial implementation"
    )
    print(f"✅ Version 1.0.0 stored: {result['success']}")
    
    # Version 1.1.0 - Enhanced
    v2_content = '''#!/usr/bin/env python3
"""
Demo Example - Version 1.1.0
Enhanced implementation with greeting customization
"""

def hello(name="World"):
    return f"Hello {name} v1.1.0"

def goodbye(name="World"):
    return f"Goodbye {name}!"

if __name__ == "__main__":
    print(hello())
    print(goodbye())
'''
    
    # Store version 1.1.0
    print("🔄 Storing version 1.1.0...")
    result = await vm.store_version(
        test_file, v2_content, "v1.1.0",
        tags=["enhancement", "demo"],
        change_summary="Added greeting customization and goodbye function"
    )
    print(f"✅ Version 1.1.0 stored: {result['success']}")
    
    # List all versions
    print("📋 Listing all versions...")
    versions = await vm.list_versions(test_file)
    for v in versions:
        print(f"   {v['version']} - {v['change_summary']}")
    
    # Generate diff
    print("🔍 Generating diff between v1.0.0 and v1.1.0...")
    diff_result = await vm.diff_versions(test_file, "v1.0.0", "v1.1.0")
    if diff_result["success"]:
        print(f"   Changes: +{diff_result['statistics']['added_lines']} -{diff_result['statistics']['removed_lines']}")
        print("   Diff preview:")
        print("   " + "\n   ".join(diff_result["diff"].split('\n')[:10]))
    
    # Test rollback
    print("⏪ Testing rollback to v1.0.0...")
    rollback_result = await vm.rollback_to_version(test_file, "v1.0.0")
    if rollback_result["success"]:
        print(f"✅ Rollback successful - content length: {len(rollback_result['content'])}")
    
    return True


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_source_versioning_workflow())