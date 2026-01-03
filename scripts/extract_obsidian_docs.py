"""
Obsidian 문서 추출 스크립트
"""
import pathlib
import json

vault_path = pathlib.Path(r"C:\\workspace\\agi\Obsidian_Vault\Nas_Obsidian_Vault")

target_files = [
    "✨ 〈Core 선언문〉.md",
    "🌿 Resonance Cue – Obsidian Personal Rhythm.md",
    "🌱 이어내다 씨앗 코덱스 (v4.1).md",
    "codex_F 색인작업.md"
]

output = {}

for fname in target_files:
    fpath = vault_path / fname
    if fpath.exists():
        try:
            content = fpath.read_text(encoding='utf-8')
            # 첫 200줄만
            lines = content.split('\n')[:200]
            output[fname] = '\n'.join(lines)
            print(f"✓ {fname}: {len(lines)} lines")
        except Exception as e:
            print(f"✗ {fname}: {e}")
    else:
        print(f"✗ {fname}: 파일 없음")

# JSON 저장
out_path = pathlib.Path(r"c:\workspace\agi\outputs\obsidian_docs_extract.json")
out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')

print(f"\n저장: {out_path}")
print(f"총 {len(output)}개 문서 추출")
