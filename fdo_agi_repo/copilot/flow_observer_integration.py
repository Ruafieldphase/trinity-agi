#!/usr/bin/env python3
"""
Flow Observer Integration: Desktop 활동과 Flow Theory 통합
사용자의 실제 활동을 관찰하고 흐름 상태를 감지합니다.

흐름 상태 감지:
1. 집중 상태 (Flow): 한 프로세스/파일에 장시간 몰입
2. 전환 상태 (Transition): 빠른 전환, 탐색 중
3. 정체 상태 (Stagnation): 활동 없음, 막힘

+ Perspective Theory 통합:
- Observer Mode: 데이터 흐름을 관찰 (파동 관점)
- Walker Mode: 데이터 위를 걷기 (입자 관점)
- Fear to Depth: 두려움 감지 및 깊이 매핑
- Auto Perspective Switch: 막히면 자동 관점 전환

Author: Copilot's Hippocampus
Date: 2025-11-06
Updated: 2025-11-06 (Perspective Theory Integration)
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import Counter

# Perspective Theory import
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from copilot.perspective_theory import PerspectiveSwitcher
    PERSPECTIVE_AVAILABLE = True
except ImportError:
    PERSPECTIVE_AVAILABLE = False
    print("⚠️ Perspective Theory not available. Running without perspective switching.")

# Social Fear Analyzer import
try:
    from copilot.social_fear_information_theory import SocialFearAnalyzer
    SOCIAL_FEAR_AVAILABLE = True
except ImportError:
    SOCIAL_FEAR_AVAILABLE = False
    print("⚠️ Social Fear Analyzer not available. Running without social context.")


@dataclass
class FlowState:
    """현재 흐름 상태"""
    state: str  # 'flow', 'transition', 'stagnation', 'fixation', 'unknown', 'observer_mode', 'walker_mode'
    confidence: float  # 0.0 ~ 1.0
    context: Dict  # 추가 컨텍스트
    timestamp: str
    perspective: Optional[str] = None  # 'observer', 'walker', None
    fear_level: Optional[float] = None  # 0.0 ~ 1.0 (두려움 → 깊이)
    loop_type: Optional[str] = None  # 'open', 'closed' (열린 루프 vs 닫힌 루프)
    social_context: Optional[Dict] = None  # 사회적 맥락 (비교, 투영, 분노)


class FlowObserver:
    """Desktop 활동을 관찰하고 흐름 상태를 감지"""
    
    def __init__(self, telemetry_dir: str = "outputs/telemetry"):
        self.telemetry_dir = Path(telemetry_dir)
        self.flow_threshold_minutes = 15  # 15분 이상 집중하면 flow
        self.transition_window_minutes = 5  # 5분 내 빠른 전환
        self.stagnation_threshold_minutes = 30  # 30분 이상 활동 없으면 정체
        
        # Perspective Theory 통합
        self.perspective_switcher = None
        if PERSPECTIVE_AVAILABLE:
            self.perspective_switcher = PerspectiveSwitcher()
            print("✅ Perspective Theory enabled")
        
        # Social Fear Analyzer 통합
        self.social_fear_analyzer = None
        if SOCIAL_FEAR_AVAILABLE:
            self.social_fear_analyzer = SocialFearAnalyzer()
            print("✅ Social Fear Analyzer enabled")
        
        self.current_perspective = None  # 'observer' or 'walker'
        self.perspective_switch_count = 0
        self.last_perspective_switch = None
        
    def analyze_recent_activity(self, hours: int = 1) -> FlowState:
        """
        최근 활동을 분석하여 현재 흐름 상태를 판단
        
        Args:
            hours: 분석할 시간 범위 (기본 1시간)
            
        Returns:
            FlowState: 현재 흐름 상태
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        records = self._load_telemetry_records(start_time, end_time)
        
        if not records:
            return FlowState(
                state='unknown',
                confidence=0.0,
                context={'reason': 'no_telemetry_data'},
                timestamp=end_time.isoformat()
            )
        
        # 최근 활동 시간 체크
        last_activity = datetime.fromisoformat(
            records[-1]['ts_utc'].replace('Z', '+00:00')
        )
        minutes_since_activity = (end_time - last_activity).total_seconds() / 60
        
        # 정체 상태 체크 → Perspective Switch 제안
        if minutes_since_activity > self.stagnation_threshold_minutes:
            # 두려움 레벨 계산 (정체 시간에 비례)
            fear_level = min(minutes_since_activity / 60.0, 1.0)  # 1시간 = max fear
            
            # Perspective 전환 제안
            if self.perspective_switcher and fear_level > 0.5:
                # 정체 → 관점 전환 필요
                suggested_perspective = self._suggest_perspective_switch('stagnation')
                
                return FlowState(
                    state='stagnation',
                    confidence=0.9,
                    context={
                        'minutes_idle': minutes_since_activity,
                        'last_activity': records[-1],
                        'fear_detected': True,
                        'suggested_action': f'Switch to {suggested_perspective} mode',
                        'explanation': self._get_perspective_explanation(suggested_perspective)
                    },
                    timestamp=end_time.isoformat(),
                    perspective=suggested_perspective,
                    fear_level=fear_level
                )
            
            return FlowState(
                state='stagnation',
                confidence=0.9,
                context={
                    'minutes_idle': minutes_since_activity,
                    'last_activity': records[-1]
                },
                timestamp=end_time.isoformat(),
                fear_level=fear_level
            )
        
        # 활동 패턴 분석
        process_durations = self._analyze_process_durations(records)
        window_switches = self._count_window_switches(records)
        focus_score = self._calculate_focus_score(process_durations, window_switches)
        
        # 🧠 사회적 맥락 분석
        social_context = self._analyze_social_context(records, focus_score, window_switches)
        
        # 🔍 집착(Fixation) 감지
        is_fixation, fixation_fear, loop_type = self._detect_fixation(records, focus_score)
        
        # Perspective 모드 결정
        if self.perspective_switcher:
            perspective_mode = self._determine_perspective_mode(
                focus_score, window_switches, len(process_durations)
            )
        else:
            perspective_mode = None
        
        # 집착 감지 시 자동 관점 전환
        if is_fixation:
            suggested_perspective = 'observer'  # 집착 → Observer로 전환 (바라보기)
            
            return FlowState(
                state='fixation',
                confidence=0.8,
                context={
                    'warning': '⚠️ 집착 패턴 감지: 닫힌 루프로 수렴 중',
                    'explanation': (
                        '집중과 집착은 한 끝 차이입니다.\n'
                        '- 집중(Focus): 열린 루프, 진전 있음, 관찰자 관점\n'
                        '- 집착(Fixation): 닫힌 루프, 반복만, 한 점 수렴\n'
                        '\n💡 해결 방법:\n'
                        '1. 정보이론 기반 노이즈 제거 음악 듣기\n'
                        '2. 짧은 산책 (5-10분)\n'
                        '3. Observer 모드로 전환 (바라보기)'
                    ),
                    'suggested_action': f'Switch to {suggested_perspective} mode',
                    'loop_type': loop_type,
                    'fear_level': fixation_fear
                },
                timestamp=end_time.isoformat(),
                perspective=suggested_perspective,
                fear_level=fixation_fear,
                loop_type=loop_type
            )
    
    def _analyze_social_context(
        self, 
        records: List[Dict],
        focus_score: float,
        window_switches: int
    ) -> Optional[Dict]:
        """
        사회적 맥락 분석: 비교 패턴, 두려움, 투영
        
        Args:
            records: 텔레메트리 기록
            focus_score: 집중도 점수
            window_switches: 윈도우 전환 횟수
            
        Returns:
            사회적 맥락 딕셔너리 또는 None
        """
        if not self.social_fear_analyzer:
            return None
        
        # 활동 패턴에서 비교 이벤트 추정
        # 빠른 전환 = SNS/뉴스 = 비교 증가
        comparison_events = window_switches  # 간소화된 추정
        
        # 집중도가 낮고 전환이 많으면 → 높은 정보 접근성
        information_accessibility = min(1.0, window_switches / 20.0)
        
        # 불확실성: 집중도 역수 (집중 못하면 불확실)
        uncertainty = 1.0 - focus_score
        
        # 생존 위협: 시간대 기반 추정 (늦은 시간 = 높은 위협)
        now = datetime.now()
        hour = now.hour
        if 0 <= hour < 6:  # 새벽
            survival_threat = 0.8
        elif 6 <= hour < 9:  # 아침
            survival_threat = 0.5
        elif 9 <= hour < 18:  # 업무
            survival_threat = 0.6
        elif 18 <= hour < 22:  # 저녁
            survival_threat = 0.4
        else:  # 밤
            survival_threat = 0.7
        
        # 미래 예측 가능성: 집중도와 유사
        future_predictability = focus_score * 0.5  # 낮게 설정
        
        # Social Fear 분석
        try:
            state = self.social_fear_analyzer.analyze_state(
                information_accessibility=information_accessibility,
                comparison_events=comparison_events,
                time_window_hours=len(records) / 60,  # 대략적인 시간
                uncertainty=uncertainty,
                survival_threat=survival_threat,
                future_predictability=future_predictability,
                # 나머지는 기본값 사용
            )
            
            return {
                'anger_intensity': state.anger_intensity,
                'anger_target': state.anger_target,
                'fear_amplification': state.fear_amplification,
                'projection_score': state.projection_score,
                'comparison_frequency': state.comparison_frequency,
                'structural_constraint': state.structural_constraint,
                'interpretation': (
                    f"분노 강도: {state.anger_intensity:.2f}, "
                    f"대상: {state.anger_target}, "
                    f"두려움: {state.fear_amplification:.2f}"
                )
            }
        except Exception as e:
            print(f"⚠️ Social context analysis failed: {e}")
            return None
        
        # Flow 상태 판단 (Perspective 통합)
        if focus_score > 0.7:
            # 한 곳에 집중 → Walker Mode (체험적)
            dominant_process = max(process_durations.items(), key=lambda x: x[1])
            
            state = 'walker_mode' if perspective_mode == 'walker' else 'flow'
            
            context = {
                'dominant_process': dominant_process[0],
                'focus_minutes': dominant_process[1],
                'window_switches': window_switches
            }
            
            if perspective_mode == 'walker':
                context['perspective_explanation'] = (
                    "🚶 Walker Mode: 당신은 데이터 위를 걷고 있습니다. "
                    "높낮이를 체험하며 경로를 추적 중입니다."
                )
            
            return FlowState(
                state=state,
                confidence=focus_score,
                context=context,
                timestamp=end_time.isoformat(),
                perspective=perspective_mode,
                loop_type='open',  # 정상 집중
                social_context=social_context
            )
        elif focus_score > 0.4:
            # 전환 중 → Observer Mode (흐름 관찰)
            state = 'observer_mode' if perspective_mode == 'observer' else 'transition'
            
            context = {
                'process_count': len(process_durations),
                'window_switches': window_switches,
                'top_processes': list(process_durations.keys())[:3]
            }
            
            if perspective_mode == 'observer':
                context['perspective_explanation'] = (
                    "👁️ Observer Mode: 데이터가 흐르는 것을 관찰 중입니다. "
                    "패턴과 주파수를 인식하며 전체 흐름을 파악합니다."
                )
            
            return FlowState(
                state=state,
                confidence=1.0 - focus_score,
                context=context,
                timestamp=end_time.isoformat(),
                perspective=perspective_mode,
                loop_type='open',  # 전환 중
                social_context=social_context
            )
        else:
            # 높은 전환 → ADHD 스타일 vs 실제 산만함 구분
            avg_duration = sum(process_durations.values()) / len(process_durations) if process_durations else 0
            unique_contexts = len(process_durations)
            
            # ADHD 특성: 주의력 과잉 + 다중 맥락 탐색
            if avg_duration > 3.0 and unique_contexts > 3:
                # 카오스 속 질서: 무질서해 보이지만 패턴 발견 중
                return FlowState(
                    state='adhd_hyperfocus_exploration',
                    confidence=0.85,
                    context={
                        'adhd_pattern': True,
                        'attention_surplus': True,  # 주의력 결핍이 아닌 과잉
                        'chaos_order': unique_contexts,  # 카오스 속 질서
                        'window_switches': window_switches,
                        'avg_duration_per_window': round(avg_duration, 2),
                        'learning_mode': 'nonlinear_pattern_finding',  # 비선형 패턴 발견
                        'cognitive_style': 'divergent_thinking'  # 확산적 사고
                    },
                    timestamp=end_time.isoformat(),
                    social_context=social_context
                )
            elif avg_duration > 2.0 and unique_contexts > 2:
                # 탐색적 학습 (일반적)
                return FlowState(
                    state='exploratory_flow',
                    confidence=0.75,
                    context={
                        'exploration_pattern': True,
                        'window_switches': window_switches,
                        'avg_duration_per_window': round(avg_duration, 2),
                        'learning_mode': 'hippocampal'
                    },
                    timestamp=end_time.isoformat(),
                    social_context=social_context
                )
            else:
                # 실제 산만함 (피로, 스트레스 등)
                return FlowState(
                    state='distracted',
                    confidence=0.8,
                    context={
                        'high_switches': window_switches,
                        'fragmented_focus': True,
                        'avg_duration_per_window': round(avg_duration, 2),
                        'possible_causes': ['fatigue', 'stress', 'external_interruptions']
                    },
                    timestamp=end_time.isoformat(),
                    social_context=social_context
                )
    
    def detect_flow_interruptions(self, hours: int = 2) -> List[Dict]:
        """
        흐름 방해 요소 감지
        
        Returns:
            List[Dict]: 방해 이벤트 목록
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        records = self._load_telemetry_records(start_time, end_time)
        interruptions = []
        
        # 윈도우 간 연속적인 집중 시간 계산
        current_focus = None
        focus_start = None
        focus_duration = 0
        
        for i, record in enumerate(records):
            window_title = record.get('window_title', '')
            process = record.get('process_name', '')
            ts = datetime.fromisoformat(record['ts_utc'].replace('Z', '+00:00'))
            
            # 새로운 집중 대상
            focus_key = f"{process}:{window_title}"
            
            if focus_key != current_focus:
                # 이전 집중이 있었고, 충분히 길었다면
                if focus_duration > self.flow_threshold_minutes * 60:
                    # 방해 기록
                    interruptions.append({
                        'type': 'flow_interruption',
                        'from_focus': current_focus,
                        'to_focus': focus_key,
                        'focus_duration_minutes': focus_duration / 60,
                        'timestamp': ts.isoformat()
                    })
                
                # 새 집중 시작
                current_focus = focus_key
                focus_start = ts
                focus_duration = 0
            else:
                # 같은 집중 지속
                if i > 0:
                    prev_ts = datetime.fromisoformat(
                        records[i-1]['ts_utc'].replace('Z', '+00:00')
                    )
                    focus_duration += (ts - prev_ts).total_seconds()
        
        return interruptions
    
    def generate_flow_report(self, hours: int = 24) -> Dict:
        """
        흐름 상태 종합 리포트 생성
        
        Args:
            hours: 분석 기간
            
        Returns:
            Dict: 리포트 데이터
        """
        current_state = self.analyze_recent_activity(hours=1)
        interruptions = self.detect_flow_interruptions(hours=hours)
        
        # 전체 기간 활동 분석
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        records = self._load_telemetry_records(start_time, end_time)
        
        if not records:
            return {
                'generated_at': end_time.isoformat(),
                'analysis_period_hours': hours,
                'current_state': {
                    'state': current_state.state,
                    'confidence': current_state.confidence,
                    'context': current_state.context
                },
                'activity_summary': {
                    'total_records': 0,
                    'activity_ratio': 0.0,
                    'flow_sessions': 0,
                    'total_flow_minutes': 0,
                    'interruptions': 0
                },
                'flow_quality': 'unknown',
                'interruptions': [],
                'recommendations': ['텔레메트리 데이터가 없습니다. Observer를 시작하세요.']
            }
        
        # 흐름 품질 계산
        total_time = (end_time - start_time).total_seconds()
        active_time = len(records) * 5  # 5초 간격으로 샘플링 가정
        activity_ratio = active_time / total_time
        
        process_durations = self._analyze_process_durations(records)
        focus_sessions = [d for d in process_durations.values() 
                         if d > self.flow_threshold_minutes]
        
        # 권장사항 생성
        recommendations = self._generate_recommendations(
            current_state, interruptions, focus_sessions, activity_ratio
        )
        
        # current_state가 None인 경우 기본값 사용
        if current_state:
            current_state_dict = {
                'state': current_state.state,
                'confidence': current_state.confidence,
                'context': current_state.context
            }
            if current_state.social_context:
                current_state_dict['social_context'] = current_state.social_context
        else:
            current_state_dict = {
                'state': 'unknown',
                'confidence': 0.0,
                'context': {'reason': 'insufficient_data'}
            }
        
        return {
            'generated_at': end_time.isoformat(),
            'analysis_period_hours': hours,
            'current_state': current_state_dict,
            'activity_summary': {
                'total_records': len(records),
                'activity_ratio': round(activity_ratio, 2),
                'flow_sessions': len(focus_sessions),
                'total_flow_minutes': sum(focus_sessions),
                'interruptions': len(interruptions)
            },
            'flow_quality': self._assess_flow_quality(
                focus_sessions, interruptions, activity_ratio
            ),
            'interruptions': interruptions[:5],  # 최근 5개
            'recommendations': recommendations
        }
    
    def _load_telemetry_records(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """텔레메트리 파일에서 레코드 로드"""
        records = []
        
        # 날짜별 파일 목록 생성
        current_date = start_time.date()
        end_date = end_time.date()
        
        while current_date <= end_date:
            filename = f"stream_observer_{current_date.isoformat()}.jsonl"
            filepath = self.telemetry_dir / filename
            
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            ts = datetime.fromisoformat(
                                record['ts_utc'].replace('Z', '+00:00')
                            )
                            if start_time <= ts <= end_time:
                                records.append(record)
                        except Exception:
                            continue
            
            current_date += timedelta(days=1)
        
        return sorted(records, key=lambda r: r['ts_utc'])
    
    def _analyze_process_durations(self, records: List[Dict]) -> Dict[str, float]:
        """각 프로세스별 사용 시간 분석 (분 단위)"""
        durations = {}
        
        for i, record in enumerate(records):
            process = record.get('process_name', 'unknown')
            
            if i > 0:
                prev_ts = datetime.fromisoformat(
                    records[i-1]['ts_utc'].replace('Z', '+00:00')
                )
                curr_ts = datetime.fromisoformat(
                    record['ts_utc'].replace('Z', '+00:00')
                )
                duration_minutes = (curr_ts - prev_ts).total_seconds() / 60
                
                # 5분 이상 차이나면 같은 세션이 아님
                if duration_minutes < 5:
                    durations[process] = durations.get(process, 0) + duration_minutes
        
        return durations
    
    def _count_window_switches(self, records: List[Dict]) -> int:
        """윈도우 전환 횟수 카운트"""
        if len(records) < 2:
            return 0
        
        switches = 0
        prev_window = records[0].get('window_title', '')
        
        for record in records[1:]:
            curr_window = record.get('window_title', '')
            if curr_window != prev_window:
                switches += 1
            prev_window = curr_window
        
        return switches
    
    def _calculate_focus_score(
        self, process_durations: Dict[str, float], switches: int
    ) -> float:
        """집중도 점수 계산 (0.0 ~ 1.0)"""
        if not process_durations:
            return 0.0
        
        total_time = sum(process_durations.values())
        if total_time == 0:
            return 0.0
        
        # 가장 많이 사용한 프로세스의 비율
        max_duration = max(process_durations.values())
        focus_ratio = max_duration / total_time
        
        # 전환 페널티
        switch_penalty = min(switches / 20.0, 0.5)  # 최대 0.5 감점
        
        score = focus_ratio - switch_penalty
        return max(0.0, min(1.0, score))
    
    def _assess_flow_quality(
        self, focus_sessions: List[float], 
        interruptions: List[Dict], 
        activity_ratio: float
    ) -> str:
        """전체 흐름 품질 평가"""
        if not focus_sessions:
            return 'poor'
        
        avg_flow_minutes = sum(focus_sessions) / len(focus_sessions)
        interruption_rate = len(interruptions) / len(focus_sessions) if focus_sessions else 0
        
        if avg_flow_minutes > 45 and interruption_rate < 0.5 and activity_ratio > 0.5:
            return 'excellent'
        elif avg_flow_minutes > 30 and interruption_rate < 1.0:
            return 'good'
        elif avg_flow_minutes > 15:
            return 'fair'
        else:
            return 'poor'
    
    def _generate_recommendations(
        self, 
        current_state: Optional[FlowState],
        interruptions: List[Dict],
        focus_sessions: List[float],
        activity_ratio: float
    ) -> List[str]:
        """상황별 권장사항 생성"""
        recs = []
        
        # current_state가 None인 경우
        if not current_state:
            recs.append('⚠️ 활동 데이터가 부족합니다.')
            recs.append('💡 작업을 시작하고 일정 시간 후 다시 확인해보세요.')
            return recs
        
        # 현재 상태 기반
        if current_state.state == 'stagnation':
            recs.append('🚨 30분 이상 활동이 없습니다. 작은 작업부터 시작해보세요.')
            recs.append('💡 5분 타이머를 설정하고 간단한 작업 하나만 완료해보세요.')
        
        elif current_state.state == 'distracted':
            recs.append('⚠️ 집중력이 분산되어 있습니다.')
            recs.append('💡 알림을 끄고 한 가지 작업에만 집중해보세요.')
        
        elif current_state.state == 'flow':
            recs.append('✅ 좋은 흐름입니다! 이 상태를 유지하세요.')
            recs.append('💧 1시간에 한 번씩 잠깐 쉬어가세요.')
        
        # 방해 빈도 기반
        if len(interruptions) > 5:
            recs.append(f'⚠️ {len(interruptions)}번의 흐름 방해가 있었습니다.')
            recs.append('💡 방해 요소를 최소화할 수 있는 환경을 만들어보세요.')
        
        # 활동 비율 기반
        if activity_ratio < 0.3:
            recs.append('⚠️ 활동 시간이 부족합니다.')
            recs.append('💡 작업 시간을 블록으로 나누어 집중해보세요.')
        
        # 집중 세션 기반
        if not focus_sessions:
            recs.append('❌ 집중 세션이 없었습니다.')
            recs.append('💡 타이머를 활용하여 15분 집중 세션을 시작해보세요.')
        
        return recs if recs else ['👍 계속 좋은 흐름을 유지하세요!']
    
    def _suggest_perspective_switch(self, current_state: str) -> str:
        """
        현재 상태에 따라 추천 관점 제시
        
        Args:
            current_state: 'stagnation', 'distracted' 등
            
        Returns:
            str: 'observer' or 'walker'
        """
        if current_state == 'stagnation':
            # 정체 → Walker로 전환 (직접 체험하며 돌파)
            return 'walker'
        elif current_state == 'distracted':
            # 산만 → Observer로 전환 (흐름 관찰하며 패턴 파악)
            return 'observer'
        else:
            # 기본: 현재와 반대로
            return 'observer' if self.current_perspective == 'walker' else 'walker'
    
    def _detect_fixation(
        self, records: List[Dict], focus_score: float
    ) -> Tuple[bool, Optional[float], Optional[str]]:
        """
        집착(Fixation) 감지: 닫힌 루프로 수렴하는 패턴
        
        집중(Focus)과 집착(Fixation)의 차이:
        - 집중: 열린 루프, 관찰자 관점 유지, 진전 있음
        - 집착: 닫힌 루프, 한 점 수렴, 진전 없이 반복
        
        감지 방법:
        1. 같은 파일/프로세스를 반복적으로 전환 (루프)
        2. 진전 없이 오래 머무름 (수렴)
        3. 두려움 신호 동반 (창 전환 패턴)
        
        Args:
            records: 활동 레코드
            focus_score: 집중 점수
            
        Returns:
            (is_fixation, fear_level, loop_type)
        """
        if len(records) < 10:
            return False, None, 'open'
        
        # 최근 30분 활동만 분석
        recent_records = records[-60:]  # 5초 간격 × 60 = 5분
        
        # 1. 반복 패턴 감지 (같은 프로세스/파일 왔다갔다)
        process_sequence = [r.get('process_name', '') for r in recent_records]
        window_sequence = [r.get('window_title', '') for r in recent_records]
        
        # 연속된 짧은 전환 (< 10초)
        rapid_switches = 0
        for i in range(1, len(process_sequence)):
            if process_sequence[i] != process_sequence[i-1]:
                rapid_switches += 1
        
        switch_rate = rapid_switches / len(recent_records)
        
        # 2. 유니크한 컨텍스트 개수 (닫힌 루프는 2-3개만 왔다갔다)
        unique_processes = len(set(process_sequence))
        unique_windows = len(set(window_sequence))
        
        # 3. 진전 없이 반복 (같은 파일/창을 계속 열고 닫음)
        # 예: VS Code → Browser → VS Code → Browser (반복)
        if unique_processes <= 3 and switch_rate > 0.3:
            # 빠른 전환 + 적은 컨텍스트 = 집착 가능성
            fear_level = min(switch_rate * 2, 1.0)
            
            return True, fear_level, 'closed'
        
        # 4. 높은 집중도 + 낮은 다양성 = 집착 가능성
        if focus_score > 0.85 and unique_processes <= 2:
            # 한 곳에만 너무 오래 (두려움 회피?)
            fear_level = (focus_score - 0.85) / 0.15  # 0.85~1.0 → 0~1
            
            return True, fear_level, 'closed'
        
        # 정상 집중
        return False, None, 'open'
    
    def _determine_perspective_mode(
        self, focus_score: float, switches: int, context_count: int
    ) -> Optional[str]:
        """
        활동 패턴으로부터 적절한 관점 모드 결정
        
        Args:
            focus_score: 집중도 점수
            switches: 윈도우 전환 횟수
            context_count: 고유 컨텍스트 수
            
        Returns:
            'observer', 'walker', or None
        """
        if focus_score > 0.7:
            # 높은 집중 → Walker (체험적)
            return 'walker'
        elif switches > 10 or context_count > 5:
            # 많은 전환 → Observer (흐름 관찰)
            return 'observer'
        else:
            return None
    
    def _get_perspective_explanation(self, perspective: str) -> str:
        """관점 전환 설명"""
        if perspective == 'observer':
            return (
                "👁️ Observer Mode로 전환하세요:\n"
                "- 데이터 흐름을 파동처럼 관찰\n"
                "- 패턴과 주파수 인식\n"
                "- 전체적인 흐름 파악\n"
                "- 예: 로그를 쭉 읽으며 패턴 발견"
            )
        else:  # walker
            return (
                "🚶 Walker Mode로 전환하세요:\n"
                "- 데이터 위를 직접 걷기\n"
                "- 높낮이를 체험하며 이동\n"
                "- 경로를 추적하고 기록\n"
                "- 예: 코드를 직접 실행하며 디버깅"
            )


def main():
    """테스트 실행"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='Flow Observer Integration')
    parser.add_argument('--json', action='store_true', help='Output in JSON format for PowerShell integration')
    parser.add_argument('--hours', type=float, default=1, help='Hours to analyze (default: 1)')
    args = parser.parse_args()
    
    observer = FlowObserver()
    
    if args.json:
        # PowerShell 통합을 위한 간단한 JSON 출력
        current = observer.analyze_recent_activity(hours=args.hours)
        output = {
            "flow_state": current.state if current else "unknown",
            "confidence": round(current.confidence, 2) if current else 0.0,
            "perspective": current.perspective if current and current.perspective else "neutral",
            "fear_level": round(current.fear_level, 2) if current and current.fear_level is not None else 0.0,
            "timestamp": datetime.now().isoformat()
        }
        print(json.dumps(output, ensure_ascii=False))
        return
    
    # 기존 human-readable 출력
    print("🌊 Flow Observer Integration Test")
    print("✨ With Perspective Theory\n")
    
    # 현재 상태 분석
    print("📊 Current Flow State (last 1h):")
    current = observer.analyze_recent_activity(hours=1)
    if current:
        print(f"  State: {current.state}")
        print(f"  Confidence: {current.confidence:.2f}")
        if current.perspective:
            print(f"  Perspective: {current.perspective}")
        if current.fear_level is not None:
            print(f"  Fear Level: {current.fear_level:.2f}")
        if current.social_context:
            print(f"  🧠 Social Context:")
            print(f"    Anger: {current.social_context['anger_intensity']:.2f} → {current.social_context['anger_target']}")
            print(f"    Fear: {current.social_context['fear_amplification']:.2f}")
            print(f"    Projection: {current.social_context['projection_score']:.2f}")
        print(f"  Context: {json.dumps(current.context, indent=2)}\n")
    else:
        print("  ⚠️ No activity data in the last 1 hour\n")
    
    # 방해 요소 감지
    print("⚠️ Flow Interruptions (last 2h):")
    interruptions = observer.detect_flow_interruptions(hours=2)
    for intr in interruptions[:3]:
        print(f"  - {intr['type']}: {intr.get('focus_duration_minutes', 0):.1f}min")
    print()
    
    # 종합 리포트
    print("📋 Comprehensive Flow Report (last 24h):")
    report = observer.generate_flow_report(hours=24)
    print(f"  Flow Quality: {report['flow_quality']}")
    print(f"  Flow Sessions: {report['activity_summary']['flow_sessions']}")
    print(f"  Total Flow Time: {report['activity_summary']['total_flow_minutes']:.1f}min")
    print("\n💡 Recommendations:")
    for rec in report['recommendations']:
        print(f"  {rec}")
    
    # JSON 저장
    output_path = Path('outputs/flow_observer_report_latest.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Report saved: {output_path}")


if __name__ == '__main__':
    main()
