import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

base = Path('d:/nas_backup/outputs')

# Keyword chart
df_kw = pd.read_csv(base / 'perple_6m_keyword_groups.csv')
if 'group' not in df_kw.columns:
    df_kw.columns = ['group', 'mentions']
df_kw = df_kw.sort_values('mentions', ascending=False)
plt.style.use('ggplot')
fig, ax = plt.subplots(figsize=(6, 4))
colors = ['#2f6fed', '#4fa3ff', '#7cc0ff', '#a6d4ff']
ax.bar(df_kw['group'], df_kw['mentions'], color=colors[:len(df_kw)])
ax.set_title('Perple Keyword Clusters (2025-04~09)')
ax.set_ylabel('Mentions')
for idx, val in enumerate(df_kw['mentions']):
    ax.text(idx, val + max(df_kw['mentions']) * 0.02, str(val), ha='center', fontsize=10)
fig.tight_layout()
fig.savefig(base / 'perple_keyword_chart.svg', transparent=True)
plt.close(fig)

# Model mix
df_model = pd.read_csv(base / 'perple_6m_model_counts.csv')
fig, ax = plt.subplots(figsize=(5.2, 5.2))
ax.pie(df_model['count'], labels=df_model['model'], autopct='%1.0f%%', startangle=90,
       colors=['#274690', '#576ca8', '#302b27', '#9db4c0', '#7c90a0', '#cbd5e0'])
ax.set_title('Perple Model Mix (2025-04~09)')
fig.savefig(base / 'perple_model_mix.svg', transparent=True)
plt.close(fig)
