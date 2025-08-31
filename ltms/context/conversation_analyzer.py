"""
LTMC Conversation Analysis Engine for Lean JSON Compaction
Analyzes conversations to extract key decisions, technical changes, and active tasks.

File: ltms/context/conversation_analyzer.py
Lines: ~290 (under 300 limit)
Purpose: Extract essential context elements for lean JSON compaction
"""
import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class KeyDecision:
    """Represents a key decision made during conversation."""
    decision_id: str
    timestamp: str
    summary: str
    impact: str  # "high", "medium", "low"
    implementation_status: str  # "completed", "pending", "failed"

@dataclass
class TechnicalChange:
    """Represents a technical change made to files."""
    change_id: str
    files_modified: List[str]
    change_type: str  # "fix", "feature", "refactor"
    description: str
    validation_status: str  # "tested", "untested", "failed"

@dataclass
class ActiveTask:
    """Represents an active task or todo item."""
    task_id: str
    description: str
    status: str  # "in_progress", "pending", "blocked"
    dependencies: List[str]

@dataclass
class ContextPreservation:
    """Critical context elements to preserve."""
    critical_code_sections: List[str]  # "file:line_range"
    key_concepts: List[str]
    user_preferences: Dict[str, str]

@dataclass
class SessionMetadata:
    """Metadata about the conversation session."""
    start_time: str
    end_time: str
    message_count: int
    compaction_trigger: str  # "auto" | "manual"

class ConversationAnalyzer:
    """
    Analyzes conversation transcripts to extract essential elements for lean JSON compaction.
    Designed to work with existing LTMC precompact hook without breaking functionality.
    """
    
    def __init__(self):
        # Pattern matchers for different types of content
        self.decision_patterns = [
            r"(?i)(decided?|concluded?|agreed?|chose|selected).*",
            r"(?i)(let's|we'll|i'll).*",
            r"(?i)(the solution|the approach|the fix).*",
            r"(?i)(remove|add|implement|fix|change).*"
        ]
        
        self.file_modification_patterns = [
            r"(?i)(modified?|edited?|changed?|updated?|created?)\s+.*?\.(py|js|ts|md|json|yml|yaml|txt|sh)",
            r"(?i)(file:?\s*)?([a-zA-Z0-9_/.-]+\.(py|js|ts|md|json|yml|yaml|txt|sh))",
            r"(?i)line[s]?\s+\d+",
        ]
        
        self.task_patterns = [
            r"(?i)(todo|task|need to|should|must|next step).*",
            r"(?i)(pending|in.progress|blocked|waiting).*",
            r"(?i)(implement|build|create|fix|test).*",
        ]
        
        self.technical_indicators = [
            "function", "class", "method", "variable", "import", "export",
            "database", "API", "endpoint", "service", "component",
            "test", "error", "exception", "bug", "fix"
        ]

    def analyze_conversation(self, transcript_data: Any, session_id: str, trigger: str) -> Dict[str, Any]:
        """
        Analyze conversation transcript and generate lean JSON summary.
        
        Args:
            transcript_data: Raw transcript data from Claude Code
            session_id: Session identifier
            trigger: Compaction trigger type
            
        Returns:
            Lean JSON structure with essential context elements
        """
        try:
            logger.info(f"Starting conversation analysis for session {session_id}")
            
            # Extract messages from transcript
            messages = self._extract_messages(transcript_data)
            
            # Analyze different aspects
            decisions = self._extract_key_decisions(messages)
            changes = self._extract_technical_changes(messages)
            tasks = self._extract_active_tasks(messages)
            context = self._extract_context_preservation(messages)
            metadata = self._generate_session_metadata(messages, trigger)
            
            # Build lean JSON structure
            lean_summary = {
                "conversation_id": session_id,
                "session_metadata": asdict(metadata),
                "key_decisions": [asdict(d) for d in decisions],
                "technical_changes": [asdict(c) for c in changes],
                "active_tasks": [asdict(t) for t in tasks],
                "context_preservation": asdict(context)
            }
            
            # Calculate compression ratio
            original_size = len(json.dumps(transcript_data))
            compressed_size = len(json.dumps(lean_summary))
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            logger.info(f"Analysis complete: {compression_ratio:.1f}% compression achieved")
            logger.info(f"Extracted: {len(decisions)} decisions, {len(changes)} changes, {len(tasks)} tasks")
            
            return lean_summary
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return self._create_fallback_summary(session_id, trigger)

    def _extract_messages(self, transcript_data: Any) -> List[Dict[str, Any]]:
        """Extract structured messages from raw transcript data."""
        messages = []
        
        try:
            if isinstance(transcript_data, list):
                for entry in transcript_data:
                    if isinstance(entry, dict) and 'role' in entry and 'content' in entry:
                        messages.append({
                            'role': entry['role'],
                            'content': self._extract_text_content(entry['content']),
                            'timestamp': entry.get('timestamp', datetime.now().isoformat())
                        })
            elif isinstance(transcript_data, dict) and 'messages' in transcript_data:
                for msg in transcript_data['messages']:
                    if 'role' in msg and 'content' in msg:
                        messages.append({
                            'role': msg['role'],
                            'content': self._extract_text_content(msg['content']),
                            'timestamp': msg.get('timestamp', datetime.now().isoformat())
                        })
                        
        except Exception as e:
            logger.warning(f"Error extracting messages: {e}")
            
        return messages

    def _extract_text_content(self, content: Any) -> str:
        """Extract plain text from complex content structures."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and 'text' in part:
                    text_parts.append(part['text'])
                elif isinstance(part, str):
                    text_parts.append(part)
            return '\n'.join(text_parts)
        else:
            return str(content)

    def _extract_key_decisions(self, messages: List[Dict[str, Any]]) -> List[KeyDecision]:
        """Extract key decisions from conversation messages."""
        decisions = []
        decision_counter = 1
        
        for msg in messages:
            if msg['role'] == 'user':  # Focus on user decisions
                content = msg['content']
                
                # Check for decision indicators
                for pattern in self.decision_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        decision = KeyDecision(
                            decision_id=f"decision_{decision_counter:03d}",
                            timestamp=msg['timestamp'],
                            summary=self._summarize_text(content, 100),
                            impact=self._assess_impact(content),
                            implementation_status=self._assess_status(content)
                        )
                        decisions.append(decision)
                        decision_counter += 1
                        break  # One decision per message
                        
        return decisions[:10]  # Limit to top 10 decisions

    def _extract_technical_changes(self, messages: List[Dict[str, Any]]) -> List[TechnicalChange]:
        """Extract technical changes and file modifications."""
        changes = []
        change_counter = 1
        
        for msg in messages:
            content = msg['content']
            
            # Look for file modifications
            files_mentioned = []
            for pattern in self.file_modification_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        files_mentioned.extend([m for m in match if '.' in m])
                    elif '.' in match:
                        files_mentioned.append(match)
            
            if files_mentioned:
                change = TechnicalChange(
                    change_id=f"change_{change_counter:03d}",
                    files_modified=list(set(files_mentioned))[:5],  # Limit to 5 files
                    change_type=self._classify_change_type(content),
                    description=self._summarize_text(content, 150),
                    validation_status=self._assess_validation_status(content)
                )
                changes.append(change)
                change_counter += 1
                
        return changes[:15]  # Limit to top 15 changes

    def _extract_active_tasks(self, messages: List[Dict[str, Any]]) -> List[ActiveTask]:
        """Extract active tasks and todo items."""
        tasks = []
        task_counter = 1
        
        for msg in messages:
            content = msg['content']
            
            # Look for task indicators
            for pattern in self.task_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    task = ActiveTask(
                        task_id=f"task_{task_counter:03d}",
                        description=self._summarize_text(content, 80),
                        status=self._assess_task_status(content),
                        dependencies=[]  # Could be enhanced to detect dependencies
                    )
                    tasks.append(task)
                    task_counter += 1
                    break
                    
        return tasks[:8]  # Limit to top 8 tasks

    def _extract_context_preservation(self, messages: List[Dict[str, Any]]) -> ContextPreservation:
        """Extract critical context elements to preserve."""
        code_sections = []
        key_concepts = []
        preferences = {}
        
        for msg in messages:
            content = msg['content']
            
            # Extract code sections (file:line patterns)
            code_matches = re.findall(r"([a-zA-Z0-9_/.-]+\.(py|js|ts)):\s*(\d+)", content)
            for match in code_matches:
                code_sections.append(f"{match[0]}:{match[2]}")
            
            # Extract key technical concepts
            for indicator in self.technical_indicators:
                if indicator in content.lower():
                    key_concepts.append(indicator)
                    
        return ContextPreservation(
            critical_code_sections=list(set(code_sections))[:10],
            key_concepts=list(set(key_concepts))[:15],
            user_preferences=preferences  # Could be enhanced
        )

    def _generate_session_metadata(self, messages: List[Dict[str, Any]], trigger: str) -> SessionMetadata:
        """Generate session metadata."""
        if not messages:
            now = datetime.now().isoformat()
            return SessionMetadata(now, now, 0, trigger)
            
        start_time = messages[0]['timestamp'] if messages else datetime.now().isoformat()
        end_time = messages[-1]['timestamp'] if messages else datetime.now().isoformat()
        
        return SessionMetadata(
            start_time=start_time,
            end_time=end_time,
            message_count=len(messages),
            compaction_trigger=trigger
        )

    def _summarize_text(self, text: str, max_length: int) -> str:
        """Create a concise summary of text."""
        if len(text) <= max_length:
            return text.strip()
        
        # Simple summarization - take first sentence or truncate
        sentences = text.split('.')
        if sentences and len(sentences[0]) <= max_length:
            return sentences[0].strip() + '.'
        
        return text[:max_length-3].strip() + '...'

    def _assess_impact(self, content: str) -> str:
        """Assess the impact level of a decision."""
        high_impact_words = ['critical', 'important', 'major', 'significant', 'breaking', 'complete']
        medium_impact_words = ['update', 'change', 'modify', 'improve', 'enhance']
        
        content_lower = content.lower()
        
        if any(word in content_lower for word in high_impact_words):
            return "high"
        elif any(word in content_lower for word in medium_impact_words):
            return "medium"
        else:
            return "low"

    def _assess_status(self, content: str) -> str:
        """Assess implementation status."""
        if any(word in content.lower() for word in ['completed', 'done', 'finished', 'success']):
            return "completed"
        elif any(word in content.lower() for word in ['failed', 'error', 'broken']):
            return "failed"
        else:
            return "pending"

    def _classify_change_type(self, content: str) -> str:
        """Classify the type of change."""
        if any(word in content.lower() for word in ['fix', 'bug', 'error', 'issue']):
            return "fix"
        elif any(word in content.lower() for word in ['refactor', 'restructure', 'reorganize']):
            return "refactor"
        else:
            return "feature"

    def _assess_validation_status(self, content: str) -> str:
        """Assess validation status of changes."""
        if any(word in content.lower() for word in ['test', 'validated', 'verified']):
            return "tested"
        elif any(word in content.lower() for word in ['fail', 'error', 'broken']):
            return "failed"
        else:
            return "untested"

    def _assess_task_status(self, content: str) -> str:
        """Assess task status."""
        if any(word in content.lower() for word in ['in progress', 'working on', 'implementing']):
            return "in_progress"
        elif any(word in content.lower() for word in ['blocked', 'waiting', 'stuck']):
            return "blocked"
        else:
            return "pending"

    def _create_fallback_summary(self, session_id: str, trigger: str) -> Dict[str, Any]:
        """Create minimal fallback summary when analysis fails."""
        now = datetime.now().isoformat()
        
        return {
            "conversation_id": session_id,
            "session_metadata": {
                "start_time": now,
                "end_time": now,
                "message_count": 0,
                "compaction_trigger": trigger
            },
            "key_decisions": [],
            "technical_changes": [],
            "active_tasks": [],
            "context_preservation": {
                "critical_code_sections": [],
                "key_concepts": [],
                "user_preferences": {}
            }
        }