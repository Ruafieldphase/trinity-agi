#!/usr/bin/env python3
"""
BQI Phase 5: User Feedback Predictor

레전드의 BQI 좌표와 품질 메트릭을 학습하여
사용자의 피드백을 예측하고 응답을 사전 조정합니다.

학습 데이터:
- quality (0.0-1.0): 사용자 만족도 직접 지표
- confidence (0.0-1.0): AGI 자신감 (낮으면 second_pass 발동)
- evidence_ok (bool): 증거 충분성
- second_pass (event): 품질 불만족 시그널
- BQI 좌표: priority, emotion, rhythm

예측 목표:
- 응답 전송 전 사용자 만족도 예측 (0.0-1.0)
- 만족도 < 0.6 시 응답 조정 힌트 제공
"""
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
from collections import defaultdict
import statistics


class UserFeedbackPredictor:
    """BQI 기반 사용자 피드백 예측기"""
    
    def __init__(self, model_path: str = "outputs/feedback_prediction_model.json"):
        self.model_path = Path(model_path)
        self.model = self._load_or_create_model()
    
    def _load_or_create_model(self) -> Dict:
        """모델 로드 또는 생성"""
        if self.model_path.exists():
            with open(self.model_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "satisfaction_by_bqi": {},  # BQI 패턴별 평균 만족도
            "adjustment_rules": [],     # 조정 규칙
            "samples_count": 0
        }
    
    def learn_from_ledger(self, ledger_path: Path | str = "memory/resonance_ledger.jsonl"):
        """레전드에서 BQI→만족도 패턴 학습
        
        학습 로직:
        1. task_id별로 이벤트 그룹화
        2. BQI 좌표 추출 (priority, emotion, rhythm)
        3. 만족도 메트릭 계산:
           - quality (직접 지표)
           - confidence (간접 지표)
           - second_pass 발생 여부 (불만족 강한 시그널)
        4. BQI 패턴별 평균 만족도 저장
        """
        ledger_path_obj = Path(ledger_path) if isinstance(ledger_path, str) else ledger_path
        if not ledger_path_obj.exists():
            print(f"[Feedback] Ledger not found: {ledger_path_obj}")
            return
        
        tasks: Dict[str, List[Dict]] = defaultdict(list)
        
        # 1. task_id별 이벤트 그룹화
        with open(ledger_path_obj, 'r', encoding='utf-8') as f:
            for line in f:
                event = json.loads(line.strip())
                if 'task_id' in event:
                    tasks[event['task_id']].append(event)
        
        # 2. BQI→만족도 매핑 생성
        satisfaction_samples = []
        
        for task_id, events in tasks.items():
            # BQI 좌표 추출 (run_config에서)
            bqi_coord = None
            for evt in events:
                if evt['event'] == 'run_config' and 'bqi_coord' in evt:
                    bqi_coord = evt['bqi_coord']
                    break
            
            # 만족도 메트릭 추출
            quality = None
            confidence = None
            had_second_pass = False
            
            for evt in events:
                if evt['event'] == 'eval':
                    quality = evt.get('quality', 0.5)
                elif evt['event'] == 'meta_cognition':
                    confidence = evt.get('confidence', 0.5)
                elif evt['event'] == 'second_pass':
                    had_second_pass = True
            
            # 만족도 점수 계산
            if quality is not None:
                satisfaction = quality
                if had_second_pass:
                    satisfaction *= 0.7  # 2차 패스 발동 시 페널티
                if confidence is not None and confidence < 0.6:
                    satisfaction *= 0.9  # 낮은 확신도 페널티
                
                if bqi_coord:
                    pattern_key = self._bqi_to_key(bqi_coord)
                    satisfaction_samples.append((pattern_key, satisfaction))
        
        # 3. BQI 패턴별 평균 만족도 계산
        pattern_scores: Dict[str, List[float]] = defaultdict(list)
        for pattern, score in satisfaction_samples:
            pattern_scores[pattern].append(score)
        
        for pattern, scores in pattern_scores.items():
            self.model["satisfaction_by_bqi"][pattern] = {
                "mean": statistics.mean(scores),
                "stdev": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "count": len(scores)
            }
        
        self.model["samples_count"] = len(satisfaction_samples)
        self.model["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # 4. 조정 규칙 생성
        self._generate_adjustment_rules()
        
        # 모델 저장
        self._save_model()
        
        print(f"[Feedback] Learned from {len(tasks)} tasks, {len(satisfaction_samples)} samples")
        print(f"[Feedback] Generated {len(self.model['satisfaction_by_bqi'])} BQI patterns")
    
    def _bqi_to_key(self, bqi_coord: Dict) -> str:
        """BQI 좌표를 패턴 키로 변환
        
        예: priority=4, emotion=['urgent','concern'], rhythm='debug'
        -> "p4_e:urgent,concern_r:debug"
        """
        p = bqi_coord.get('priority', 2)
        e = ','.join(sorted(bqi_coord.get('emotion', [])))
        r = bqi_coord.get('rhythm', 'unknown')
        return f"p{p}_e:{e}_r:{r}"
    
    def _generate_adjustment_rules(self):
        """만족도 낮은 BQI 패턴에 대한 조정 규칙 생성"""
        rules = []
        
        for pattern, stats in self.model["satisfaction_by_bqi"].items():
            if stats["mean"] < 0.6:  # 낮은 만족도
                # 패턴 파싱
                parts = pattern.split('_')
                priority = int(parts[0][1])  # p4 -> 4
                emotions = parts[1].split(':')[1].split(',') if ':' in parts[1] else []
                rhythm = parts[2].split(':')[1] if len(parts) > 2 and ':' in parts[2] else 'unknown'
                
                # 조정 힌트 생성
                hints = []
                if priority >= 3:
                    hints.append("reduce_priority")  # 긴급도 낮춤
                if 'urgent' in emotions:
                    hints.append("add_empathy")  # 공감 추가
                if rhythm == 'debug':
                    hints.append("add_explanation")  # 설명 추가
                
                rules.append({
                    "pattern": pattern,
                    "mean_satisfaction": stats["mean"],
                    "adjustments": hints
                })
        
        self.model["adjustment_rules"] = rules
    
    def predict_satisfaction(
        self, 
        bqi_coord: Dict, 
        response_draft: str
    ) -> Tuple[float, List[str]]:
        """응답 전송 전 만족도 예측
        
        Args:
            bqi_coord: BQI 좌표 {priority, emotion, rhythm}
            response_draft: 응답 초안 텍스트
        
        Returns:
            (predicted_satisfaction, adjustment_hints)
            - predicted_satisfaction: 0.0-1.0 예측 만족도
            - adjustment_hints: 조정 힌트 리스트
        """
        pattern_key = self._bqi_to_key(bqi_coord)
        
        # BQI 패턴으로 예측
        if pattern_key in self.model["satisfaction_by_bqi"]:
            stats = self.model["satisfaction_by_bqi"][pattern_key]
            predicted = stats["mean"]
        else:
            # 미학습 패턴: priority 기반 휴리스틱
            priority = bqi_coord.get('priority', 2)
            predicted = 0.5 + (4 - priority) * 0.1  # priority 낮을수록 만족도 높음
        
        # 응답 길이 기반 조정
        if len(response_draft) < 50:
            predicted *= 0.9  # 너무 짧은 응답 페널티
        
        # 조정 힌트 조회
        hints = []
        for rule in self.model["adjustment_rules"]:
            if rule["pattern"] == pattern_key:
                hints = rule["adjustments"]
                break
        
        return predicted, hints
    
    def _save_model(self):
        """모델 저장"""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'w', encoding='utf-8') as f:
            json.dump(self.model, f, indent=2, ensure_ascii=False)


def main():
    """CLI 진입점"""
    predictor = UserFeedbackPredictor()
    
    # 레전드에서 학습
    predictor.learn_from_ledger()
    
    # 모델 요약 출력
    model = predictor.model
    print(f"\n[Feedback Model Summary]")
    print(f"  Version: {model['version']}")
    print(f"  Last Updated: {model['last_updated']}")
    print(f"  Samples: {model['samples_count']}")
    print(f"  BQI Patterns: {len(model['satisfaction_by_bqi'])}")
    print(f"  Adjustment Rules: {len(model['adjustment_rules'])}")
    
    # 낮은 만족도 패턴 출력
    if model['adjustment_rules']:
        print(f"\n[Low Satisfaction Patterns]")
        for rule in model['adjustment_rules'][:5]:  # 상위 5개
            print(f"  {rule['pattern']}: {rule['mean_satisfaction']:.2f}")
            print(f"    Adjustments: {', '.join(rule['adjustments'])}")


if __name__ == "__main__":
    main()
