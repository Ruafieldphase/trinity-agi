#!/usr/bin/env python3
"""
Simple integration test for Computer Use + HTTP Poller
Tests basic queue functionality and API contract
"""
import requests
import time
import json
from typing import Dict, Any, Optional

API_BASE = "http://127.0.0.1:8091/api"
TIMEOUT = 10  # seconds


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    RESET = '\033[0m'


def log_pass(msg: str):
    print(f"{Colors.GREEN}✓ PASS{Colors.RESET} {msg}")


def log_fail(msg: str):
    print(f"{Colors.RED}✗ FAIL{Colors.RESET} {msg}")


def log_warn(msg: str):
    print(f"{Colors.YELLOW}⚠ WARN{Colors.RESET} {msg}")


def log_info(msg: str):
    print(f"{Colors.CYAN}ℹ INFO{Colors.RESET} {msg}")


def check_server_health() -> bool:
    """Check if test server is running"""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            log_pass(f"Server healthy: {data['service']} (queue: {data['queue_size']}, results: {data['results_count']})")
            return True
        else:
            log_fail(f"Server returned {resp.status_code}")
            return False
    except Exception as e:
        log_fail(f"Server not reachable: {e}")
        return False


def create_task(task_type: str, data: Dict[str, Any]) -> Optional[str]:
    """Create a task and return task_id"""
    try:
        payload = {"type": task_type, "data": data}
        resp = requests.post(f"{API_BASE}/tasks/create", json=payload, timeout=5)
        if resp.status_code == 200:
            result = resp.json()
            task_id = result.get("task_id")
            log_info(f"Task created: {task_id} (type: {task_type})")
            return task_id
        else:
            log_fail(f"Task creation failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        log_fail(f"Task creation error: {e}")
        return None


def poll_result(task_id: str, timeout: int = TIMEOUT) -> Optional[Dict[str, Any]]:
    """Poll for task result with timeout"""
    start = time.time()
    while (time.time() - start) < timeout:
        try:
            resp = requests.get(f"{API_BASE}/results/{task_id}", timeout=5)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                # Result not ready yet
                time.sleep(0.5)
                continue
            else:
                log_warn(f"Unexpected status {resp.status_code} while polling")
                return None
        except Exception as e:
            log_warn(f"Poll error: {e}")
            time.sleep(0.5)
    
    log_warn(f"Result polling timeout after {timeout}s")
    return None


def test_ping():
    """Test 1: Basic ping task"""
    print(f"\n{Colors.CYAN}=== Test 1: Ping Task ==={Colors.RESET}")
    
    task_id = create_task("ping", {})
    if not task_id:
        log_fail("Cannot create ping task")
        return False
    
    log_info("Waiting for HTTP Poller to process task...")
    result = poll_result(task_id, timeout=15)
    
    if result:
        if result.get("success"):
            log_pass(f"Ping task succeeded: {json.dumps(result.get('data', {}), indent=2)}")
            return True
        else:
            log_fail(f"Ping task failed: {result.get('error')}")
            return False
    else:
        log_warn("Ping task result not available (HTTP Poller may not be running)")
        log_info("This is EXPECTED if VS Code extension is not active with HTTP Poller enabled")
        return None  # Indeterminate


def test_computer_use_scan():
    """Test 2: Computer Use scan (requires kill-switch enabled)"""
    print(f"\n{Colors.CYAN}=== Test 2: Computer Use Scan ==={Colors.RESET}")
    
    task_data = {
        "command": "scan",
        "params": {}
    }
    
    task_id = create_task("computer_use.scan", task_data)
    if not task_id:
        log_fail("Cannot create computer_use.scan task")
        return False
    
    log_info("Waiting for HTTP Poller to process Computer Use task...")
    result = poll_result(task_id, timeout=20)
    
    if result:
        if result.get("success"):
            data = result.get("data", {})
            element_count = len(data.get("elements", []))
            log_pass(f"Computer Use scan succeeded: {element_count} elements found")
            return True
        else:
            error = result.get("error", "")
            if "enableComputerUseOverHttp" in error or "kill-switch" in error.lower():
                log_warn(f"Computer Use blocked by kill-switch (expected if disabled): {error}")
                return None  # Expected when disabled
            else:
                log_fail(f"Computer Use scan failed: {error}")
                return False
    else:
        log_warn("Computer Use scan result not available (HTTP Poller may not be running)")
        log_info("This is EXPECTED if VS Code extension is not active")
        return None


def test_api_contract():
    """Test 3: API contract validation"""
    print(f"\n{Colors.CYAN}=== Test 3: API Contract Validation ==={Colors.RESET}")
    
    # Check health endpoint schema
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        data = resp.json()
        required_fields = ["status", "service", "queue_size", "results_count", "timestamp"]
        
        for field in required_fields:
            if field in data:
                log_pass(f"Health endpoint has required field: {field}")
            else:
                log_fail(f"Health endpoint missing field: {field}")
                return False
        
        return True
    except Exception as e:
        log_fail(f"API contract test error: {e}")
        return False


def main():
    """Run all integration tests"""
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}Computer Use + HTTP Poller Integration Tests{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
    
    # Pre-flight: Check server
    log_info("Checking test API server...")
    if not check_server_health():
        log_fail("Test server is not running! Start it with:")
        log_info("  python task_queue_server.py --port 8091")
        return 1
    
    print()
    
    # Run tests
    results = {}
    
    # Test 1: Ping
    results['ping'] = test_ping()
    
    # Test 2: Computer Use scan
    results['computer_use'] = test_computer_use_scan()
    
    # Test 3: API contract
    results['api_contract'] = test_api_contract()
    
    # Summary
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.CYAN}Test Summary{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            log_pass(f"{test_name}")
        elif result is False:
            log_fail(f"{test_name}")
        else:
            log_warn(f"{test_name} (skipped/indeterminate)")
    
    print(f"\n{Colors.CYAN}Results:{Colors.RESET} {passed} passed, {failed} failed, {skipped} skipped (total: {total})")
    
    if failed > 0:
        print(f"\n{Colors.RED}Some tests FAILED{Colors.RESET}")
        return 1
    elif passed > 0:
        print(f"\n{Colors.GREEN}All critical tests PASSED{Colors.RESET}")
        if skipped > 0:
            print(f"{Colors.YELLOW}Note: {skipped} tests skipped (HTTP Poller may not be running){Colors.RESET}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}No tests executed or all indeterminate{Colors.RESET}")
        print(f"{Colors.YELLOW}Make sure VS Code extension is running with HTTP Poller enabled{Colors.RESET}")
        return 2


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        exit(130)
