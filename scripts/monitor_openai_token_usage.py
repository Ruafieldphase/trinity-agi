#!/usr/bin/env python3
"""
💰 OpenAI Token Usage Monitor
==============================

Codex Meta-Observer의 토큰 사용량 추적 및 비용 계산

Author: Autonomous AGI System
Created: 2025-11-11
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# OpenAI 요금 (2025년 기준, 실제는 확인 필요)
CODEX_PRICE_PER_1K_TOKENS = 0.02  # $0.02 per 1K tokens (예시)


class TokenUsageMonitor:
    """OpenAI 토큰 사용량 모니터"""
    
    def __init__(self, workspace_root: str = "c:\\workspace\\agi"):
        self.workspace_root = Path(workspace_root)
        self.observer_dir = self.workspace_root / "outputs" / "codex_meta_observer"
        self.usage_log = self.observer_dir / "token_usage_log.jsonl"
    
    def log_usage(self, prompt_tokens: int, completion_tokens: int, total_tokens: int, model: str = "code-davinci-002"):
        """토큰 사용 로그 기록"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": total_tokens / 1000 * CODEX_PRICE_PER_1K_TOKENS
        }
        
        # JSONL 형식으로 추가
        with open(self.usage_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """최근 N시간 사용량 요약"""
        if not self.usage_log.exists():
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "entries": []
            }
        
        cutoff = datetime.now() - timedelta(hours=hours)
        entries = []
        
        with open(self.usage_log, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line.strip())
                entry_time = datetime.fromisoformat(entry["timestamp"])
                
                if entry_time >= cutoff:
                    entries.append(entry)
        
        total_tokens = sum(e["total_tokens"] for e in entries)
        total_cost = sum(e["estimated_cost_usd"] for e in entries)
        
        return {
            "period_hours": hours,
            "total_calls": len(entries),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 4),
            "avg_tokens_per_call": round(total_tokens / len(entries), 2) if entries else 0,
            "entries": entries
        }
    
    def print_summary(self, hours: int = 24):
        """사용량 요약 출력"""
        summary = self.get_usage_summary(hours)
        
        print(f"\n💰 OpenAI Token Usage Summary (Last {hours}h)")
        print("=" * 60)
        print(f"📞 Total API Calls: {summary['total_calls']}")
        print(f"🎫 Total Tokens: {summary['total_tokens']:,}")
        print(f"💵 Estimated Cost: ${summary['total_cost_usd']:.4f}")
        print(f"📊 Avg per Call: {summary['avg_tokens_per_call']:.1f} tokens")
        print("=" * 60)
        
        if summary["entries"]:
            print("\n📋 Recent Calls:")
            for entry in summary["entries"][-5:]:  # 최근 5개만
                ts = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
                print(f"  [{ts}] {entry['total_tokens']:>5} tokens (${entry['estimated_cost_usd']:.4f})")
    
    def check_budget(self, daily_limit_usd: float = 1.0) -> Dict[str, Any]:
        """일일 예산 체크"""
        summary_24h = self.get_usage_summary(24)
        
        remaining = daily_limit_usd - summary_24h["total_cost_usd"]
        percent_used = (summary_24h["total_cost_usd"] / daily_limit_usd * 100) if daily_limit_usd > 0 else 0
        
        status = "🟢 OK" if percent_used < 50 else "🟡 CAUTION" if percent_used < 80 else "🔴 WARNING"
        
        return {
            "status": status,
            "daily_limit_usd": daily_limit_usd,
            "used_usd": summary_24h["total_cost_usd"],
            "remaining_usd": round(remaining, 4),
            "percent_used": round(percent_used, 1)
        }
    
    def print_budget_status(self, daily_limit_usd: float = 1.0):
        """예산 상태 출력"""
        budget = self.check_budget(daily_limit_usd)
        
        print(f"\n{budget['status']} Daily Budget Check")
        print("=" * 60)
        print(f"💰 Limit: ${budget['daily_limit_usd']:.2f}/day")
        print(f"💸 Used: ${budget['used_usd']:.4f} ({budget['percent_used']:.1f}%)")
        print(f"💵 Remaining: ${budget['remaining_usd']:.4f}")
        print("=" * 60)


def main():
    """메인 실행"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OpenAI Token Usage Monitor")
    parser.add_argument("--hours", type=int, default=24, help="Hours to analyze (default: 24)")
    parser.add_argument("--budget", type=float, default=1.0, help="Daily budget in USD (default: 1.0)")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    
    args = parser.parse_args()
    
    monitor = TokenUsageMonitor()
    
    if args.json:
        summary = monitor.get_usage_summary(args.hours)
        budget = monitor.check_budget(args.budget)
        print(json.dumps({"summary": summary, "budget": budget}, indent=2, ensure_ascii=False))
    else:
        monitor.print_summary(args.hours)
        monitor.print_budget_status(args.budget)


if __name__ == "__main__":
    main()
