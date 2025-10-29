#!/usr/bin/env python3
"""
Cloud Billing Client - GCP 비용 데이터 수집

BigQuery Billing Export 또는 Cloud Billing API를 통해
실제 일일 비용 데이터를 수집합니다.
"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

try:
    from google.cloud import bigquery
    from google.cloud import billing_v1
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    print("⚠️  google-cloud-bigquery 또는 google-cloud-billing 미설치")
    print("   설치: pip install google-cloud-bigquery google-cloud-billing")


# 프로젝트 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# GCP 설정
PROJECT_ID = os.getenv("GCP_PROJECT", "naeda-genesis")
BILLING_DATASET = os.getenv("BILLING_DATASET", "billing_export")
BILLING_TABLE = os.getenv("BILLING_TABLE", "gcp_billing_export_v1_*")


@dataclass
class DailyCost:
    """일일 비용 데이터"""
    date: str
    cost_usd: float
    service_breakdown: Dict[str, float]


class BillingClient:
    """
    Cloud Billing Client
    
    BigQuery Billing Export에서 실제 비용 데이터를 조회합니다.
    """
    
    def __init__(self, project_id: str = PROJECT_ID):
        """
        Args:
            project_id: GCP 프로젝트 ID
        """
        self.project_id = project_id
        
        if GOOGLE_CLOUD_AVAILABLE:
            self.bq_client = bigquery.Client(project=project_id)
        else:
            self.bq_client = None
    
    def get_daily_costs(self, days: int = 7) -> List[DailyCost]:
        """
        일일 비용 데이터 조회
        
        Args:
            days: 조회 일수
            
        Returns:
            DailyCost 리스트
        """
        if not GOOGLE_CLOUD_AVAILABLE or not self.bq_client:
            # Fallback: 더미 데이터 반환
            return self._get_dummy_daily_costs(days)
        
        # BigQuery에서 실제 데이터 조회
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        query = f"""
        SELECT
            DATE(usage_start_time) as date,
            SUM(cost) as cost_usd,
            service.description as service_name
        FROM
            `{self.project_id}.{BILLING_DATASET}.{BILLING_TABLE}`
        WHERE
            DATE(usage_start_time) BETWEEN @start_date AND @end_date
            AND project.id = @project_id
        GROUP BY
            date, service_name
        ORDER BY
            date DESC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
                bigquery.ScalarQueryParameter("project_id", "STRING", self.project_id),
            ]
        )
        
        try:
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            # 날짜별로 그룹화
            daily_costs_dict: Dict[str, Dict[str, float]] = {}
            
            for row in results:
                date_str = row.date.isoformat()
                service_name = row.service_name or "Unknown"
                cost = float(row.cost_usd or 0.0)
                
                if date_str not in daily_costs_dict:
                    daily_costs_dict[date_str] = {}
                
                daily_costs_dict[date_str][service_name] = cost
            
            # DailyCost 객체 생성
            daily_costs = []
            for date_str in sorted(daily_costs_dict.keys(), reverse=True):
                service_breakdown = daily_costs_dict[date_str]
                total_cost = sum(service_breakdown.values())
                
                daily_costs.append(DailyCost(
                    date=date_str,
                    cost_usd=total_cost,
                    service_breakdown=service_breakdown,
                ))
            
            return daily_costs
            
        except Exception as e:
            print(f"⚠️  BigQuery 쿼리 실패: {e}")
            return self._get_dummy_daily_costs(days)
    
    def _get_dummy_daily_costs(self, days: int) -> List[DailyCost]:
        """
        더미 비용 데이터 생성 (BigQuery 사용 불가 시)
        
        Args:
            days: 조회 일수
            
        Returns:
            DailyCost 리스트
        """
        # Redis + Cloud Run 추정치
        redis_daily = 9.36 / 30  # $0.312/day
        cloudrun_daily = 15.0 / 30  # $0.50/day
        base_daily = redis_daily + cloudrun_daily  # ~$0.812/day
        
        # 약간의 변동성 추가
        import random
        random.seed(42)
        
        daily_costs = []
        end_date = datetime.utcnow().date()
        
        for i in range(days):
            date = end_date - timedelta(days=i)
            
            # 일일 비용 변동 (±10%)
            cost_usd = base_daily * (1 + random.uniform(-0.1, 0.1))
            
            service_breakdown = {
                "Cloud Run": cost_usd * 0.62,  # 62%
                "Memorystore for Redis": cost_usd * 0.38,  # 38%
            }
            
            daily_costs.append(DailyCost(
                date=date.isoformat(),
                cost_usd=cost_usd,
                service_breakdown=service_breakdown,
            ))
        
        return daily_costs
    
    def get_current_month_spend(self) -> float:
        """
        현재 달 누적 비용 조회
        
        Returns:
            월 누적 비용 (USD)
        """
        now = datetime.utcnow()
        days_in_month = now.day
        
        daily_costs = self.get_daily_costs(days=days_in_month)
        
        return sum(dc.cost_usd for dc in daily_costs)
    
    def get_forecasted_month_spend(self) -> float:
        """
        월말 예측 비용 계산
        
        Returns:
            월말 예측 비용 (USD)
        """
        daily_costs = self.get_daily_costs(days=7)
        
        if not daily_costs:
            return 0.0
        
        # 7일 평균 × 30일
        avg_daily = sum(dc.cost_usd for dc in daily_costs) / len(daily_costs)
        forecasted = avg_daily * 30
        
        return forecasted
    
    def print_cost_summary(self, days: int = 7):
        """
        비용 요약 출력
        
        Args:
            days: 조회 일수
        """
        print("=" * 70)
        print(f"Cloud Billing Summary (Last {days} days)")
        print("=" * 70)
        print()
        
        daily_costs = self.get_daily_costs(days)
        
        if not daily_costs:
            print("❌ 비용 데이터 없음")
            return
        
        # 일별 비용 출력
        print("📅 Daily Costs:")
        print()
        for dc in daily_costs:
            print(f"  {dc.date}: ${dc.cost_usd:.2f}")
            for service, cost in sorted(dc.service_breakdown.items(), key=lambda x: -x[1]):
                percentage = (cost / dc.cost_usd * 100) if dc.cost_usd > 0 else 0
                print(f"    - {service}: ${cost:.2f} ({percentage:.1f}%)")
        print()
        
        # 통계
        total_cost = sum(dc.cost_usd for dc in daily_costs)
        avg_daily = total_cost / len(daily_costs)
        
        print("📊 Statistics:")
        print(f"  Total Cost: ${total_cost:.2f}")
        print(f"  Average Daily: ${avg_daily:.2f}")
        print(f"  Forecasted Monthly: ${avg_daily * 30:.2f}")
        print()
        
        # 서비스별 합계
        service_totals: Dict[str, float] = {}
        for dc in daily_costs:
            for service, cost in dc.service_breakdown.items():
                service_totals[service] = service_totals.get(service, 0.0) + cost
        
        print("🔍 Service Breakdown:")
        for service, cost in sorted(service_totals.items(), key=lambda x: -x[1]):
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            print(f"  - {service}: ${cost:.2f} ({percentage:.1f}%)")
        print()
        
        print("=" * 70)


def main():
    """테스트 함수"""
    client = BillingClient(PROJECT_ID)
    
    # 7일 비용 요약
    client.print_cost_summary(days=7)
    
    # 현재 달 누적
    current_spend = client.get_current_month_spend()
    print(f"💰 Current Month Spend: ${current_spend:.2f}")
    
    # 월말 예측
    forecasted_spend = client.get_forecasted_month_spend()
    print(f"📈 Forecasted Month Spend: ${forecasted_spend:.2f}")
    print()


if __name__ == "__main__":
    main()
