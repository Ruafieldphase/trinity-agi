#!/usr/bin/env python3
"""
Add Orchestration Section to Monitoring Dashboard
"""
import sys
from pathlib import Path
from workspace_root import get_workspace_root

# Import orchestration bridge
WORKSPACE_ROOT = get_workspace_root()
sys.path.insert(0, str(WORKSPACE_ROOT / "scripts"))

from orchestration_bridge import OrchestrationBridge

def generate_orchestration_html() -> str:
    """
    Generate HTML section for orchestration status
    
    Returns:
        HTML string
    """
    bridge = OrchestrationBridge(workspace_root=str(WORKSPACE_ROOT))
    context = bridge.get_orchestration_context()
    
    # CSS classes for health
    health_class_map = {
        "EXCELLENT": "success",
        "GOOD": "info",
        "DEGRADED": "warning",
        "POOR": "danger",
        "OFFLINE": "dark"
    }
    
    # Build channel cards
    channel_cards = ""
    for name, ch in context.channels.items():
        health_class = health_class_map.get(ch.health.value, "secondary")
        optional_badge = '<span class="badge bg-secondary ms-2">Optional</span>' if ch.optional else ""
        
        channel_cards += f"""
        <div class="col-md-4">
            <div class="card shadow-sm mb-3">
                <div class="card-body">
                    <h6 class="card-title">
                        {name} Channel {optional_badge}
                        <span class="badge bg-{health_class}">{ch.health.value}</span>
                    </h6>
                    <ul class="list-unstyled mb-0 small">
                        <li>레이턴시: <strong>{ch.mean_latency_ms:.0f}ms</strong></li>
                        <li>가용성: <strong>{ch.availability:.1f}%</strong></li>
                        <li>스파이크: <strong>{ch.spikes}</strong></li>
                        <li>우선순위: <strong>{ch.routing_priority.value}</strong></li>
                    </ul>
                </div>
            </div>
        </div>
        """
    
    # Recovery badge
    recovery_badge = ""
    if context.recovery_needed:
        recovery_badge = f"""
        <div class="alert alert-warning" role="alert">
            <strong>⚠️ Recovery Needed:</strong> {context.recovery_reason}
        </div>
        """
    
    # Full HTML
    html = f"""
    <div class="row mt-4">
        <div class="col-12">
            <h3 class="mb-3">🎯 Orchestration Status</h3>
            {recovery_badge}
        </div>
    </div>
    
    <div class="row">
        {channel_cards}
    </div>
    
    <div class="row mt-3">
        <div class="col-12">
            <h5>Routing Recommendation</h5>
            <p class="mb-0">
                <strong>Primary:</strong> {context.recommended_primary}
            </p>
            <p class="text-muted small mb-0">
                Last updated: {context.timestamp}
            </p>
        </div>
    </div>
    """
    
    return html

def main():
    """Generate and print HTML"""
    try:
        html = generate_orchestration_html()
        print(html)
    except Exception as e:
        print(f"<div class='alert alert-danger'>Error generating orchestration section: {e}</div>")
        sys.exit(1)

if __name__ == "__main__":
    main()
