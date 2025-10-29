#!/usr/bin/env python3
"""
Conversation Log Parser

ai_binoche_conversation_origin의 대화 로그를 파싱하여
AGI 학습 데이터 형식으로 변환합니다.

Sena의 판단으로 구현됨 (2025-10-20)
"""

import json
import os
import glob
from pathlib import Path
from typing import List, Dict, Any, Generator
from datetime import datetime, timezone
from collections import defaultdict


class ConversationLogParser:
    """대화 로그 파싱 및 정규화"""

    def __init__(self, source_directory: str):
        """
        Args:
            source_directory: ai_binoche_conversation_origin의 경로
        """
        self.source_dir = source_directory
        self.parsed_conversations = []
        self.statistics = {
            "total_files": 0,
            "total_sessions": 0,
            "total_messages": 0,
            "speakers": defaultdict(int),
            "errors": []
        }

    def find_jsonl_files(self) -> List[str]:
        """
        source_directory에서 모든 JSONL 파일 찾기

        Returns:
            JSONL 파일 경로 리스트
        """
        # Windows 경로 처리
        search_pattern = os.path.join(self.source_dir, "**", "*.jsonl")
        files = glob.glob(search_pattern, recursive=True)

        return sorted(files)

    def parse_jsonl_file(self, file_path: str) -> Generator[Dict[str, Any], None, None]:
        """
        JSONL 파일을 한 줄씩 파싱

        Args:
            file_path: JSONL 파일 경로

        Yields:
            파싱된 JSON 객체
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if line.strip():
                            obj = json.loads(line)
                            yield obj
                    except json.JSONDecodeError as e:
                        self.statistics["errors"].append(
                            f"{file_path}:{line_num} - JSON decode error"
                        )
                        continue
        except IOError as e:
            self.statistics["errors"].append(
                f"{file_path} - IO error: {str(e)}"
            )

    def extract_speaker(self, obj: Dict[str, Any]) -> str:
        """
        JSON 객체에서 speaker 추출

        여러 형식을 지원:
        - "role" 필드
        - "speaker" 필드
        - "author" 필드
        """
        # 가능한 speaker 필드들
        for field in ["role", "speaker", "author", "name", "user_role"]:
            if field in obj:
                return str(obj[field])

        # 기본값
        return "unknown"

    def extract_text(self, obj: Dict[str, Any]) -> str:
        """
        JSON 객체에서 text 추출

        여러 형식을 지원:
        - "content" 필드
        - "text" 필드
        - "message" 필드
        """
        # 가능한 text 필드들
        for field in ["content", "text", "message", "body"]:
            if field in obj:
                value = obj[field]
                if isinstance(value, str):
                    return value
                elif isinstance(value, dict):
                    # nested content
                    if "text" in value:
                        return value["text"]
                    elif "content" in value:
                        return value["content"]

        return ""

    def extract_timestamp(self, obj: Dict[str, Any]) -> str:
        """
        JSON 객체에서 timestamp 추출

        Returns:
            ISO 8601 형식의 timestamp 또는 현재 시간
        """
        for field in ["timestamp", "created_at", "time", "date"]:
            if field in obj:
                value = obj[field]
                # 이미 ISO 형식인 경우
                if isinstance(value, str) and ("T" in value or "-" in value):
                    return value
                # Unix timestamp인 경우
                elif isinstance(value, (int, float)):
                    try:
                        dt = datetime.fromtimestamp(value)
                        return dt.isoformat() + "Z"
                    except:
                        pass

        # 기본값: 현재 시간
        return datetime.now(timezone.utc).isoformat() + "Z"

    def normalize_conversation(
        self,
        obj: Dict[str, Any],
        session_id: str,
        turn_number: int
    ) -> Dict[str, Any]:
        """
        원본 JSON을 정규화된 형식으로 변환

        Args:
            obj: 원본 JSON 객체
            session_id: 세션 ID
            turn_number: 턴 번호

        Returns:
            정규화된 대화 객체
        """
        speaker = self.extract_speaker(obj)
        text = self.extract_text(obj)
        timestamp = self.extract_timestamp(obj)

        # text가 list인 경우 처리
        if isinstance(text, list):
            text = " ".join(str(t) for t in text)

        # text를 문자열로 변환
        text = str(text) if text else ""
        tokens = text.lower().split() if text else []

        return {
            "session_id": session_id,
            "timestamp": timestamp,
            "turn_number": turn_number,
            "speaker": speaker,
            "text": text,
            "tokens": tokens,
            "token_count": len(tokens),
            "raw_data": obj  # 원본 데이터 보존
        }

    def parse_all_conversations(self) -> int:
        """
        모든 대화 파일을 파싱

        Returns:
            파싱된 총 메시지 수
        """
        files = self.find_jsonl_files()
        self.statistics["total_files"] = len(files)

        total_messages = 0

        for file_path in files:
            # 세션 ID 생성 (파일 경로 기반)
            session_id = Path(file_path).stem

            turn_number = 0
            for obj in self.parse_jsonl_file(file_path):
                turn_number += 1
                total_messages += 1

                # 정규화
                normalized = self.normalize_conversation(
                    obj, session_id, turn_number
                )

                # Speaker 추적
                speaker = normalized["speaker"]
                self.statistics["speakers"][speaker] += 1

                self.parsed_conversations.append(normalized)

            self.statistics["total_sessions"] += 1

        self.statistics["total_messages"] = total_messages
        return total_messages

    def get_statistics(self) -> Dict[str, Any]:
        """
        파싱 통계 조회

        Returns:
            통계 딕셔너리
        """
        return self.statistics

    def export_to_jsonl(self, output_file: str) -> int:
        """
        파싱된 대화를 JSONL 형식으로 내보내기

        Args:
            output_file: 출력 파일 경로

        Returns:
            내보낸 메시지 수
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for conv in self.parsed_conversations:
                    # raw_data는 제외 (크기 때문에)
                    export_conv = {k: v for k, v in conv.items() if k != "raw_data"}
                    f.write(json.dumps(export_conv, ensure_ascii=False) + '\n')

            return len(self.parsed_conversations)

        except IOError as e:
            print(f"[ERROR] Cannot write to {output_file}: {str(e)}")
            return 0

    def get_speakers(self) -> List[str]:
        """
        참여한 모든 speaker 목록

        Returns:
            speaker 리스트
        """
        return list(self.statistics["speakers"].keys())

    def filter_by_speaker(self, speaker: str) -> List[Dict[str, Any]]:
        """
        특정 speaker의 메시지만 필터링

        Args:
            speaker: speaker 이름

        Returns:
            필터링된 대화 리스트
        """
        return [
            conv for conv in self.parsed_conversations
            if conv["speaker"] == speaker
        ]

    def filter_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        특정 session의 메시지만 필터링

        Args:
            session_id: session ID

        Returns:
            필터링된 대화 리스트
        """
        return [
            conv for conv in self.parsed_conversations
            if conv["session_id"] == session_id
        ]


def demo():
    """데모: 대화 로그 파싱"""
    print("="*70)
    print("Conversation Log Parser - Demo")
    print("="*70)

    # Windows 경로 처리
    if os.name == 'nt':
        source_dir = r"d:\nas_backup\ai_binoche_conversation_origin"
        output_file = r"d:\nas_backup\session_memory\parsed_conversations.jsonl"
    else:
        source_dir = "/d/nas_backup/ai_binoche_conversation_origin"
        output_file = "/d/nas_backup/session_memory/parsed_conversations.jsonl"

    print(f"\n[INFO] Source directory: {source_dir}")
    print(f"[INFO] Output file: {output_file}\n")

    # 파서 생성
    parser = ConversationLogParser(source_dir)

    # 모든 파일 찾기
    files = parser.find_jsonl_files()
    print(f"[INFO] Found {len(files)} JSONL files")

    if len(files) > 0:
        print(f"[INFO] Parsing conversations...")
        total = parser.parse_all_conversations()
        print(f"[OK] Parsed {total} messages")

        # 통계 출력
        stats = parser.get_statistics()
        print(f"\n[STATS]")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total sessions: {stats['total_sessions']}")
        print(f"  Total messages: {stats['total_messages']}")
        print(f"  Speakers: {dict(stats['speakers'])}")

        if stats['errors']:
            print(f"\n[WARNING] Errors ({len(stats['errors'])}):")
            for error in stats['errors'][:5]:
                print(f"  - {error}")

        # 내보내기
        print(f"\n[INFO] Exporting to JSONL...")
        exported = parser.export_to_jsonl(output_file)
        print(f"[OK] Exported {exported} messages to {output_file}")

        # 샘플 출력
        if parser.parsed_conversations:
            print(f"\n[SAMPLE] First message:")
            sample = parser.parsed_conversations[0]
            print(f"  Session: {sample['session_id']}")
            print(f"  Speaker: {sample['speaker']}")
            print(f"  Text: {sample['text'][:100]}...")
            print(f"  Tokens: {len(sample['tokens'])}")

    else:
        print("[WARNING] No JSONL files found!")

    print("\n" + "="*70)
    print("[SUCCESS] Conversation Log Parser Ready!")
    print("="*70)


if __name__ == "__main__":
    demo()
