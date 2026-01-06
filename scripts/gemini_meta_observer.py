#!/usr/bin/env python3
"""
Gemini Code Assist Meta Observer
문서 품질, 컨텍스트 일관성, 자연어 처리 특화 분석

Author: AGI System
Created: 2025-11-11
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from workspace_root import get_workspace_root

try:
    import google.generativeai as genai
except ImportError:
    print("❌ google-generativeai not installed", file=sys.stderr)
    print("Install: pip install google-generativeai", file=sys.stderr)
    sys.exit(1)

# UTF-8 출력 보장
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


class GeminiTokenTracker:
    """Gemini API 토큰 사용량 추적"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "token_usage.jsonl"
    
    def log_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        analysis_type: str
    ):
        """토큰 사용 로그 기록"""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "analysis_type": analysis_type,
            "cost_estimate_usd": self._estimate_cost(model, prompt_tokens, completion_tokens)
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        return entry
    
    def _estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """토큰 비용 추정 (Gemini 2.0 Flash 기준)"""
        # Gemini 2.0 Flash: 무료 티어 또는 $0.075/$0.30 per 1M tokens
        # 128K 미만 컨텍스트: 무료
        # 초과 시: $0.075 입력 / $0.30 출력 per 1M tokens
        if "gemini-2.0" in model.lower() or "flash" in model.lower():
            input_cost = (prompt_tokens / 1_000_000) * 0.075
            output_cost = (completion_tokens / 1_000_000) * 0.30
            return round(input_cost + output_cost, 6)
        else:
            # Gemini 1.5 Pro: $1.25 입력 / $5.00 출력 per 1M tokens
            input_cost = (prompt_tokens / 1_000_000) * 1.25
            output_cost = (completion_tokens / 1_000_000) * 5.00
            return round(input_cost + output_cost, 6)


class GeminiMetaObserver:
    """Gemini 기반 문서/컨텍스트 분석 시스템"""
    
    def __init__(
        self,
        workspace_root: Path,
        model_name: str = "models/gemini-2.0-flash-exp",
        output_dir: Optional[Path] = None
    ):
        self.workspace_root = workspace_root
        self.model_name = model_name
        self.output_dir = output_dir or (workspace_root / "outputs" / "gemini_meta_observer")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 토큰 트래커 초기화
        self.token_tracker = GeminiTokenTracker(self.output_dir)
        
        # Gemini API 설정
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. "
                "Get your key from https://makersuite.google.com/app/apikey"
            )
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def analyze_documentation_quality(self, target_files: List[Path]) -> Dict[str, Any]:
        """문서 품질 분석 (Gemini 특화)"""
        print("🧠 Gemini: Analyzing documentation quality...")
        
        # 문서 내용 수집
        docs_content = []
        for file_path in target_files:
            if file_path.suffix.lower() in [".md", ".txt", ".rst"]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    docs_content.append({
                        "path": str(file_path.relative_to(self.workspace_root)),
                        "content": content[:10000]  # 첫 10K 문자
                    })
                except Exception as e:
                    print(f"⚠️ Failed to read {file_path}: {e}")
        
        if not docs_content:
            return {"status": "no_docs", "message": "No documentation files found"}
        
        # Gemini 프롬프트 (문서 품질 분석)
        prompt = f"""
Analyze the following documentation files for quality and consistency.

Focus on:
1. **Terminology Consistency**: Are terms used consistently across documents?
2. **Writing Quality**: Grammar, clarity, readability
3. **Structure**: Organization, headings, sections
4. **Completeness**: Missing information, gaps
5. **Code-Documentation Sync**: Are code examples up-to-date?

Documents:
{json.dumps(docs_content, indent=2, ensure_ascii=False)}

Provide a detailed analysis in JSON format:
{{
    "overall_quality_score": 0-100,
    "terminology_issues": [...],
    "writing_improvements": [...],
    "structural_recommendations": [...],
    "missing_content": [...],
    "top_priorities": [...]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            # 토큰 사용량 추적
            if hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                self.token_tracker.log_usage(
                    model=self.model_name,
                    prompt_tokens=usage.prompt_token_count,
                    completion_tokens=usage.candidates_token_count,
                    total_tokens=usage.total_token_count,
                    analysis_type="documentation_quality"
                )
            
            # 응답 파싱
            result_text = response.text
            
            # JSON 추출 시도
            try:
                # Markdown 코드 블록 제거
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(result_text)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 raw text 반환
                analysis = {
                    "raw_response": result_text,
                    "status": "parse_failed"
                }
            
            # 결과 저장
            output_file = self.output_dir / f"doc_quality_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Analysis saved to {output_file}")
            return analysis
        
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return {"status": "error", "message": str(e)}
    
    def check_context_consistency(self, markdown_files: List[Path]) -> Dict[str, Any]:
        """컨텍스트 일관성 검사 (Gemini 장기 컨텍스트 활용)"""
        print("🧠 Gemini: Checking context consistency across files...")
        
        # 파일 내용 수집
        contexts = []
        for md_file in markdown_files[:20]:  # 최대 20개 파일
            try:
                content = md_file.read_text(encoding="utf-8", errors="ignore")
                contexts.append({
                    "file": str(md_file.relative_to(self.workspace_root)),
                    "content": content[:5000]  # 각 파일 5K 문자
                })
            except Exception as e:
                print(f"⚠️ Failed to read {md_file}: {e}")
        
        if not contexts:
            return {"status": "no_contexts", "message": "No markdown files found"}
        
        # Gemini 프롬프트 (컨텍스트 일관성)
        prompt = f"""
Analyze these markdown documents for contextual consistency.

Check for:
1. **Cross-References**: Are links and references valid?
2. **Narrative Flow**: Do documents tell a coherent story?
3. **Duplicated Information**: Is content unnecessarily repeated?
4. **Contradictions**: Are there conflicting statements?
5. **Missing Links**: Should documents reference each other?

Files:
{json.dumps(contexts, indent=2, ensure_ascii=False)}

Provide analysis in JSON:
{{
    "consistency_score": 0-100,
    "broken_references": [...],
    "contradictions": [...],
    "duplication_issues": [...],
    "recommended_links": [...],
    "narrative_gaps": [...]
}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            
            # 토큰 추적
            if hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                self.token_tracker.log_usage(
                    model=self.model_name,
                    prompt_tokens=usage.prompt_token_count,
                    completion_tokens=usage.candidates_token_count,
                    total_tokens=usage.total_token_count,
                    analysis_type="context_consistency"
                )
            
            result_text = response.text
            
            # JSON 파싱
            try:
                if "```json" in result_text:
                    result_text = result_text.split("```json")[1].split("```")[0].strip()
                elif "```" in result_text:
                    result_text = result_text.split("```")[1].split("```")[0].strip()
                
                analysis = json.loads(result_text)
            except json.JSONDecodeError:
                analysis = {
                    "raw_response": result_text,
                    "status": "parse_failed"
                }
            
            # 결과 저장
            output_file = self.output_dir / f"context_consistency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Analysis saved to {output_file}")
            return analysis
        
        except Exception as e:
            print(f"❌ Gemini API error: {e}")
            return {"status": "error", "message": str(e)}
    
    def generate_report(
        self,
        doc_quality: Optional[Dict[str, Any]] = None,
        context_consistency: Optional[Dict[str, Any]] = None
    ) -> str:
        """Markdown 리포트 생성"""
        report_lines = [
            "# 🧠 Gemini Meta Observer Report",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Model**: {self.model_name}",
            "",
            "---",
            ""
        ]
        
        if doc_quality and doc_quality.get("status") != "error":
            report_lines.extend([
                "## 📖 Documentation Quality Analysis",
                ""
            ])
            
            if "overall_quality_score" in doc_quality:
                score = doc_quality["overall_quality_score"]
                report_lines.append(f"**Overall Quality Score**: {score}/100")
                report_lines.append("")
            
            if "terminology_issues" in doc_quality:
                report_lines.append("### 📝 Terminology Issues")
                for issue in doc_quality["terminology_issues"][:5]:
                    report_lines.append(f"- {issue}")
                report_lines.append("")
            
            if "top_priorities" in doc_quality:
                report_lines.append("### 🎯 Top Priorities")
                for priority in doc_quality["top_priorities"][:5]:
                    report_lines.append(f"- {priority}")
                report_lines.append("")
        
        if context_consistency and context_consistency.get("status") != "error":
            report_lines.extend([
                "## 🔗 Context Consistency Analysis",
                ""
            ])
            
            if "consistency_score" in context_consistency:
                score = context_consistency["consistency_score"]
                report_lines.append(f"**Consistency Score**: {score}/100")
                report_lines.append("")
            
            if "broken_references" in context_consistency:
                report_lines.append("### 🔴 Broken References")
                for ref in context_consistency["broken_references"][:5]:
                    report_lines.append(f"- {ref}")
                report_lines.append("")
            
            if "recommended_links" in context_consistency:
                report_lines.append("### 💡 Recommended Links")
                for link in context_consistency["recommended_links"][:5]:
                    report_lines.append(f"- {link}")
                report_lines.append("")
        
        report_lines.extend([
            "---",
            "",
            "📊 **Token Usage Log**: `outputs/gemini_meta_observer/token_usage.jsonl`"
        ])
        
        report_content = "\n".join(report_lines)
        
        # 리포트 저장
        report_file = self.output_dir / f"gemini_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_file.write_text(report_content, encoding="utf-8")
        
        # latest 심볼릭 링크
        latest_file = self.output_dir / "gemini_analysis_latest.md"
        if latest_file.exists():
            latest_file.unlink()
        latest_file.write_text(report_content, encoding="utf-8")
        
        print(f"📄 Report saved to {report_file}")
        return report_content


def main():
    parser = argparse.ArgumentParser(description="Gemini Meta Observer - Documentation & Context Analysis")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=get_workspace_root(),
        help="Workspace root directory"
    )
    parser.add_argument(
        "--model",
        default="models/gemini-2.0-flash-exp",
        help="Gemini model name"
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Only analyze documentation quality"
    )
    parser.add_argument(
        "--context-only",
        action="store_true",
        help="Only check context consistency"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Custom output directory"
    )
    
    args = parser.parse_args()
    
    # Observer 초기화
    observer = GeminiMetaObserver(
        workspace_root=args.workspace,
        model_name=args.model,
        output_dir=args.output
    )
    
    # 분석 대상 파일 수집
    workspace = args.workspace
    
    # Markdown/문서 파일 찾기
    doc_files = []
    for ext in ["*.md", "*.txt", "*.rst"]:
        doc_files.extend(workspace.glob(f"**/{ext}"))
    
    # .git, node_modules, .venv 제외
    doc_files = [
        f for f in doc_files
        if not any(part.startswith(".") or part in ["node_modules", ".venv", "__pycache__"]
                   for part in f.parts)
    ]
    
    print(f"📁 Found {len(doc_files)} documentation files")
    
    # 분석 실행
    doc_quality = None
    context_consistency = None
    
    if not args.context_only:
        doc_quality = observer.analyze_documentation_quality(doc_files[:10])
    
    if not args.docs_only:
        md_files = [f for f in doc_files if f.suffix == ".md"]
        context_consistency = observer.check_context_consistency(md_files[:15])
    
    # 리포트 생성
    report = observer.generate_report(doc_quality, context_consistency)
    
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    print("\n✅ Gemini Meta Observer analysis complete!")


if __name__ == "__main__":
    main()
