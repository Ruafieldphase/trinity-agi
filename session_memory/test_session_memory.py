"""
Test Suite for Session Memory System
"""
import os
import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from session_logger import SessionLogger
from session_search import SessionSearch


def test_session_lifecycle():
    """Test complete session lifecycle: start -> add task -> add file -> end"""
    print("\n=== Test: Session Lifecycle ===")
    
    logger = SessionLogger()
    
    # Start session
    session_id = logger.start_session(
        title="Test Session",
        description="Testing session memory system",
        tags=["test", "ci"]
    )
    assert session_id is not None, "Session ID should not be None"
    print(f"✓ Session started: {session_id}")
    
    # Add task
    logger.add_task(
        title="Test Task 1",
        description="First test task"
    )
    print("✓ Task added")
    
    # Add artifact
    test_file = Path(__file__)
    logger.add_artifact(
        file_path=str(test_file),
        artifact_type="code",
        operation="modified"
    )
    print(f"✓ Artifact added: {test_file.name}")
    
    # End session
    logger.end_session(resonance_score=0.85)
    print("✓ Session ended with resonance: 0.85")
    
    return session_id


def test_search_functionality(session_id):
    """Test search and query operations"""
    print("\n=== Test: Search Functionality ===")
    
    searcher = SessionSearch()
    
    # Test recent sessions
    recent = searcher.get_recent_sessions(limit=5)
    assert len(recent) > 0, "Should have at least one session"
    print(f"✓ Found {len(recent)} recent session(s)")
    
    # Test full-text search
    results = searcher.search_text("test", limit=10)
    assert len(results) > 0, "Should find test session"
    print(f"✓ FTS search found {len(results)} result(s)")
    
    # Test session details
    details = searcher.get_session_details(session_id)
    assert details is not None, "Should retrieve session details"
    assert len(details['tasks']) > 0, "Should have at least one task"
    assert len(details['artifacts']) > 0, "Should have at least one artifact"
    print(f"✓ Session details: {len(details['tasks'])} tasks, {len(details['artifacts'])} artifacts")
    
    # Test active sessions
    active = searcher.get_active_sessions()
    print(f"✓ Active sessions: {len(active)}")
    
    # Test stats
    stats = searcher.get_stats_by_persona()
    print(f"✓ Stats by persona: {len(stats)} persona(s)")
    
    return details


def test_export_functionality(session_id):
    """Test export to JSON and Markdown"""
    print("\n=== Test: Export Functionality ===")
    
    searcher = SessionSearch()
    
    # Get session details
    session = searcher.get_session_details(session_id)
    
    # Export to JSON
    json_path = Path(__file__).parent / "outputs" / "test_session.json"
    json_path.parent.mkdir(exist_ok=True)
    searcher.export_to_json([session], str(json_path))
    assert json_path.exists(), "JSON export file should exist"
    print(f"✓ Exported to JSON: {json_path.name}")
    
    # Export to Markdown
    md_path = Path(__file__).parent / "outputs" / "test_session.md"
    searcher.export_to_markdown(session, str(md_path))
    assert md_path.exists(), "Markdown export file should exist"
    print(f"✓ Exported to Markdown: {md_path.name}")
    
    # Verify JSON content
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert len(data) == 1, "Should have one session"
        assert data[0]['session_id'] == session_id, "Session ID should match"
    print("✓ JSON content verified")
    
    # Clean up
    json_path.unlink()
    md_path.unlink()
    print("✓ Cleanup completed")


def test_error_handling():
    """Test error handling scenarios"""
    print("\n=== Test: Error Handling ===")
    
    logger = SessionLogger()
    searcher = SessionSearch()
    
    # Test adding task without active session
    try:
        # First end any active session
        if logger.current_session_id:
            logger.end_session()
        
        # Reset state
        logger.current_session_id = None
        logger.current_task_number = 0
        
        # Now try to add task without session
        logger.add_task("Should fail")
        print("✗ Should have raised error for task without session")
    except ValueError as e:
        print(f"✓ Correctly raised error: {e}")
    
    # Test invalid session ID in search
    invalid = searcher.get_session_details("00000000-0000-0000-0000-000000000000")
    assert invalid is None, "Should return None for invalid session ID"
    print("✓ Handled invalid session ID gracefully")
    
    # Test search with no results
    results = searcher.search_text("xyzxyzxyznonexistent", limit=10)
    assert len(results) == 0, "Should return empty list for no matches"
    print("✓ Handled empty search results")


def test_database_integrity():
    """Test database integrity and FTS5 sync"""
    print("\n=== Test: Database Integrity ===")
    
    db_path = Path(__file__).parent / "sessions.db"
    assert db_path.exists(), "Database should exist"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Check tables exist
    tables = ['sessions', 'tasks', 'artifacts', 'tags', 'session_tags', 
              'sessions_fts', 'tasks_fts']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    db_tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        assert table in db_tables, f"Table {table} should exist"
    print(f"✓ All {len(tables)} tables exist")
    
    # Check views exist
    views = ['v_recent_sessions', 'v_active_sessions', 'v_session_stats_by_persona']
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    db_views = [row[0] for row in cursor.fetchall()]
    
    for view in views:
        assert view in db_views, f"View {view} should exist"
    print(f"✓ All {len(views)} views exist")
    
    # Check FTS5 sync
    cursor.execute("SELECT COUNT(*) FROM sessions")
    session_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sessions_fts")
    fts_count = cursor.fetchone()[0]
    
    assert session_count == fts_count, "FTS5 should be in sync with sessions"
    print(f"✓ FTS5 sync verified: {session_count} sessions")
    
    conn.close()


def test_pause_resume():
    """Test pause and resume functionality"""
    print("\n=== Test: Pause & Resume ===")
    
    logger = SessionLogger()
    
    # Start session
    session_id = logger.start_session(
        title="Pause Test Session",
        description="Testing pause/resume"
    )
    print(f"✓ Session started: {session_id}")
    
    # Pause session
    logger.pause_session()
    print("✓ Session paused")
    
    # Verify paused status
    searcher = SessionSearch()
    session = searcher.get_session_details(session_id)
    assert session['status'] == 'paused', "Status should be paused"
    print("✓ Status verified: paused")
    
    # Resume session
    logger.resume_session(session_id)
    print("✓ Session resumed")
    
    # Verify active status
    session = searcher.get_session_details(session_id)
    assert session['status'] == 'active', "Status should be active"
    print("✓ Status verified: active")
    
    # Clean up
    logger.end_session()
    print("✓ Session ended")


def run_all_tests():
    """Run all test suites"""
    print("=" * 60)
    print("Session Memory System - Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        session_id = test_session_lifecycle()
        test_search_functionality(session_id)
        test_export_functionality(session_id)
        test_pause_resume()
        test_error_handling()
        test_database_integrity()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(run_all_tests())
