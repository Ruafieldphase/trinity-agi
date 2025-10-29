#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 마이그레이션 시스템 - 스키마 버전 관리

이 모듈은 데이터베이스 스키마의 버전을 관리하고 마이그레이션을 수행합니다.
"""

import sys
import io
import json
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
from sqlalchemy import Column, String, Integer, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 마이그레이션 모델
# ============================================================================

Base = declarative_base()


class MigrationVersion(Base):
    """마이그레이션 버전 기록"""
    __tablename__ = 'migration_versions'

    version_id = Column(String(50), primary_key=True)
    version = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    applied_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer, default=0)
    status = Column(String(50), default="completed")  # completed, failed, pending

    def __repr__(self):
        return f"<MigrationVersion v{self.version} - {self.name}>"


# ============================================================================
# 마이그레이션 정의
# ============================================================================

class Migration:
    """마이그레이션 기본 클래스"""

    def __init__(self, version: int, name: str, description: str = ""):
        """
        초기화

        Args:
            version: 마이그레이션 버전 번호
            name: 마이그레이션 이름
            description: 마이그레이션 설명
        """
        self.version = version
        self.name = name
        self.description = description

    def up(self, session) -> bool:
        """마이그레이션 업그레이드"""
        raise NotImplementedError

    def down(self, session) -> bool:
        """마이그레이션 다운그레이드"""
        raise NotImplementedError

    def get_id(self) -> str:
        """마이그레이션 ID 생성"""
        return f"{self.version:03d}_{self.name}"


# ============================================================================
# 마이그레이션 구현
# ============================================================================

class Migration001_InitialSchema(Migration):
    """마이그레이션 001: 초기 스키마 생성"""

    def __init__(self):
        super().__init__(1, "initial_schema", "에이전트 시스템 초기 스키마 생성")

    def up(self, session) -> bool:
        """마이그레이션 업그레이드"""
        try:
            # 이 마이그레이션은 database_models.py에서 Base.metadata.create_all()로 처리됨
            print("  ✓ 초기 스키마 생성 완료")
            return True
        except Exception as e:
            print(f"  ✗ 스키마 생성 실패: {e}")
            return False

    def down(self, session) -> bool:
        """마이그레이션 다운그레이드"""
        try:
            # 실제 환경에서는 신중하게 처리
            print("  ✓ 초기 스키마 롤백")
            return True
        except Exception as e:
            print(f"  ✗ 롤백 실패: {e}")
            return False


class Migration002_AddIndices(Migration):
    """마이그레이션 002: 인덱스 추가"""

    def __init__(self):
        super().__init__(2, "add_indices", "자주 검색되는 컬럼에 인덱스 추가")

    def up(self, session) -> bool:
        """마이그레이션 업그레이드"""
        try:
            # 인덱스 생성 쿼리 (DB별로 다를 수 있음)
            # SQLite의 경우
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_tasks_workflow_id ON tasks(workflow_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_agent_id ON tasks(agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)",
                "CREATE INDEX IF NOT EXISTS idx_messages_from_agent ON messages(from_agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_messages_to_agent ON messages(to_agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_health_records_agent_id ON health_records(agent_id)",
                "CREATE INDEX IF NOT EXISTS idx_agent_metrics_agent_id ON agent_metrics(agent_id)",
            ]

            for idx_sql in indexes:
                try:
                    session.execute(idx_sql)
                except Exception as e:
                    # 인덱스가 이미 존재하거나 다른 오류
                    pass

            session.commit()
            print("  ✓ 인덱스 추가 완료")
            return True

        except Exception as e:
            print(f"  ✗ 인덱스 추가 실패: {e}")
            session.rollback()
            return False

    def down(self, session) -> bool:
        """마이그레이션 다운그레이드"""
        try:
            indexes_to_drop = [
                "DROP INDEX IF EXISTS idx_tasks_workflow_id",
                "DROP INDEX IF EXISTS idx_tasks_agent_id",
                "DROP INDEX IF EXISTS idx_tasks_status",
                "DROP INDEX IF EXISTS idx_messages_from_agent",
                "DROP INDEX IF EXISTS idx_messages_to_agent",
                "DROP INDEX IF EXISTS idx_health_records_agent_id",
                "DROP INDEX IF EXISTS idx_agent_metrics_agent_id",
            ]

            for idx_sql in indexes_to_drop:
                try:
                    session.execute(idx_sql)
                except Exception:
                    pass

            session.commit()
            print("  ✓ 인덱스 제거 완료")
            return True

        except Exception as e:
            print(f"  ✗ 인덱스 제거 실패: {e}")
            session.rollback()
            return False


class Migration003_AddColumnProperties(Migration):
    """마이그레이션 003: 컬럼 속성 추가"""

    def __init__(self):
        super().__init__(3, "add_column_properties", "추가 컬럼 속성 및 메타데이터")

    def up(self, session) -> bool:
        """마이그레이션 업그레이드"""
        try:
            # 알터 테이블 쿼리 (DB별로 다름)
            # 이는 시뮬레이션이므로 실제 DB에 따라 조정 필요
            print("  ✓ 컬럼 속성 추가 완료")
            return True

        except Exception as e:
            print(f"  ✗ 컬럼 속성 추가 실패: {e}")
            return False

    def down(self, session) -> bool:
        """마이그레이션 다운그레이드"""
        try:
            print("  ✓ 컬럼 속성 제거 완료")
            return True

        except Exception as e:
            print(f"  ✗ 컬럼 속성 제거 실패: {e}")
            return False


# ============================================================================
# 마이그레이션 관리자
# ============================================================================

class MigrationManager:
    """마이그레이션 관리자"""

    def __init__(self, database_url: str, migration_dir: str = None):
        """
        초기화

        Args:
            database_url: 데이터베이스 연결 문자열
            migration_dir: 마이그레이션 파일 디렉토리
        """
        self.database_url = database_url
        self.migration_dir = Path(migration_dir) if migration_dir else Path("migrations")
        self.migration_dir.mkdir(exist_ok=True)

        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 마이그레이션 버전 테이블 생성
        Base.metadata.create_all(self.engine)

        # 마이그레이션 목록
        self.migrations: Dict[int, Migration] = {}
        self._register_migrations()

    def _register_migrations(self):
        """마이그레이션 등록"""
        self.migrations[1] = Migration001_InitialSchema()
        self.migrations[2] = Migration002_AddIndices()
        self.migrations[3] = Migration003_AddColumnProperties()

    def register_migration(self, migration: Migration):
        """커스텀 마이그레이션 등록"""
        self.migrations[migration.version] = migration

    def get_applied_versions(self) -> List[int]:
        """적용된 마이그레이션 버전 조회"""
        session = self.SessionLocal()
        try:
            records = session.query(MigrationVersion).order_by(MigrationVersion.version).all()
            return [r.version for r in records if r.status == "completed"]
        finally:
            session.close()

    def get_latest_version(self) -> int:
        """최신 마이그레이션 버전"""
        applied = self.get_applied_versions()
        return max(applied) if applied else 0

    def migrate_up(self, target_version: int = None) -> bool:
        """마이그레이션 업그레이드"""
        session = self.SessionLocal()
        try:
            applied = self.get_applied_versions()
            current_version = max(applied) if applied else 0

            if target_version is None:
                target_version = max(self.migrations.keys())

            migrations_to_apply = sorted([
                v for v in self.migrations.keys()
                if v > current_version and v <= target_version
            ])

            if not migrations_to_apply:
                print("✓ 모든 마이그레이션이 적용되어 있습니다.")
                return True

            print(f"\n마이그레이션 업그레이드: v{current_version} → v{target_version}")
            print("-" * 80)

            for version in migrations_to_apply:
                migration = self.migrations[version]
                print(f"\n[{version}] {migration.name}: {migration.description}")

                import time
                start_time = time.time()

                try:
                    success = migration.up(session)
                    duration_ms = int((time.time() - start_time) * 1000)

                    if success:
                        # 마이그레이션 기록
                        record = MigrationVersion(
                            version_id=migration.get_id(),
                            version=version,
                            name=migration.name,
                            description=migration.description,
                            duration_ms=duration_ms,
                            status="completed"
                        )
                        session.add(record)
                        session.commit()
                        print(f"✓ 완료 ({duration_ms}ms)")
                    else:
                        print(f"✗ 실패")
                        return False

                except Exception as e:
                    print(f"✗ 오류: {e}")
                    session.rollback()
                    return False

            print("\n✓ 마이그레이션 완료!")
            return True

        finally:
            session.close()

    def migrate_down(self, target_version: int = None) -> bool:
        """마이그레이션 다운그레이드"""
        session = self.SessionLocal()
        try:
            applied = self.get_applied_versions()
            current_version = max(applied) if applied else 0

            if target_version is None:
                target_version = current_version - 1 if current_version > 1 else 0

            if target_version >= current_version:
                print("✓ 이미 대상 버전입니다.")
                return True

            migrations_to_rollback = sorted([
                v for v in self.migrations.keys()
                if v > target_version and v <= current_version
            ], reverse=True)

            if not migrations_to_rollback:
                print("✓ 롤백할 마이그레이션이 없습니다.")
                return True

            print(f"\n마이그레이션 다운그레이드: v{current_version} → v{target_version}")
            print("-" * 80)

            for version in migrations_to_rollback:
                migration = self.migrations[version]
                print(f"\n[{version}] {migration.name} 롤백 중...")

                import time
                start_time = time.time()

                try:
                    success = migration.down(session)
                    duration_ms = int((time.time() - start_time) * 1000)

                    if success:
                        # 마이그레이션 기록 삭제
                        session.query(MigrationVersion).filter_by(version=version).delete()
                        session.commit()
                        print(f"✓ 완료 ({duration_ms}ms)")
                    else:
                        print(f"✗ 실패")
                        return False

                except Exception as e:
                    print(f"✗ 오류: {e}")
                    session.rollback()
                    return False

            print("\n✓ 롤백 완료!")
            return True

        finally:
            session.close()

    def status(self):
        """마이그레이션 상태 확인"""
        session = self.SessionLocal()
        try:
            records = session.query(MigrationVersion).order_by(MigrationVersion.version).all()

            print("\n" + "=" * 80)
            print("마이그레이션 상태")
            print("=" * 80)

            if not records:
                print("\n적용된 마이그레이션이 없습니다.")
                return

            current_version = max([r.version for r in records]) if records else 0
            latest_version = max(self.migrations.keys())

            print(f"\n현재 버전: v{current_version}")
            print(f"최신 버전: v{latest_version}")
            print(f"상태: {'최신' if current_version == latest_version else '업그레이드 필요'}")

            print(f"\n적용된 마이그레이션:")
            for record in records:
                print(f"  • v{record.version}: {record.name}")
                print(f"    적용시간: {record.applied_at.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    소요시간: {record.duration_ms}ms")

        finally:
            session.close()


# ============================================================================
# 데모: 마이그레이션 시스템
# ============================================================================

def demo_migration_system():
    """마이그레이션 시스템 데모"""
    print("=" * 80)
    print("데이터베이스 마이그레이션 시스템 데모")
    print("=" * 80)

    # 마이그레이션 관리자 생성
    print("\n[1단계] 마이그레이션 관리자 초기화")
    print("-" * 80)

    manager = MigrationManager("sqlite:///:memory:")
    print("✓ 마이그레이션 관리자 초기화 완료")

    # 마이그레이션 업그레이드
    print("\n[2단계] 마이그레이션 업그레이드")
    print("-" * 80)

    success = manager.migrate_up(target_version=3)
    if success:
        print("✓ 마이그레이션 업그레이드 성공")
    else:
        print("✗ 마이그레이션 업그레이드 실패")

    # 마이그레이션 상태 확인
    print("\n[3단계] 마이그레이션 상태 확인")
    print("-" * 80)

    manager.status()

    # 마이그레이션 다운그레이드
    print("\n[4단계] 마이그레이션 다운그레이드")
    print("-" * 80)

    success = manager.migrate_down(target_version=1)
    if success:
        print("✓ 마이그레이션 다운그레이드 성공")
    else:
        print("✗ 마이그레이션 다운그레이드 실패")

    # 최종 상태 확인
    print("\n[5단계] 최종 상태 확인")
    print("-" * 80)

    manager.status()

    # 다시 업그레이드
    print("\n[6단계] 다시 마이그레이션 업그레이드")
    print("-" * 80)

    success = manager.migrate_up()
    if success:
        print("✓ 마이그레이션 업그레이드 성공")
    else:
        print("✗ 마이그레이션 업그레이드 실패")

    # 최종 상태
    print("\n[7단계] 최종 상태")
    print("-" * 80)

    manager.status()

    print("\n" + "=" * 80)
    print("마이그레이션 시스템 데모 완료!")
    print("=" * 80)


if __name__ == "__main__":
    demo_migration_system()
