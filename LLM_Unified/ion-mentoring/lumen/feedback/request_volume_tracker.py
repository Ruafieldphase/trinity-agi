"""
Request Volume Tracker

Tracks request volume over time to:
1. Monitor growth trends
2. Identify breakeven points
3. Trigger ROI milestone alerts
4. Support strategic decision-making

Economic Milestones:
- Breakeven: 1,541 req/day (46,222/month)
- Profitability: 1,600 req/day (ROI > 0%)
- Excellence: 9,260 req/day (ROI > 500%)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


# Economic thresholds (based on ROI_ANALYSIS.md)
REDIS_MONTHLY_COST = 9.36  # USD
GEMINI_COST_PER_REQUEST = 0.0003375  # USD (Flash 1.5 actual pricing)
CACHE_HIT_RATE = 0.60  # 60% average

# Volume milestones
BREAKEVEN_MONTHLY_REQUESTS = 46222  # ROI = 0%
BREAKEVEN_DAILY_REQUESTS = 1541

PROFITABILITY_MONTHLY_REQUESTS = 48000  # ROI > 0%
PROFITABILITY_DAILY_REQUESTS = 1600

EXCELLENCE_MONTHLY_REQUESTS = 277800  # ROI > 500%
EXCELLENCE_DAILY_REQUESTS = 9260


@dataclass
class VolumeSnapshot:
    """Single point-in-time volume measurement"""
    timestamp: str
    daily_requests: int
    monthly_projection: int
    roi_percent: float
    milestone: str  # "STARTUP" | "GROWTH" | "BREAKEVEN" | "PROFITABLE" | "EXCELLENT"


@dataclass
class VolumeTrend:
    """Volume trend analysis over time period"""
    current_snapshot: VolumeSnapshot
    previous_snapshot: Optional[VolumeSnapshot]
    
    # Trend metrics
    daily_growth_rate: float  # % change in daily requests
    monthly_growth_rate: float  # % change in monthly projection
    days_to_breakeven: Optional[int]  # Estimated days until breakeven
    days_to_profitability: Optional[int]  # Estimated days until profitable
    
    # Status
    trend_direction: str  # "INCREASING" | "STABLE" | "DECREASING"
    alert_level: str  # "NONE" | "INFO" | "WARNING" | "CRITICAL"
    alert_message: str


class RequestVolumeTracker:
    """
    Tracks request volume and provides economic insights
    """
    
    def __init__(self, project_id: str, service_name: str):
        """
        Args:
            project_id: GCP project ID
            service_name: Cloud Run service name
        """
        self.project_id = project_id
        self.service_name = service_name
        
        # State file paths
        project_root = Path(__file__).resolve().parents[2]
        self.state_dir = project_root / "outputs"
        self.state_dir.mkdir(exist_ok=True)
        
        self.snapshot_file = self.state_dir / "volume_snapshots.json"
        self.trend_file = self.state_dir / "volume_trend.json"
    
    def calculate_roi_from_volume(self, daily_requests: int) -> float:
        """
        Calculate ROI based on request volume
        
        Args:
            daily_requests: Daily request count
            
        Returns:
            ROI percentage
        """
        monthly_requests = daily_requests * 30
        cached_requests = monthly_requests * CACHE_HIT_RATE
        savings = cached_requests * GEMINI_COST_PER_REQUEST
        net_benefit = savings - REDIS_MONTHLY_COST
        
        if REDIS_MONTHLY_COST == 0:
            return 0.0
        
        roi_percent = (net_benefit / REDIS_MONTHLY_COST) * 100
        return roi_percent
    
    def classify_milestone(self, daily_requests: int) -> str:
        """
        Classify current volume milestone
        
        Args:
            daily_requests: Daily request count
            
        Returns:
            Milestone name
        """
        if daily_requests >= EXCELLENCE_DAILY_REQUESTS:
            return "EXCELLENT"
        elif daily_requests >= PROFITABILITY_DAILY_REQUESTS:
            return "PROFITABLE"
        elif daily_requests >= BREAKEVEN_DAILY_REQUESTS:
            return "BREAKEVEN"
        elif daily_requests >= 100:
            return "GROWTH"
        else:
            return "STARTUP"
    
    def create_snapshot(self, daily_requests: int) -> VolumeSnapshot:
        """
        Create current volume snapshot
        
        Args:
            daily_requests: Current daily request count
            
        Returns:
            VolumeSnapshot object
        """
        monthly_projection = daily_requests * 30
        roi_percent = self.calculate_roi_from_volume(daily_requests)
        milestone = self.classify_milestone(daily_requests)
        
        snapshot = VolumeSnapshot(
            timestamp=datetime.utcnow().isoformat(),
            daily_requests=daily_requests,
            monthly_projection=monthly_projection,
            roi_percent=roi_percent,
            milestone=milestone,
        )
        
        return snapshot
    
    def save_snapshot(self, snapshot: VolumeSnapshot):
        """
        Save snapshot to history
        
        Args:
            snapshot: VolumeSnapshot to save
        """
        # Load existing snapshots
        snapshots = []
        if self.snapshot_file.exists():
            with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                snapshots = data.get("snapshots", [])
        
        # Add new snapshot
        snapshots.append(asdict(snapshot))
        
        # Keep last 90 days only
        cutoff = (datetime.utcnow() - timedelta(days=90)).isoformat()
        snapshots = [s for s in snapshots if s["timestamp"] >= cutoff]
        
        # Save
        with open(self.snapshot_file, 'w', encoding='utf-8') as f:
            json.dump({"snapshots": snapshots}, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved volume snapshot: {snapshot.daily_requests} req/day")
    
    def load_previous_snapshot(self) -> Optional[VolumeSnapshot]:
        """
        Load most recent previous snapshot (from yesterday or earlier)
        
        Returns:
            Previous VolumeSnapshot or None
        """
        if not self.snapshot_file.exists():
            return None
        
        try:
            with open(self.snapshot_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                snapshots = data.get("snapshots", [])
            
            if len(snapshots) < 2:
                return None
            
            # Get second-to-last snapshot (last is current)
            prev_dict = snapshots[-2]
            
            # Convert dict to VolumeSnapshot
            prev_snapshot = VolumeSnapshot(**prev_dict)
            
            return prev_snapshot
        
        except Exception as e:
            logger.error(f"Failed to load previous snapshot: {e}")
            return None
    
    def analyze_trend(self, current: VolumeSnapshot, previous: Optional[VolumeSnapshot]) -> VolumeTrend:
        """
        Analyze volume trend
        
        Args:
            current: Current snapshot
            previous: Previous snapshot (if available)
            
        Returns:
            VolumeTrend object
        """
        # Default values for first run
        daily_growth_rate = 0.0
        monthly_growth_rate = 0.0
        trend_direction = "STABLE"
        alert_level = "INFO"
        alert_message = "Initial volume measurement"
        
        if previous:
            # Calculate growth rates
            if previous.daily_requests > 0:
                daily_growth_rate = ((current.daily_requests - previous.daily_requests) / 
                                    previous.daily_requests) * 100
            
            if previous.monthly_projection > 0:
                monthly_growth_rate = ((current.monthly_projection - previous.monthly_projection) / 
                                      previous.monthly_projection) * 100
            
            # Determine trend direction
            if daily_growth_rate > 5:
                trend_direction = "INCREASING"
            elif daily_growth_rate < -5:
                trend_direction = "DECREASING"
            else:
                trend_direction = "STABLE"
            
            # Generate alerts
            alert_level, alert_message = self._generate_alert(
                current, previous, daily_growth_rate, monthly_growth_rate
            )
        
        # Estimate days to milestones
        days_to_breakeven = self._estimate_days_to_target(
            current.daily_requests, BREAKEVEN_DAILY_REQUESTS, daily_growth_rate
        )
        
        days_to_profitability = self._estimate_days_to_target(
            current.daily_requests, PROFITABILITY_DAILY_REQUESTS, daily_growth_rate
        )
        
        trend = VolumeTrend(
            current_snapshot=current,
            previous_snapshot=previous,
            daily_growth_rate=daily_growth_rate,
            monthly_growth_rate=monthly_growth_rate,
            days_to_breakeven=days_to_breakeven,
            days_to_profitability=days_to_profitability,
            trend_direction=trend_direction,
            alert_level=alert_level,
            alert_message=alert_message,
        )
        
        return trend
    
    def _estimate_days_to_target(
        self, 
        current: int, 
        target: int, 
        growth_rate: float
    ) -> Optional[int]:
        """
        Estimate days to reach target volume
        
        Args:
            current: Current daily requests
            target: Target daily requests
            growth_rate: Daily growth rate (%)
            
        Returns:
            Estimated days or None if unreachable
        """
        if current >= target:
            return 0
        
        if growth_rate <= 0:
            return None  # Not growing
        
        # Exponential growth: current * (1 + rate)^days = target
        # days = log(target / current) / log(1 + rate)
        import math
        
        try:
            days = math.log(target / current) / math.log(1 + (growth_rate / 100))
            return int(days)
        except:
            return None
    
    def _generate_alert(
        self,
        current: VolumeSnapshot,
        previous: VolumeSnapshot,
        daily_growth: float,
        monthly_growth: float,
    ) -> Tuple[str, str]:
        """
        Generate alert based on volume changes
        
        Args:
            current: Current snapshot
            previous: Previous snapshot
            daily_growth: Daily growth rate (%)
            monthly_growth: Monthly growth rate (%)
            
        Returns:
            (alert_level, alert_message)
        """
        # Milestone transitions
        if current.milestone != previous.milestone:
            if current.milestone == "BREAKEVEN":
                return ("INFO", f"🎉 Breakeven milestone reached! ({current.daily_requests} req/day)")
            elif current.milestone == "PROFITABLE":
                return ("INFO", f"🚀 Profitability milestone reached! (ROI: {current.roi_percent:.1f}%)")
            elif current.milestone == "EXCELLENT":
                return ("INFO", f"⭐ Excellence milestone reached! (ROI: {current.roi_percent:.1f}%)")
        
        # Rapid growth
        if daily_growth > 50:
            return ("INFO", f"📈 Rapid growth: +{daily_growth:.1f}% ({current.daily_requests} req/day)")
        
        # Significant decline
        if daily_growth < -20:
            return ("WARNING", f"📉 Significant decline: {daily_growth:.1f}% ({current.daily_requests} req/day)")
        
        # Sustained low volume
        if current.daily_requests < 100 and previous.daily_requests < 100:
            return ("WARNING", f"⚠️ Sustained low volume: {current.daily_requests} req/day (consider optimization)")
        
        # Normal operation
        if daily_growth > 0:
            return ("NONE", f"Volume: {current.daily_requests} req/day (growing +{daily_growth:.1f}%)")
        elif daily_growth < 0:
            return ("NONE", f"Volume: {current.daily_requests} req/day (declining {daily_growth:.1f}%)")
        else:
            return ("NONE", f"Volume: {current.daily_requests} req/day (stable)")
    
    def save_trend(self, trend: VolumeTrend):
        """
        Save trend analysis
        
        Args:
            trend: VolumeTrend to save
        """
        trend_dict = {
            "current_snapshot": asdict(trend.current_snapshot),
            "previous_snapshot": asdict(trend.previous_snapshot) if trend.previous_snapshot else None,
            "daily_growth_rate": trend.daily_growth_rate,
            "monthly_growth_rate": trend.monthly_growth_rate,
            "days_to_breakeven": trend.days_to_breakeven,
            "days_to_profitability": trend.days_to_profitability,
            "trend_direction": trend.trend_direction,
            "alert_level": trend.alert_level,
            "alert_message": trend.alert_message,
        }
        
        with open(self.trend_file, 'w', encoding='utf-8') as f:
            json.dump(trend_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved volume trend: {trend.trend_direction} ({trend.alert_level})")
    
    def track(self, daily_requests: int) -> VolumeTrend:
        """
        Main entry point: Track current volume and analyze trend
        
        Args:
            daily_requests: Current daily request count
            
        Returns:
            VolumeTrend object
        """
        # Create current snapshot
        current = self.create_snapshot(daily_requests)
        
        # Load previous snapshot
        previous = self.load_previous_snapshot()
        
        # Analyze trend
        trend = self.analyze_trend(current, previous)
        
        # Save
        self.save_snapshot(current)
        self.save_trend(trend)
        
        # Log
        logger.info(f"Volume tracked: {current.daily_requests} req/day, ROI: {current.roi_percent:.1f}%")
        logger.info(f"Trend: {trend.trend_direction}, Alert: {trend.alert_message}")
        
        return trend
    
    def generate_report(self, trend: VolumeTrend) -> str:
        """
        Generate volume trend report
        
        Args:
            trend: VolumeTrend object
            
        Returns:
            Markdown report
        """
        current = trend.current_snapshot
        previous = trend.previous_snapshot
        
        # Alert icon
        alert_icons = {
            "NONE": "",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "CRITICAL": "🔴",
        }
        icon = alert_icons.get(trend.alert_level, "")
        
        # Trend icon
        trend_icons = {
            "INCREASING": "📈",
            "STABLE": "➡️",
            "DECREASING": "📉",
        }
        trend_icon = trend_icons.get(trend.trend_direction, "")
        
        report = f"""
## 📊 Request Volume Trend

**Current Volume**: {current.daily_requests} req/day ({current.monthly_projection}/month)
**Milestone**: {current.milestone}
**ROI**: {current.roi_percent:.1f}%

### Trend Analysis {trend_icon}

- **Direction**: {trend.trend_direction}
- **Daily Growth**: {trend.daily_growth_rate:+.1f}%
"""
        
        if previous:
            report += f"- **Previous**: {previous.daily_requests} req/day\n"
        
        report += "\n### Economic Projections\n\n"
        
        if trend.days_to_breakeven is not None:
            report += f"- **Days to Breakeven** ({BREAKEVEN_DAILY_REQUESTS} req/day): {trend.days_to_breakeven} days\n"
        else:
            report += f"- **Days to Breakeven**: Not growing (need {BREAKEVEN_DAILY_REQUESTS - current.daily_requests} more req/day)\n"
        
        if trend.days_to_profitability is not None:
            report += f"- **Days to Profitability** ({PROFITABILITY_DAILY_REQUESTS} req/day): {trend.days_to_profitability} days\n"
        else:
            report += f"- **Days to Profitability**: Not growing (need {PROFITABILITY_DAILY_REQUESTS - current.daily_requests} more req/day)\n"
        
        report += f"\n### Alert {icon}\n\n"
        report += f"{trend.alert_message}\n"
        
        return report
