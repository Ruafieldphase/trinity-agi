#!/usr/bin/env python3
"""
PersonaOrchestrator 자동 마이그레이션 도구

Week 7: 자동화된 마이그레이션
기존 import 문과 API 호출을 새로운 방식으로 자동 변환

Usage:
  python migrate_persona_imports.py --file path/to/file.py
  python migrate_persona_imports.py --dir path/to/directory
  python migrate_persona_imports.py --project .
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class MigrationChange:
    """마이그레이션 변경사항"""

    line_number: int
    original: str
    new: str
    change_type: str  # 'import', 'api_call', 'comment'


class PersonaPipelineMigrator:
    """PersonaPipeline 자동 마이그레이션 도구"""

    def __init__(self, dry_run: bool = True, verbose: bool = True):
        """
        초기화

        Args:
            dry_run: True이면 변경사항만 표시하고 실제 수정하지 않음
            verbose: True이면 상세 정보 출력
        """
        self.dry_run = dry_run
        self.verbose = verbose
        self.changes: List[MigrationChange] = []

    def migrate_file(self, filepath: str) -> bool:
        """
        파일 마이그레이션

        Args:
            filepath: 대상 파일 경로

        Returns:
            마이그레이션 성공 여부
        """
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False

        if not filepath.endswith(".py"):
            print(f"⏭️  Skipping non-Python file: {filepath}")
            return True

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            self.changes.clear()
            new_lines = []

            for line_num, line in enumerate(lines, 1):
                new_line = self._migrate_line(line, line_num)
                new_lines.append(new_line)

            # 파일에 변경사항이 있으면
            new_content = "\n".join(new_lines)
            if new_content != content:
                if self.dry_run:
                    print(f"📋 (dry-run) Would migrate: {filepath}")
                    self._print_changes()
                else:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"✅ Migrated: {filepath}")
                    if self.verbose:
                        self._print_changes()
                return True
            else:
                if self.verbose:
                    print(f"⏭️  No changes needed: {filepath}")
                return True

        except Exception as e:
            print(f"❌ Error processing {filepath}: {str(e)}")
            return False

    def migrate_directory(self, directory: str) -> Tuple[int, int]:
        """
        디렉토리 내 모든 Python 파일 마이그레이션

        Args:
            directory: 대상 디렉토리

        Returns:
            (성공 개수, 실패 개수)
        """
        if not os.path.isdir(directory):
            print(f"❌ Directory not found: {directory}")
            return 0, 0

        success = 0
        failed = 0

        for root, dirs, files in os.walk(directory):
            # 무시할 디렉토리
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", "venv"]]

            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    if self.migrate_file(filepath):
                        success += 1
                    else:
                        failed += 1

        return success, failed

    def _migrate_line(self, line: str, line_num: int) -> str:
        """
        라인 마이그레이션

        Args:
            line: 원본 라인
            line_num: 라인 번호

        Returns:
            마이그레이션된 라인
        """
        original = line

        # 1. Import 문 마이그레이션
        # from persona_system import PersonaPipeline
        # → from persona_system import get_pipeline
        if "from persona_system import PersonaPipeline" in line and "get_pipeline" not in line:
            line = line.replace(
                "from persona_system import PersonaPipeline",
                "from persona_system import get_pipeline",
            )
            if line != original:
                self.changes.append(
                    MigrationChange(
                        line_number=line_num,
                        original=original.strip(),
                        new=line.strip(),
                        change_type="import",
                    )
                )

        # 2. PersonaPipeline() 호출 마이그레이션
        # PersonaPipeline() → get_pipeline()
        if re.search(r"\bPersonaPipeline\(\)", line) and "from" not in line:
            new_line = re.sub(r"\bPersonaPipeline\(\)", "get_pipeline()", line)
            if new_line != line:
                self.changes.append(
                    MigrationChange(
                        line_number=line_num,
                        original=line.strip(),
                        new=new_line.strip(),
                        change_type="api_call",
                    )
                )
                line = new_line

        return line

    def _print_changes(self) -> None:
        """변경사항 출력"""
        if not self.changes:
            return

        print("  변경사항:")
        for change in self.changes:
            print(f"    Line {change.line_number} [{change.change_type}]")
            print(f"      - {change.original}")
            print(f"      + {change.new}")

    def generate_report(self, success: int, failed: int) -> str:
        """
        마이그레이션 보고서 생성

        Args:
            success: 성공한 파일 개수
            failed: 실패한 파일 개수

        Returns:
            보고서 텍스트
        """
        return f"""
╔════════════════════════════════════════╗
║   PersonaOrchestrator 마이그레이션     ║
║          보고서                        ║
╚════════════════════════════════════════╝

Mode: {"DRY RUN (시뮬레이션)" if self.dry_run else "LIVE MIGRATION"}

결과:
  ✅ 성공: {success}개 파일
  ❌ 실패: {failed}개 파일
  📊 총계: {success + failed}개 파일

다음 단계:
  1. 변경사항 검토
  2. 테스트 실행: pytest tests/
  3. 코드 리뷰
  4. 배포

주의사항:
  - 마이그레이션 후 모든 테스트 실행하세요
  - 기존 코드는 여전히 작동합니다 (호환성 레이어)
  - 필요시 세부 수정이 필요할 수 있습니다
"""


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="PersonaOrchestrator 자동 마이그레이션 도구")
    parser.add_argument("--file", help="마이그레이션할 파일 경로")
    parser.add_argument("--dir", help="마이그레이션할 디렉토리")
    parser.add_argument("--project", help="프로젝트 루트 디렉토리")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="변경사항만 표시하고 수정하지 않음 (기본값)",
    )
    parser.add_argument("--live", action="store_true", help="실제 파일 수정")
    parser.add_argument("--quiet", action="store_true", help="최소한의 출력만 표시")

    args = parser.parse_args()

    # 검증
    if not any([args.file, args.dir, args.project]):
        parser.print_help()
        print("\n❌ --file, --dir, 또는 --project 중 하나를 지정하세요")
        sys.exit(1)

    # 마이그레이터 생성
    migrator = PersonaPipelineMigrator(dry_run=not args.live, verbose=not args.quiet)

    success = 0
    failed = 0

    # 실행
    if args.file:
        if migrator.migrate_file(args.file):
            success = 1
        else:
            failed = 1
    elif args.dir:
        success, failed = migrator.migrate_directory(args.dir)
    elif args.project:
        # 프로젝트 디렉토리 (테스트, 앱 등 제외)
        for subdir in ["app", "tests", "persona_system"]:
            path = os.path.join(args.project, subdir)
            if os.path.exists(path):
                s, f = migrator.migrate_directory(path)
                success += s
                failed += f

    # 보고서 출력
    print(migrator.generate_report(success, failed))

    # 종료 코드
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
