#!/usr/bin/env python3
"""
Session Logger - Core implementation for Session Memory System
Hybrid approach: JSONL (append-only, source of truth) + SQLite (fast queries)

Features:
- Auto-generate session IDs (UUID)
- Append to JSONL log (immutable history)
- Sync to SQLite DB (fast search with FTS5)
- Track tasks, artifacts, tags
- Git integration (branch, commit)
- Persona tracking
- Resonance score calculation

Usage:
    from session_logger import SessionLogger
    
    logger = SessionLogger()
    session_id = logger.start_session("BQI Phase 6 implementation")
    logger.add_task("Implement online learner", description="...")
    logger.add_artifact("outputs/ensemble_weights.json", artifact_type="data")
    logger.end_session(resonance_score=0.85)
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import hashlib
import subprocess

# Default paths (relative to workspace root)
WORKSPACE_ROOT = Path("C:/workspace/agi")
SESSION_LOG_PATH = WORKSPACE_ROOT / "session_memory" / "session_log.jsonl"
SESSION_DB_PATH = WORKSPACE_ROOT / "session_memory" / "sessions.db"
SCHEMA_PATH = WORKSPACE_ROOT / "session_memory" / "schema.sql"


class SessionLogger:
    """Main class for logging work sessions and artifacts."""
    
    def __init__(
        self, 
        log_path: Optional[Path] = None,
        db_path: Optional[Path] = None,
        auto_sync: bool = True
    ):
        """
        Initialize SessionLogger.
        
        Args:
            log_path: Path to JSONL log file
            db_path: Path to SQLite database
            auto_sync: If True, sync to DB after each operation
        """
        self.log_path = log_path or SESSION_LOG_PATH
        self.db_path = db_path or SESSION_DB_PATH
        self.auto_sync = auto_sync
        
        # Ensure directories exist
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Current session state
        self.current_session_id: Optional[str] = None
        self.current_task_number = 0
    
    def _init_db(self):
        """Initialize SQLite database with schema."""
        if not self.db_path.exists() or self.db_path.stat().st_size == 0:
            # Create new database from schema
            if SCHEMA_PATH.exists():
                with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                
                conn = sqlite3.connect(self.db_path)
                conn.executescript(schema_sql)
                conn.commit()
                conn.close()
                print(f"✅ Database initialized: {self.db_path}")
            else:
                print(f"⚠️ Schema file not found: {SCHEMA_PATH}")
    
    def _append_to_log(self, entry: Dict[str, Any]):
        """Append entry to JSONL log (immutable history)."""
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    def _get_git_info(self) -> Dict[str, Optional[str]]:
        """Get current Git branch and commit hash."""
        try:
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=WORKSPACE_ROOT,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            commit = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD'],
                cwd=WORKSPACE_ROOT,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            
            return {'branch': branch, 'commit_hash': commit}
        except Exception:
            return {'branch': None, 'commit_hash': None}
    
    def _calculate_file_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA256 hash of file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return None
    
    def start_session(
        self,
        title: str,
        description: Optional[str] = None,
        context: Optional[str] = None,
        persona: Optional[str] = None,
        parent_session_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Start a new work session.
        
        Args:
            title: Session title (required)
            description: Brief summary
            context: What are you working on?
            persona: Active persona name
            parent_session_id: Continue from previous session
            tags: List of tags for categorization
        
        Returns:
            session_id (UUID string)
        """
        session_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc).isoformat()
        git_info = self._get_git_info()
        
        entry = {
            'event_type': 'session_start',
            'session_id': session_id,
            'start_time': start_time,
            'title': title,
            'description': description,
            'context': context,
            'status': 'active',
            'persona': persona,
            'parent_session_id': parent_session_id,
            'branch': git_info['branch'],
            'commit_hash': git_info['commit_hash'],
            'tags': tags or []
        }
        
        # Append to JSONL log
        self._append_to_log(entry)
        
        # Sync to SQLite
        if self.auto_sync:
            self._sync_session_to_db(entry)
        
        # Update state
        self.current_session_id = session_id
        self.current_task_number = 0
        
        print(f"🚀 Session started: {title}")
        print(f"   Session ID: {session_id}")
        if git_info['branch']:
            print(f"   Git branch: {git_info['branch']}")
        
        return session_id
    
    def _sync_session_to_db(self, entry: Dict[str, Any]):
        """Sync session entry to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions 
            (session_id, start_time, end_time, title, description, status, 
             context, branch, commit_hash, persona, parent_session_id, resonance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry['session_id'],
            entry['start_time'],
            entry.get('end_time'),
            entry['title'],
            entry.get('description'),
            entry['status'],
            entry.get('context'),
            entry.get('branch'),
            entry.get('commit_hash'),
            entry.get('persona'),
            entry.get('parent_session_id'),
            entry.get('resonance_score')
        ))
        
        # Add tags if provided
        if entry.get('tags'):
            for tag_name in entry['tags']:
                # Insert tag if not exists
                cursor.execute('INSERT OR IGNORE INTO tags (tag_name) VALUES (?)', (tag_name,))
                
                # Get tag_id
                cursor.execute('SELECT tag_id FROM tags WHERE tag_name = ?', (tag_name,))
                tag_id = cursor.fetchone()[0]
                
                # Link session to tag
                cursor.execute('''
                    INSERT OR IGNORE INTO session_tags (session_id, tag_id) 
                    VALUES (?, ?)
                ''', (entry['session_id'], tag_id))
        
        conn.commit()
        conn.close()
    
    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        status: str = 'in-progress',
        session_id: Optional[str] = None
    ) -> str:
        """
        Add a task to current or specified session.
        
        Args:
            title: Task title
            description: Task details
            status: not-started, in-progress, completed, blocked
            session_id: Override current session
        
        Returns:
            task_id (UUID string)
        """
        if not session_id:
            session_id = self.current_session_id
        
        if not session_id:
            raise ValueError("No active session. Call start_session() first.")
        
        task_id = str(uuid.uuid4())
        self.current_task_number += 1
        started_at = datetime.now(timezone.utc).isoformat()
        
        entry = {
            'event_type': 'task_add',
            'task_id': task_id,
            'session_id': session_id,
            'task_number': self.current_task_number,
            'title': title,
            'description': description,
            'status': status,
            'started_at': started_at
        }
        
        # Append to JSONL log
        self._append_to_log(entry)
        
        # Sync to SQLite
        if self.auto_sync:
            self._sync_task_to_db(entry)
        
        print(f"📋 Task added: {title}")
        return task_id
    
    def _sync_task_to_db(self, entry: Dict[str, Any]):
        """Sync task entry to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (task_id, session_id, task_number, title, description, status, started_at, completed_at, duration_seconds, result, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry['task_id'],
            entry['session_id'],
            entry['task_number'],
            entry['title'],
            entry.get('description'),
            entry['status'],
            entry.get('started_at'),
            entry.get('completed_at'),
            entry.get('duration_seconds'),
            entry.get('result'),
            entry.get('notes')
        ))
        
        conn.commit()
        conn.close()
    
    def add_artifact(
        self,
        file_path: str,
        artifact_type: str = 'file',
        operation: str = 'created',
        description: Optional[str] = None,
        task_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """
        Track a file or code artifact created/modified in session.
        
        Args:
            file_path: Absolute or relative file path
            artifact_type: file, code, script, doc, data
            operation: created, modified, deleted
            description: What is this artifact
            task_id: Associate with specific task
            session_id: Override current session
        
        Returns:
            artifact_id (UUID string)
        """
        if not session_id:
            session_id = self.current_session_id
        
        if not session_id:
            raise ValueError("No active session. Call start_session() first.")
        
        artifact_id = str(uuid.uuid4())
        
        # Convert to Path object
        path = Path(file_path)
        
        # Calculate relative path if file is in workspace
        try:
            relative_path = str(path.relative_to(WORKSPACE_ROOT))
        except ValueError:
            relative_path = str(path)
        
        # Get file info
        content_hash = self._calculate_file_hash(path) if path.exists() else None
        file_size = path.stat().st_size if path.exists() else None
        
        entry = {
            'event_type': 'artifact_add',
            'artifact_id': artifact_id,
            'session_id': session_id,
            'task_id': task_id,
            'artifact_type': artifact_type,
            'file_path': str(path.absolute()),
            'relative_path': relative_path,
            'content_hash': content_hash,
            'file_size_bytes': file_size,
            'operation': operation,
            'description': description,
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Append to JSONL log
        self._append_to_log(entry)
        
        # Sync to SQLite
        if self.auto_sync:
            self._sync_artifact_to_db(entry)
        
        print(f"📄 Artifact tracked: {relative_path} ({operation})")
        return artifact_id
    
    def _sync_artifact_to_db(self, entry: Dict[str, Any]):
        """Sync artifact entry to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO artifacts 
            (artifact_id, session_id, task_id, artifact_type, file_path, relative_path, 
             content_hash, file_size_bytes, operation, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry['artifact_id'],
            entry['session_id'],
            entry.get('task_id'),
            entry['artifact_type'],
            entry.get('file_path'),
            entry.get('relative_path'),
            entry.get('content_hash'),
            entry.get('file_size_bytes'),
            entry['operation'],
            entry.get('description'),
            entry['created_at']
        ))
        
        conn.commit()
        conn.close()
    
    def end_session(
        self,
        resonance_score: Optional[float] = None,
        result: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        End current or specified session.
        
        Args:
            resonance_score: 0.0-1.0, how successful was this session
            result: Brief result summary
            session_id: Override current session
        """
        if not session_id:
            session_id = self.current_session_id
        
        if not session_id:
            raise ValueError("No active session to end.")
        
        end_time = datetime.now(timezone.utc).isoformat()
        
        entry = {
            'event_type': 'session_end',
            'session_id': session_id,
            'end_time': end_time,
            'status': 'completed',
            'resonance_score': resonance_score,
            'result': result
        }
        
        # Append to JSONL log
        self._append_to_log(entry)
        
        # Sync to SQLite (update existing session)
        if self.auto_sync:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sessions 
                SET end_time = ?, status = ?, resonance_score = ?
                WHERE session_id = ?
            ''', (end_time, 'completed', resonance_score, session_id))
            
            conn.commit()
            conn.close()
        
        # Clear state
        self.current_session_id = None
        self.current_task_number = 0
        
        print(f"✅ Session ended: {session_id}")
        if resonance_score:
            print(f"   Resonance: {resonance_score:.2f}")
    
    def pause_session(self, session_id: Optional[str] = None):
        """Pause current session (can be resumed later)."""
        if not session_id:
            session_id = self.current_session_id
        
        if not session_id:
            raise ValueError("No active session to pause.")
        
        entry = {
            'event_type': 'session_pause',
            'session_id': session_id,
            'paused_at': datetime.now(timezone.utc).isoformat(),
            'status': 'paused'
        }
        
        self._append_to_log(entry)
        
        if self.auto_sync:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET status = ? WHERE session_id = ?', ('paused', session_id))
            conn.commit()
            conn.close()
        
        print(f"⏸️ Session paused: {session_id}")
    
    def resume_session(self, session_id: str):
        """Resume a paused session."""
        entry = {
            'event_type': 'session_resume',
            'session_id': session_id,
            'resumed_at': datetime.now(timezone.utc).isoformat(),
            'status': 'active'
        }
        
        self._append_to_log(entry)
        
        if self.auto_sync:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('UPDATE sessions SET status = ? WHERE session_id = ?', ('active', session_id))
            conn.commit()
            conn.close()
        
        self.current_session_id = session_id
        print(f"▶️ Session resumed: {session_id}")


if __name__ == "__main__":
    # Example usage
    logger = SessionLogger()
    
    # Start session
    session_id = logger.start_session(
        title="Session Memory System Implementation",
        description="Create hybrid JSONL + SQLite session tracking",
        context="Building session logger to track work history",
        persona="Perple",
        tags=["session-memory", "infrastructure", "phase-7"]
    )
    
    # Add tasks
    task1 = logger.add_task("Design database schema", status="completed")
    task2 = logger.add_task("Implement SessionLogger class", status="in-progress")
    
    # Track artifacts
    logger.add_artifact("session_memory/schema.sql", artifact_type="doc", operation="created")
    logger.add_artifact("session_memory/session_logger.py", artifact_type="code", operation="created")
    
    # End session
    logger.end_session(resonance_score=0.9, result="Core implementation complete")
    
    print("\n✅ Example session logged successfully!")
