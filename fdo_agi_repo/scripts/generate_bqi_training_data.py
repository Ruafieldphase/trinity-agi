#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BQI Training Data Generator
기존 대화 데이터를 BQI 좌표로 변환
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# BQI 어댑터 경로 추가
import sys
from pathlib import Path
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

from scripts.rune.bqi_adapter import analyse_question, BQICoordinate

class BQITrainingDataGenerator:
    """
    비노체의 대화 데이터를 BQI 좌표로 변환하는 시스템
    
    입력: ai_conversations_anonymized.jsonl
    출력: bqi_training_dataset.jsonl
    """
    
    def __init__(
        self,
        conversation_file: str = "d:/nas_backup/outputs/ai_conversations_anonymized.jsonl",
        output_dir: str = "d:/nas_backup/fdo_agi_repo/memory"
    ):
        self.conversation_file = Path(conversation_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 통계
        self.stats = {
            "total_messages": 0,
            "user_questions": 0,
            "ai_responses": 0,
            "conversations": 0,
            "emotion_distribution": defaultdict(int),
            "rhythm_distribution": defaultdict(int)
        }
    
    def load_conversations(self) -> List[Dict]:
        """JSONL에서 대화 로드"""
        conversations = []
        
        print(f"📂 Loading conversations from {self.conversation_file}...")
        
        with open(self.conversation_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                    conversations.append(msg)
                    self.stats["total_messages"] += 1
                except json.JSONDecodeError:
                    continue
        
        print(f"✅ Loaded {self.stats['total_messages']:,} messages")
        return conversations
    
    def extract_user_questions(self, conversations: List[Dict]) -> List[Dict]:
        """사용자 질문만 추출 (author_role="user")"""
        questions = []
        
        for msg in conversations:
            if msg.get("author_role") == "user":
                content = msg.get("content_trimmed", "")
                
                # 컨텐츠 정리
                if content and len(content) > 10:  # 최소 길이
                    questions.append({
                        "conversation_id": msg.get("conversation_id_anon", ""),
                        "date": msg.get("date", ""),
                        "source": msg.get("source", "unknown"),
                        "question": content
                    })
                    self.stats["user_questions"] += 1
        
        print(f"✅ Extracted {self.stats['user_questions']:,} user questions")
        return questions
    
    def generate_bqi_coordinates(
        self,
        questions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """
        각 질문에 대해 BQI 좌표 생성
        
        Returns:
            [
                {
                    "question": "...",
                    "bqi": {
                        "timestamp": "...",
                        "rhythm_phase": "...",
                        "emotion": {...},
                        "priority": 1
                    },
                    "metadata": {...}
                },
                ...
            ]
        """
        training_data = []
        
        print(f"\n🧮 Generating BQI coordinates...")
        
        for i, q in enumerate(questions):
            try:
                # BQI 좌표 생성
                date_str = q.get("date", "")
                timestamp = self._parse_date(date_str)
                
                bqi_coord = analyse_question(q["question"], now=timestamp)
                
                # 통계 업데이트
                self.stats["rhythm_distribution"][bqi_coord.rhythm_phase] += 1
                for emotion in bqi_coord.emotion.keys():
                    self.stats["emotion_distribution"][emotion] += 1
                
                # 훈련 데이터 포맷
                training_data.append({
                    "question": q["question"],
                    "bqi": bqi_coord.to_dict(),
                    "metadata": {
                        "conversation_id": q["conversation_id"],
                        "date": q["date"],
                        "source": q["source"]
                    }
                })
                
                # 진행 상황 출력
                if (i + 1) % 1000 == 0:
                    print(f"  Processed {i+1:,} / {len(questions):,} questions...")
                
            except Exception as e:
                print(f"⚠️ Error processing question {i}: {e}")
                continue
        
        print(f"✅ Generated {len(training_data):,} BQI coordinates")
        return training_data
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열을 datetime으로 변환"""
        if not date_str:
            return None
        
        try:
            # "2025-10-07" 형식
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None
    
    def save_training_data(self, training_data: List[Dict]):
        """훈련 데이터 저장"""
        output_file = self.output_dir / "bqi_training_dataset.jsonl"
        
        print(f"\n💾 Saving training data to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        print(f"✅ Saved {len(training_data):,} training examples")
        return output_file
    
    def save_statistics(self):
        """통계 저장 (JSON + Markdown)"""
        stats_json = self.output_dir / "bqi_training_stats.json"
        stats_md = self.output_dir / "bqi_training_stats.md"
        
        # JSON 저장
        with open(stats_json, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        # Markdown 보고서 생성
        with open(stats_md, 'w', encoding='utf-8') as f:
            f.write("# BQI Training Data Statistics\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            
            f.write("## Overview\n\n")
            f.write(f"- **Total Messages:** {self.stats['total_messages']:,}\n")
            f.write(f"- **User Questions:** {self.stats['user_questions']:,}\n")
            f.write(f"- **AI Responses:** {self.stats['ai_responses']:,}\n\n")
            
            f.write("## Rhythm Phase Distribution\n\n")
            f.write("| Rhythm Phase | Count | Percentage |\n")
            f.write("|--------------|-------|------------|\n")
            total = self.stats["user_questions"]
            for phase, count in sorted(
                self.stats["rhythm_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                pct = (count / total * 100) if total > 0 else 0
                f.write(f"| {phase} | {count:,} | {pct:.1f}% |\n")
            
            f.write("\n## Emotion Distribution\n\n")
            f.write("| Emotion | Count | Percentage |\n")
            f.write("|---------|-------|------------|\n")
            for emotion, count in sorted(
                self.stats["emotion_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                pct = (count / total * 100) if total > 0 else 0
                f.write(f"| {emotion} | {count:,} | {pct:.1f}% |\n")
        
        print(f"✅ Saved statistics to {stats_json} and {stats_md}")
    
    def run(self):
        """전체 파이프라인 실행"""
        print("🚀 BQI Training Data Generation Pipeline\n")
        
        # 1. 대화 로드
        conversations = self.load_conversations()
        
        # 2. 사용자 질문 추출
        questions = self.extract_user_questions(conversations)
        
        # 3. BQI 좌표 생성
        training_data = self.generate_bqi_coordinates(questions)
        
        # 4. 저장
        output_file = self.save_training_data(training_data)
        self.save_statistics()
        
        print(f"\n✅ Pipeline complete!")
        print(f"📊 Output: {output_file}")
        print(f"📈 Stats: {self.output_dir / 'bqi_training_stats.md'}")
        
        return output_file


def main():
    """메인 실행"""
    generator = BQITrainingDataGenerator()
    output_file = generator.run()
    
    print(f"\n🎯 Next steps:")
    print(f"1. Review: code {output_file}")
    print(f"2. Analyze patterns in BQI coordinates")
    print(f"3. Integrate into pipeline.py")


if __name__ == "__main__":
    main()
