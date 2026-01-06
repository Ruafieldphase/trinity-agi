"""
Core Resonance Metrics Visualization
포트폴리오용 Coherence 및 Entities Phase 차트 생성
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from pathlib import Path
from workspace_root import get_workspace_root

# 한글 폰트 설정 (Windows 기본 폰트)
matplotlib.rc('font', family='Malgun Gothic')
matplotlib.rcParams['axes.unicode_minus'] = False

def load_metrics(csv_path):
    """메트릭 CSV 로드"""
    df = pd.read_csv(csv_path)
    return df

def load_entities(csv_path):
    """엔티티 CSV 로드"""
    df = pd.read_csv(csv_path)
    return df

def plot_coherence_timeline(df, output_path):
    """Coherence 타임라인 그래프"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Coherence 플롯
    ax.plot(df['t_idx'], df['coherence'], 
            linewidth=2, color='#2E7D32', label='Coherence', marker='o', markersize=4)
    
    # 건강 범위 표시 (0.7~1.0)
    ax.axhspan(0.7, 1.0, alpha=0.1, color='green', label='건강 범위 (0.7~1.0)')
    ax.axhline(y=0.7, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    
    ax.set_xlabel('Tick', fontsize=12, fontweight='bold')
    ax.set_ylabel('Coherence', fontsize=12, fontweight='bold')
    ax.set_title('Core Resonance Loop - Coherence Timeline (50 Ticks)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0.6, 1.05)
    
    # 통계 정보 추가
    mean_coh = df['coherence'].mean()
    min_coh = df['coherence'].min()
    max_coh = df['coherence'].max()
    
    stats_text = f'Mean: {mean_coh:.3f} | Min: {min_coh:.3f} | Max: {max_coh:.3f}'
    ax.text(0.5, 0.02, stats_text, transform=ax.transAxes, 
            fontsize=10, ha='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Coherence 그래프 저장: {output_path}")
    plt.close()

def plot_dissonance_timeline(df, output_path):
    """Dissonance 타임라인 그래프"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Dissonance 플롯 (컬럼명 수정)
    dissonance_col = 'dissonance' if 'dissonance' in df.columns else 'dissonance_rate'
    ax.plot(df['t_idx'], df[dissonance_col], 
            linewidth=2, color='#C62828', label='Dissonance', marker='o', markersize=4)
    
    # 안전 범위 표시 (0~0.1)
    ax.axhspan(0.0, 0.1, alpha=0.1, color='green', label='안전 범위 (0~0.1)')
    ax.axhline(y=0.1, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    
    ax.set_xlabel('Tick', fontsize=12, fontweight='bold')
    ax.set_ylabel('Dissonance', fontsize=12, fontweight='bold')
    ax.set_title('Core Resonance Loop - Dissonance Timeline (50 Ticks)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # 통계 정보 추가
    mean_dis = df[dissonance_col].mean()
    max_dis = df[dissonance_col].max()
    
    stats_text = f'Mean: {mean_dis:.4f} | Max: {max_dis:.4f}'
    ax.text(0.5, 0.95, stats_text, transform=ax.transAxes, 
            fontsize=10, ha='center', va='top', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Dissonance 그래프 저장: {output_path}")
    plt.close()

def plot_entities_phase(df, output_path):
    """엔티티별 Phase 변화 차트"""
    # 페르소나 엔티티만 필터링 (소문자)
    personas = ['Core', 'elo', 'sena', 'gitco']
    df_personas = df[df['id'].isin(personas)]
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    colors = {
        'Core': '#1976D2',   # 파랑 (주도자)
        'elo': '#388E3C',   # 초록 (관찰자)
        'sena': '#F57C00',  # 주황 (중재자)
        'gitco': '#7B1FA2'  # 보라 (실행자)
    }
    
    persona_names = {'Core': 'Core', 'elo': 'Elo', 'sena': 'Sena', 'gitco': 'Gitco'}
    
    for persona in personas:
        data = df_personas[df_personas['id'] == persona]
        ax.plot(data['t_idx'], data['phase'], 
                linewidth=2, label=persona_names[persona], color=colors.get(persona, 'gray'),
                marker='o', markersize=3)
    
    ax.set_xlabel('Tick', fontsize=12, fontweight='bold')
    ax.set_ylabel('Phase (radians)', fontsize=12, fontweight='bold')
    ax.set_title('Core Resonance Loop - Persona Phase Synchronization', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', fontsize=11, ncol=2)
    ax.grid(True, alpha=0.3)
    
    # Phase 범위 표시 (0~2π)
    ax.axhline(y=0, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(y=np.pi, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    ax.axhline(y=2*np.pi, color='gray', linestyle=':', linewidth=1, alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ Entities Phase 차트 저장: {output_path}")
    plt.close()

def plot_combined_metrics(df, output_path):
    """Coherence + Dissonance 통합 그래프"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    
    # Coherence
    ax1.plot(df['t_idx'], df['coherence'], 
             linewidth=2, color='#2E7D32', label='Coherence', marker='o', markersize=3)
    ax1.axhspan(0.7, 1.0, alpha=0.1, color='green')
    ax1.axhline(y=0.7, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax1.set_ylabel('Coherence', fontsize=12, fontweight='bold')
    ax1.set_title('Core Resonance Loop - 통합 메트릭 (50 Ticks)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='lower right', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0.6, 1.05)
    
    # Dissonance
    dissonance_col = 'dissonance' if 'dissonance' in df.columns else 'dissonance_rate'
    ax2.plot(df['t_idx'], df[dissonance_col], 
             linewidth=2, color='#C62828', label='Dissonance', marker='o', markersize=3)
    ax2.axhspan(0.0, 0.1, alpha=0.1, color='green')
    ax2.axhline(y=0.1, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax2.set_xlabel('Tick', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Dissonance', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✅ 통합 메트릭 그래프 저장: {output_path}")
    plt.close()

def generate_summary_report(metrics_df, entities_df, output_path):
    """메트릭 요약 리포트 생성"""
    report = []
    report.append("# Core Resonance Loop - 실행 메트릭 요약")
    report.append("")
    report.append("## 전체 통계")
    report.append("")
    
    # Coherence 통계
    report.append("### Coherence")
    report.append(f"- **평균**: {metrics_df['coherence'].mean():.4f}")
    report.append(f"- **최소**: {metrics_df['coherence'].min():.4f}")
    report.append(f"- **최대**: {metrics_df['coherence'].max():.4f}")
    report.append(f"- **표준편차**: {metrics_df['coherence'].std():.4f}")
    report.append(f"- **건강 범위(0.7~1.0) 유지율**: {(metrics_df['coherence'] >= 0.7).sum() / len(metrics_df) * 100:.1f}%")
    report.append("")
    
    # Dissonance 통계
    dissonance_col = 'dissonance' if 'dissonance' in metrics_df.columns else 'dissonance_rate'
    report.append("### Dissonance")
    report.append(f"- **평균**: {metrics_df[dissonance_col].mean():.6f}")
    report.append(f"- **최대**: {metrics_df[dissonance_col].max():.6f}")
    report.append(f"- **안전 범위(0~0.1) 유지율**: {(metrics_df[dissonance_col] <= 0.1).sum() / len(metrics_df) * 100:.1f}%")
    report.append("")
    
    # 페르소나 통계
    report.append("## 페르소나별 통계")
    report.append("")
    personas = ['Core', 'elo', 'sena', 'gitco']
    persona_names = {'Core': 'Core', 'elo': 'Elo', 'sena': 'Sena', 'gitco': 'Gitco'}
    for persona in personas:
        data = entities_df[entities_df['id'] == persona]
        if len(data) > 0:
            report.append(f"### {persona_names[persona]}")
            report.append(f"- **평균 Amplitude**: {data['amp'].mean():.4f}")
            report.append(f"- **평균 Phase**: {data['phase'].mean():.4f}")
            report.append(f"- **평균 Bandwidth**: {data['bandwidth'].mean():.4f}")
            report.append(f"- **그룹**: {data['group'].iloc[0] if len(data) > 0 else 'N/A'}")
            report.append("")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    print(f"✅ 요약 리포트 저장: {output_path}")

def main():
    # 파일 경로
    import sys
    workspace_root = get_workspace_root()
    sys.path.insert(0, str(workspace_root))
    if (workspace_root / "fdo_agi_repo").exists():
        sys.path.insert(0, str(workspace_root / "fdo_agi_repo"))
    workspace = workspace_root
    
    metrics_path = workspace / "outputs" / "core_metrics.csv"
    entities_path = Path("D:/nas_backup/outputs/core_entities.csv")
    
    output_dir = Path("D:/nas_backup/docs/core_charts")
    output_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Core Resonance Metrics Visualization")
    print("=" * 60)
    print()
    
    # 데이터 로드
    print("📊 데이터 로딩...")
    metrics_df = load_metrics(metrics_path)
    entities_df = load_entities(entities_path)
    print(f"  - Metrics: {len(metrics_df)} rows")
    print(f"  - Entities: {len(entities_df)} rows")
    print()
    
    # 그래프 생성
    print("📈 그래프 생성 중...")
    plot_coherence_timeline(metrics_df, output_dir / "coherence_timeline.png")
    plot_dissonance_timeline(metrics_df, output_dir / "dissonance_timeline.png")
    plot_entities_phase(entities_df, output_dir / "entities_phase.png")
    plot_combined_metrics(metrics_df, output_dir / "combined_metrics.png")
    print()
    
    # 요약 리포트
    print("📝 요약 리포트 생성 중...")
    generate_summary_report(metrics_df, entities_df, output_dir / "metrics_summary.md")
    print()
    
    print("=" * 60)
    print("✅ 시각화 완료!")
    print(f"📁 출력 디렉토리: {output_dir}")
    print("=" * 60)

if __name__ == "__main__":
    main()
