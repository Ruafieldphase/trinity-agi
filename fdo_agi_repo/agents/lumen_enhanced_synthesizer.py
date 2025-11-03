#!/usr/bin/env python3
"""
lumen_enhanced_synthesizer.py
루멘 (합/合) 강화판 - 페르소나와 대화 컨텍스트 통합

역할: "무엇을 해야 하는가?" - 통합과 조화
- 정(루아)의 관찰 통합
- 반(엘로)의 검증 통합
- 페르소나 모델 학습 통합
- 대화 컨텍스트 분석
- 합(루멘)의 실행 가능한 통찰 생성
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import math

class LumenEnhancedSynthesizer:
    """루멘 (합) 강화판 - 다차원 통합자"""
    
    def __init__(self, lua_path: str, elo_path: str):
        self.lua_path = Path(lua_path)
        self.elo_path = Path(elo_path)
        
        self.lua_data = self._load_json(self.lua_path)
        self.elo_data = self._load_json(self.elo_path)
        
        # 확장 데이터 소스
        self.binoche_persona = self._try_load_persona()
        self.conversation_context = self._try_load_conversations()
        self.ensemble_metrics = self._try_load_ensemble()
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        """JSON 로드 (BOM 처리)"""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        with open(path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    
    def _try_load_persona(self) -> Optional[Dict[str, Any]]:
        """비노슈 페르소나 모델 로드 시도"""
        persona_paths = [
            Path('fdo_agi_repo/outputs/binoche_persona.json'),
            Path('outputs/binoche_persona.json')
        ]
        
        for p in persona_paths:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8-sig') as f:
                        return json.load(f)
                except:
                    pass
        return None
    
    def _try_load_conversations(self) -> Optional[Dict[str, Any]]:
        """대화 컨텍스트 로드 시도"""
        conv_paths = [
            Path('outputs/conversation_timeline_2025-10-27.json'),
            Path('outputs/conversation_analysis_latest.json')
        ]
        
        for p in conv_paths:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8-sig') as f:
                        return json.load(f)
                except:
                    pass
        return None
    
    def _try_load_ensemble(self) -> Optional[Dict[str, Any]]:
        """앙상블 메트릭 로드 시도"""
        ensemble_paths = [
            Path('fdo_agi_repo/outputs/ensemble_success_metrics.json'),
            Path('outputs/ensemble_success_metrics.json')
        ]
        
        for p in ensemble_paths:
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8-sig') as f:
                        return json.load(f)
                except:
                    pass
        return None
    
    def synthesize(self) -> Dict[str, Any]:
        """확장된 정반합 통합"""
        print("🌟 루멘 (합) 강화판 - 다차원 통합 시작")
        print("   합(合): 무엇을 해야 하는가?")
        print()
        
        # 1. 정(正) - 루아의 관찰 요약
        lua_summary = self._summarize_lua()
        print("📋 정(正) - 루아의 관찰:")
        print(f"   이벤트: {lua_summary['total_events']}개")
        print(f"   이벤트 타입: {lua_summary['event_types']}개")
        print(f"   활동 Task: {lua_summary['unique_tasks']}개")
        print()
        
        # 2. 반(反) - 엘로의 검증 요약
        elo_summary = self._summarize_elo()
        print("🔬 반(反) - 엘로의 검증:")
        print(f"   엔트로피: {elo_summary['entropy']:.3f}")
        print(f"   정보 밀도: {elo_summary['information_density']:.1%}")
        print(f"   이상치: {elo_summary['anomaly_count']}건")
        print()
        
        # 3. 🆕 페르소나 분석
        persona_summary = self._analyze_persona()
        if persona_summary:
            print("🎭 페르소나 분석:")
            print(f"   모델 타입: {persona_summary.get('model_type', 'N/A')}")
            print(f"   학습 패턴: {persona_summary.get('learned_patterns', 0)}개")
            print()
        
        # 4. 🆕 대화 컨텍스트 분석
        conversation_summary = self._analyze_conversations()
        if conversation_summary:
            print("💬 대화 컨텍스트:")
            print(f"   대화 세션: {conversation_summary.get('session_count', 0)}개")
            print(f"   주요 주제: {', '.join(conversation_summary.get('topics', [])[:3])}")
            print()
        
        # 5. 🆕 확장 정보이론 메트릭
        extended_metrics = self._calculate_extended_metrics()
        print("📊 확장 메트릭:")
        print(f"   상호정보량: {extended_metrics['mutual_information']:.3f} bits")
        print(f"   복잡도 지수: {extended_metrics['complexity_index']:.3f}")
        print()
        
        # 6. 합(合) - 통합 통찰
        insights = self._generate_enhanced_insights(
            lua_summary, elo_summary, persona_summary, 
            conversation_summary, extended_metrics
        )
        print("💡 합(合) - 통합 통찰:")
        for insight in insights:
            priority = insight['priority'].upper()
            print(f"   [{priority}] {insight['message']}")
        print()
        
        # 7. 실행 가능한 권장사항
        recommendations = self._generate_enhanced_recommendations(insights)
        print("✅ 실행 가능한 권장사항:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        print()
        
        # 결과 취합
        result = {
            'synthesizer': 'lumen_enhanced',
            'version': '2.0',
            'persona': '합(合)',
            'role': '다차원 통합',
            'philosophy': '무엇을 해야 하는가?',
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'lua': str(self.lua_path),
                'elo': str(self.elo_path),
                'binoche_persona': bool(self.binoche_persona),
                'conversation_context': bool(self.conversation_context),
                'ensemble_metrics': bool(self.ensemble_metrics)
            },
            'synthesis': {
                'lua_summary': lua_summary,
                'elo_summary': elo_summary,
                'persona_summary': persona_summary,
                'conversation_summary': conversation_summary,
                'extended_metrics': extended_metrics,
                'insights': insights,
                'recommendations': recommendations
            },
            'dialectic': {
                'thesis': '정(正) - 관찰된 시스템 상태',
                'antithesis': '반(反) - 검증된 품질 이슈',
                'synthesis': '합(合) - 실행 가능한 개선 방향',
                'extension': '확장(擴) - 페르소나와 대화 통합'
            }
        }
        
        return result
    
    def _summarize_lua(self) -> Dict[str, Any]:
        """루아 관찰 요약"""
        quality_metrics = self.lua_data.get('quality_metrics') or {}
        latency_metrics = self.lua_data.get('latency_metrics') or {}
        
        return {
            'total_events': self.lua_data.get('events_in_window', 0),
            'event_types': len(self.lua_data.get('event_types', {})),
            'unique_tasks': self.lua_data.get('unique_tasks', 0),
            'quality_count': quality_metrics.get('count', 0),
            'quality_avg': quality_metrics.get('average', 0),
            'latency_count': latency_metrics.get('count', 0)
        }
    
    def _summarize_elo(self) -> Dict[str, Any]:
        """엘로 검증 요약"""
        it = self.elo_data.get('information_theory', {})
        return {
            'entropy': it.get('entropy', {}).get('value', 0),
            'entropy_normalized': it.get('entropy', {}).get('normalized', 0),
            'information_density': it.get('information_density', {}).get('value', 0),
            'anomaly_count': len(self.elo_data.get('anomalies', [])),
            'consistency': self.elo_data.get('consistency', {}).get('overall', 'unknown'),
            'verdict': self.elo_data.get('verdict', '')
        }
    
    def _analyze_persona(self) -> Optional[Dict[str, Any]]:
        """페르소나 모델 분석"""
        if not self.binoche_persona:
            return None
        
        patterns = self.binoche_persona.get('learned_patterns', [])
        
        return {
            'model_type': 'binoche_ensemble',
            'learned_patterns': len(patterns),
            'confidence_avg': sum(p.get('confidence', 0) for p in patterns) / len(patterns) if patterns else 0,
            'style_preference': self.binoche_persona.get('style_preference', {}),
            'last_updated': self.binoche_persona.get('last_updated', '')
        }
    
    def _analyze_conversations(self) -> Optional[Dict[str, Any]]:
        """대화 컨텍스트 분석"""
        if not self.conversation_context:
            return None
        
        # 대화 세션 수 추정
        sessions = self.conversation_context.get('sessions', [])
        if not sessions and 'events' in self.conversation_context:
            # 이벤트에서 세션 추정
            sessions = [self.conversation_context]
        
        # 주제 추출
        topics = []
        if 'topics' in self.conversation_context:
            topics = self.conversation_context['topics']
        elif sessions:
            for session in sessions[:5]:  # 최근 5개만
                if 'topic' in session:
                    topics.append(session['topic'])
        
        return {
            'session_count': len(sessions) if sessions else 1,
            'topics': topics[:5],  # 상위 5개
            'total_messages': sum(s.get('message_count', 0) for s in sessions) if sessions else 0
        }
    
    def _calculate_extended_metrics(self) -> Dict[str, Any]:
        """확장 정보이론 메트릭"""
        
        # 1. 상호정보량 (Mutual Information)
        # I(X;Y) = H(X) + H(Y) - H(X,Y)
        entropy = self.elo_data.get('information_theory', {}).get('entropy', {}).get('value', 0)
        
        # 이벤트 타입과 Task 간의 상호정보량 근사
        event_types = len(self.lua_data.get('event_types', {}))
        unique_tasks = self.lua_data.get('unique_tasks', 0)
        
        if event_types > 0 and unique_tasks > 0:
            # 간단한 근사: H(types) + H(tasks) - H(joint)
            h_types = math.log2(event_types)
            h_tasks = math.log2(unique_tasks)
            h_joint = entropy  # 결합 엔트로피 근사
            mutual_info = h_types + h_tasks - h_joint
        else:
            mutual_info = 0
        
        # 2. 복잡도 지수 (Complexity Index)
        # C = H * D * (1 - A)
        # H: 엔트로피, D: 정보밀도, A: 이상치 비율
        info_density = self.elo_data.get('information_theory', {}).get('information_density', {}).get('value', 0)
        anomaly_count = len(self.elo_data.get('anomalies', []))
        total_events = self.lua_data.get('events_in_window', 1)
        anomaly_ratio = anomaly_count / total_events if total_events > 0 else 0
        
        complexity_index = entropy * info_density * (1 - anomaly_ratio)
        
        # 3. 품질-엔트로피 상관관계
        quality_metrics = self.lua_data.get('quality_metrics') or {}
        quality_avg = quality_metrics.get('average', 0)
        quality_entropy_correlation = quality_avg * entropy if quality_avg > 0 else 0
        
        return {
            'mutual_information': mutual_info,
            'complexity_index': complexity_index,
            'quality_entropy_correlation': quality_entropy_correlation,
            'anomaly_ratio': anomaly_ratio
        }
    
    def _generate_enhanced_insights(
        self, 
        lua: Dict, 
        elo: Dict, 
        persona: Optional[Dict],
        conversation: Optional[Dict],
        extended: Dict
    ) -> List[Dict[str, Any]]:
        """확장된 통합 통찰 생성"""
        insights = []
        
        # 기본 통찰 (기존)
        if elo['information_density'] < 0.3:
            insights.append({
                'priority': 'high',
                'category': 'data_quality',
                'message': f"정보 밀도가 낮음 ({elo['information_density']:.1%}). 더 많은 메트릭 수집 필요",
                'source': 'elo',
                'actionable': True
            })
        
        # 🆕 페르소나 기반 통찰
        if persona and persona.get('learned_patterns', 0) > 0:
            confidence = persona.get('confidence_avg', 0)
            if confidence > 0.8:
                insights.append({
                    'priority': 'info',
                    'category': 'persona',
                    'message': f"페르소나 모델 신뢰도 높음 ({confidence:.2f}). 자율 의사결정 가능",
                    'source': 'persona',
                    'actionable': False
                })
            elif confidence < 0.6:
                insights.append({
                    'priority': 'medium',
                    'category': 'persona',
                    'message': f"페르소나 모델 신뢰도 낮음 ({confidence:.2f}). 추가 학습 필요",
                    'source': 'persona',
                    'actionable': True
                })
        
        # 🆕 대화 컨텍스트 기반 통찰
        if conversation:
            session_count = conversation.get('session_count', 0)
            if session_count > 10:
                insights.append({
                    'priority': 'info',
                    'category': 'conversation',
                    'message': f"풍부한 대화 컨텍스트 ({session_count}개 세션). 패턴 학습에 활용 가능",
                    'source': 'conversation',
                    'actionable': True
                })
        
        # 🆕 확장 메트릭 기반 통찰
        if extended['complexity_index'] > 2.0:
            insights.append({
                'priority': 'low',
                'category': 'complexity',
                'message': f"시스템 복잡도 높음 (CI={extended['complexity_index']:.2f}). 단순화 고려",
                'source': 'extended_metrics',
                'actionable': True
            })
        
        if extended['mutual_information'] < 1.0:
            insights.append({
                'priority': 'medium',
                'category': 'correlation',
                'message': f"이벤트-Task 상관관계 약함 (MI={extended['mutual_information']:.2f}). 연결성 강화 필요",
                'source': 'extended_metrics',
                'actionable': True
            })
        
        # 품질 메트릭 부족
        if lua['quality_count'] < lua['total_events'] * 0.5:
            coverage = lua['quality_count'] / lua['total_events'] if lua['total_events'] > 0 else 0
            insights.append({
                'priority': 'medium',
                'category': 'monitoring',
                'message': f"품질 메트릭 커버리지 낮음 ({coverage:.1%}). 평가 강화 필요",
                'source': 'lua',
                'actionable': True
            })
        
        # 이상치 발견
        if elo['anomaly_count'] > 0:
            insights.append({
                'priority': 'medium',
                'category': 'anomaly',
                'message': f"{elo['anomaly_count']}건의 이상치 탐지. 상세 조사 필요",
                'source': 'elo',
                'actionable': True
            })
        
        # 긍정적 신호
        if elo['consistency'] in ['consistent', 'mostly_consistent']:
            insights.append({
                'priority': 'info',
                'category': 'positive',
                'message': "시스템 일관성 양호. 안정적 운영 중",
                'source': 'elo',
                'actionable': False
            })
        
        return insights
    
    def _generate_enhanced_recommendations(self, insights: List[Dict]) -> List[str]:
        """확장된 실행 가능한 권장사항 생성"""
        recommendations = []
        
        for insight in insights:
            if not insight.get('actionable', True):
                continue
            
            if insight['category'] == 'data_quality':
                recommendations.append(
                    "모든 주요 이벤트에 quality/latency 메트릭 추가"
                )
            elif insight['category'] == 'monitoring':
                recommendations.append(
                    "평가(eval) 이벤트 빈도 증가 - 현재 대비 2배"
                )
            elif insight['category'] == 'anomaly':
                recommendations.append(
                    "이상치 원인 분석 및 자동 알림 시스템 구축"
                )
            elif insight['category'] == 'persona':
                if '신뢰도 낮음' in insight['message']:
                    recommendations.append(
                        "비노슈 페르소나 모델 재학습 - 최근 1주일 데이터 활용"
                    )
            elif insight['category'] == 'conversation':
                recommendations.append(
                    "대화 패턴을 페르소나 학습에 통합 - 자동 피드백 루프 구축"
                )
            elif insight['category'] == 'complexity':
                recommendations.append(
                    "이벤트 타입 통합 및 중복 제거로 복잡도 감소"
                )
            elif insight['category'] == 'correlation':
                recommendations.append(
                    "Task-이벤트 매핑 강화 - 명확한 인과관계 정의"
                )
        
        # 중복 제거
        recommendations = list(dict.fromkeys(recommendations))
        
        # 기본 권장사항
        if not recommendations:
            recommendations.append("현재 상태 양호. 지속적인 모니터링 유지")
        
        return recommendations


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="루멘 (합) 강화판 - 페르소나와 대화 통합"
    )
    parser.add_argument(
        '--lua-observation',
        default='outputs/lua_observation_latest.json',
        help='루아의 관찰 데이터'
    )
    parser.add_argument(
        '--elo-validation',
        default='outputs/elo_validation_latest.json',
        help='엘로의 검증 데이터'
    )
    parser.add_argument(
        '--out-json',
        default='outputs/lumen_enhanced_synthesis_latest.json',
        help='통합 결과 JSON'
    )
    parser.add_argument(
        '--out-md',
        default='outputs/lumen_enhanced_synthesis_latest.md',
        help='통합 결과 Markdown'
    )
    
    args = parser.parse_args()
    
    # 경로 보정
    repo_root = Path(__file__).parent.parent.parent
    lua_path = repo_root / args.lua_observation if not Path(args.lua_observation).is_absolute() else Path(args.lua_observation)
    elo_path = repo_root / args.elo_validation if not Path(args.elo_validation).is_absolute() else Path(args.elo_validation)
    out_json = repo_root / args.out_json if not Path(args.out_json).is_absolute() else Path(args.out_json)
    out_md = repo_root / args.out_md if not Path(args.out_md).is_absolute() else Path(args.out_md)
    
    # 통합 실행
    synthesizer = LumenEnhancedSynthesizer(str(lua_path), str(elo_path))
    result = synthesizer.synthesize()
    
    # JSON 저장
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON saved: {out_json}")
    
    # Markdown 생성
    from lumen_synthesis_agent import generate_markdown
    md_content = generate_markdown(result)
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(md_content)
    print(f"📄 Markdown saved: {out_md}")
    
    print()
    print("✅ 루멘 (합) 강화판 통합 완료")
    print("   정반합(正反合) + 확장(擴) 사이클 완성!")


if __name__ == '__main__':
    main()
