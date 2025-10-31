#!/usr/bin/env python3
"""
Session Search - Fast search and query tool for Session Memory System

Features:
- Full-text search (FTS5) across sessions, tasks, artifacts
- Filter by date range, status, persona, tags
- Find similar sessions (by tags or context)
- Get session details with all tasks and artifacts
- Export results to JSON/CSV/Markdown

Usage:
    # Search by keyword
    python session_search.py search "BQI Phase 6"
    
    # Get recent sessions
    python session_search.py recent --limit 10
    
    # Find sessions by file
    python session_search.py by-file "bqi_learner.py"
    
    # Get session details
    python session_search.py details <session-id>
    
    # Find similar sessions
    python session_search.py similar <session-id>
"""

import argparse
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from tabulate import tabulate

# Default paths
WORKSPACE_ROOT = Path("C:/workspace/agi")
SESSION_DB_PATH = WORKSPACE_ROOT / "session_memory" / "sessions.db"


class SessionSearch:
    """Search and query tool for session database."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize SessionSearch."""
        self.db_path = db_path or SESSION_DB_PATH
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
    
    def __del__(self):
        """Close database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def search_text(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Full-text search across sessions and tasks.
        
        Args:
            query: Search query (FTS5 syntax)
            limit: Maximum results
        
        Returns:
            List of matching sessions with highlights
        """
        cursor = self.conn.cursor()
        
        # Search sessions
        cursor.execute('''
            SELECT s.*, 
                   snippet(sessions_fts, 1, '**', '**', '...', 32) as title_snippet,
                   snippet(sessions_fts, 2, '**', '**', '...', 64) as description_snippet
            FROM sessions_fts
            JOIN sessions s ON sessions_fts.session_id = s.session_id
            WHERE sessions_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ''', (query, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        
        # Add task count and artifact count
        for result in results:
            session_id = result['session_id']
            
            # Count tasks
            cursor.execute('SELECT COUNT(*) FROM tasks WHERE session_id = ?', (session_id,))
            result['task_count'] = cursor.fetchone()[0]
            
            # Count artifacts
            cursor.execute('SELECT COUNT(*) FROM artifacts WHERE session_id = ?', (session_id,))
            result['artifact_count'] = cursor.fetchone()[0]
            
            # Get tags
            cursor.execute('''
                SELECT GROUP_CONCAT(t.tag_name) as tags
                FROM session_tags st
                JOIN tags t ON st.tag_id = t.tag_id
                WHERE st.session_id = ?
            ''', (session_id,))
            tags_row = cursor.fetchone()
            result['tags'] = tags_row[0] if tags_row and tags_row[0] else None
        
        return results
    
    def get_recent_sessions(
        self, 
        limit: int = 20,
        status: Optional[str] = None,
        persona: Optional[str] = None,
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent sessions with filters.
        
        Args:
            limit: Maximum results
            status: Filter by status (active, paused, completed, abandoned)
            persona: Filter by persona name
            days: Only sessions in last N days
        
        Returns:
            List of sessions
        """
        cursor = self.conn.cursor()
        
        query = 'SELECT * FROM v_recent_sessions WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if persona:
            query += ' AND persona = ?'
            params.append(persona)
        
        if days:
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            query += ' AND start_time >= ?'
            params.append(cutoff)
        
        query += ' ORDER BY start_time DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full details of a session including tasks and artifacts.
        
        Args:
            session_id: Session UUID
        
        Returns:
            Session details dict or None
        """
        cursor = self.conn.cursor()
        
        # Get session
        cursor.execute('SELECT * FROM sessions WHERE session_id = ?', (session_id,))
        session_row = cursor.fetchone()
        
        if not session_row:
            return None
        
        session = dict(session_row)
        
        # Get tags
        cursor.execute('''
            SELECT GROUP_CONCAT(t.tag_name) as tags
            FROM session_tags st
            JOIN tags t ON st.tag_id = t.tag_id
            WHERE st.session_id = ?
        ''', (session_id,))
        tags_row = cursor.fetchone()
        session['tags'] = tags_row[0].split(',') if tags_row and tags_row[0] else []
        
        # Get tasks
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE session_id = ? 
            ORDER BY task_number
        ''', (session_id,))
        session['tasks'] = [dict(row) for row in cursor.fetchall()]
        
        # Get artifacts
        cursor.execute('''
            SELECT * FROM artifacts 
            WHERE session_id = ? 
            ORDER BY created_at
        ''', (session_id,))
        session['artifacts'] = [dict(row) for row in cursor.fetchall()]
        
        return session
    
    def find_by_file(self, file_pattern: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Find sessions that created/modified a specific file.
        
        Args:
            file_pattern: File name or path pattern (SQL LIKE syntax)
            limit: Maximum results
        
        Returns:
            List of sessions
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT s.*, 
                   COUNT(DISTINCT t.task_id) as task_count,
                   COUNT(DISTINCT a.artifact_id) as artifact_count
            FROM sessions s
            JOIN artifacts a ON s.session_id = a.session_id
            LEFT JOIN tasks t ON s.session_id = t.session_id
            WHERE a.file_path LIKE ? OR a.relative_path LIKE ?
            GROUP BY s.session_id
            ORDER BY s.start_time DESC
            LIMIT ?
        ''', (f'%{file_pattern}%', f'%{file_pattern}%', limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def find_similar(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find sessions similar to given session (by tags).
        
        Args:
            session_id: Reference session UUID
            limit: Maximum results
        
        Returns:
            List of similar sessions with similarity score
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            SELECT s2.*, COUNT(*) as shared_tags,
                   COUNT(DISTINCT t.task_id) as task_count,
                   COUNT(DISTINCT a.artifact_id) as artifact_count
            FROM session_tags st1
            JOIN session_tags st2 ON st1.tag_id = st2.tag_id
            JOIN sessions s2 ON st2.session_id = s2.session_id
            LEFT JOIN tasks t ON s2.session_id = t.session_id
            LEFT JOIN artifacts a ON s2.session_id = a.session_id
            WHERE st1.session_id = ? AND st2.session_id != ?
            GROUP BY s2.session_id
            ORDER BY shared_tags DESC, s2.start_time DESC
            LIMIT ?
        ''', (session_id, session_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active or paused sessions."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM v_active_sessions')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_stats_by_persona(self) -> List[Dict[str, Any]]:
        """Get session statistics grouped by persona."""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM v_session_stats_by_persona')
        return [dict(row) for row in cursor.fetchall()]
    
    def export_to_json(self, results: List[Dict[str, Any]], output_path: Path):
        """Export results to JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Exported to {output_path}")
    
    def export_to_markdown(self, session: Dict[str, Any], output_path: Path):
        """Export session details to Markdown file."""
        md_lines = [
            f"# {session['title']}",
            f"",
            f"**Session ID**: `{session['session_id']}`  ",
            f"**Started**: {session['start_time']}  ",
            f"**Status**: {session['status']}  ",
        ]
        
        if session.get('end_time'):
            md_lines.append(f"**Ended**: {session['end_time']}  ")
        
        if session.get('persona'):
            md_lines.append(f"**Persona**: {session['persona']}  ")
        
        if session.get('resonance_score'):
            md_lines.append(f"**Resonance**: {session['resonance_score']:.2f}  ")
        
        if session.get('tags'):
            tags_str = ', '.join(session['tags'])
            md_lines.append(f"**Tags**: {tags_str}  ")
        
        if session.get('description'):
            md_lines.extend([
                f"",
                f"## Description",
                f"",
                session['description']
            ])
        
        if session.get('context'):
            md_lines.extend([
                f"",
                f"## Context",
                f"",
                session['context']
            ])
        
        # Tasks
        if session.get('tasks'):
            md_lines.extend([
                f"",
                f"## Tasks ({len(session['tasks'])})",
                f""
            ])
            
            for task in session['tasks']:
                status_emoji = {
                    'completed': '✅',
                    'in-progress': '🔄',
                    'not-started': '⏳',
                    'blocked': '🚫'
                }.get(task['status'], '❓')
                
                md_lines.append(f"{task['task_number']}. {status_emoji} **{task['title']}**")
                if task.get('description'):
                    md_lines.append(f"   - {task['description']}")
        
        # Artifacts
        if session.get('artifacts'):
            md_lines.extend([
                f"",
                f"## Artifacts ({len(session['artifacts'])})",
                f""
            ])
            
            for artifact in session['artifacts']:
                op_emoji = {
                    'created': '📄',
                    'modified': '✏️',
                    'deleted': '🗑️'
                }.get(artifact['operation'], '📎')
                
                md_lines.append(f"- {op_emoji} `{artifact['relative_path']}` ({artifact['artifact_type']})")
                if artifact.get('description'):
                    md_lines.append(f"  - {artifact['description']}")
        
        md_content = '\n'.join(md_lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"✅ Exported to {output_path}")


def format_session_table(sessions: List[Dict[str, Any]]) -> str:
    """Format sessions as table for console output."""
    if not sessions:
        return "No sessions found."
    
    # Prepare table data
    headers = ["ID (first 8)", "Title", "Started", "Status", "Tasks", "Files", "Tags"]
    rows = []
    
    for s in sessions:
        row = [
            s['session_id'][:8],
            s['title'][:50],
            s['start_time'][:16],  # Just date and time
            s['status'],
            s.get('task_count', 0),
            s.get('artifact_count', 0),
            (s.get('tags') or '')[:30]
        ]
        rows.append(row)
    
    return tabulate(rows, headers=headers, tablefmt='simple')


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Search and query session history")
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Full-text search')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=20, help='Max results')
    search_parser.add_argument('--json', type=Path, help='Export to JSON')
    
    # Recent command
    recent_parser = subparsers.add_parser('recent', help='Get recent sessions')
    recent_parser.add_argument('--limit', type=int, default=20, help='Max results')
    recent_parser.add_argument('--status', choices=['active', 'paused', 'completed', 'abandoned'])
    recent_parser.add_argument('--persona', help='Filter by persona')
    recent_parser.add_argument('--days', type=int, help='Last N days')
    recent_parser.add_argument('--json', type=Path, help='Export to JSON')
    
    # Details command
    details_parser = subparsers.add_parser('details', help='Get session details')
    details_parser.add_argument('session_id', help='Session UUID')
    details_parser.add_argument('--markdown', type=Path, help='Export to Markdown')
    details_parser.add_argument('--json', type=Path, help='Export to JSON')
    
    # By-file command
    byfile_parser = subparsers.add_parser('by-file', help='Find sessions by file')
    byfile_parser.add_argument('pattern', help='File name or path pattern')
    byfile_parser.add_argument('--limit', type=int, default=20, help='Max results')
    byfile_parser.add_argument('--json', type=Path, help='Export to JSON')
    
    # Similar command
    similar_parser = subparsers.add_parser('similar', help='Find similar sessions')
    similar_parser.add_argument('session_id', help='Reference session UUID')
    similar_parser.add_argument('--limit', type=int, default=10, help='Max results')
    similar_parser.add_argument('--json', type=Path, help='Export to JSON')
    
    # Active command
    subparsers.add_parser('active', help='Get active sessions')
    
    # Stats command
    subparsers.add_parser('stats', help='Get statistics by persona')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize search
    try:
        search = SessionSearch()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Run a session first to create the database.")
        return
    
    # Execute command
    if args.command == 'search':
        results = search.search_text(args.query, args.limit)
        print(format_session_table(results))
        
        if args.json:
            search.export_to_json(results, args.json)
    
    elif args.command == 'recent':
        results = search.get_recent_sessions(
            limit=args.limit,
            status=args.status,
            persona=args.persona,
            days=args.days
        )
        print(format_session_table(results))
        
        if args.json:
            search.export_to_json(results, args.json)
    
    elif args.command == 'details':
        session = search.get_session_details(args.session_id)
        
        if not session:
            print(f"❌ Session not found: {args.session_id}")
            return
        
        # Print summary
        print(f"\n📋 {session['title']}")
        print(f"   Session ID: {session['session_id']}")
        print(f"   Started: {session['start_time']}")
        if session.get('end_time'):
            print(f"   Ended: {session['end_time']}")
        print(f"   Status: {session['status']}")
        if session.get('persona'):
            print(f"   Persona: {session['persona']}")
        if session.get('resonance_score'):
            print(f"   Resonance: {session['resonance_score']:.2f}")
        if session.get('tags'):
            print(f"   Tags: {', '.join(session['tags'])}")
        
        print(f"\n   Tasks: {len(session['tasks'])}")
        print(f"   Artifacts: {len(session['artifacts'])}")
        
        if args.markdown:
            search.export_to_markdown(session, args.markdown)
        
        if args.json:
            search.export_to_json([session], args.json)
    
    elif args.command == 'by-file':
        results = search.find_by_file(args.pattern, args.limit)
        print(format_session_table(results))
        
        if args.json:
            search.export_to_json(results, args.json)
    
    elif args.command == 'similar':
        results = search.find_similar(args.session_id, args.limit)
        print(format_session_table(results))
        
        if args.json:
            search.export_to_json(results, args.json)
    
    elif args.command == 'active':
        results = search.get_active_sessions()
        print(format_session_table(results))
    
    elif args.command == 'stats':
        results = search.get_stats_by_persona()
        
        if results:
            headers = ["Persona", "Sessions", "Completed", "Avg Resonance", "Avg Hours"]
            rows = [
                [
                    r['persona'],
                    r['session_count'],
                    r['completed_count'],
                    f"{r['avg_resonance']:.2f}" if r['avg_resonance'] else 'N/A',
                    f"{r['avg_duration_hours']:.1f}" if r['avg_duration_hours'] else 'N/A'
                ]
                for r in results
            ]
            print(tabulate(rows, headers=headers, tablefmt='simple'))
        else:
            print("No session data available.")


if __name__ == "__main__":
    main()
