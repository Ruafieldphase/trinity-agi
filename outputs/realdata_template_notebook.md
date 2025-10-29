# Flowing Information – 데이터 실험 템플릿

This notebook offers a scaffold for importing real-world empathy/
interaction logs and running them through the Flowing Information
analysis pipeline.

1. **Setup**
    ```python
    import pandas as pd
    import matplotlib.pyplot as plt

    from pathlib import Path

    DATA = Path('data/your_log.csv')  # update path
    df = pd.read_csv(DATA)
    df.head()
    ```

2. **Normalize day / time fields**
    ```python
    df['day'] = pd.to_datetime(df['timestamp']).dt.day_name()
    df['step'] = range(len(df))
    ```

3. **Run metrics**
    ```python
    from lumen_realdata_template import Measurement, summarize, compute_horizon_flags

    measurements = [
        Measurement(step=row['step'], day=row['day'], info=row['info'], resonance=row['resonance'],
                    entropy=row['entropy'], logic=row['logic'], ethics=row['ethics'], horizon=row.get('horizon'))
        for _, row in df.iterrows()
    ]
    horizon_flags = compute_horizon_flags(measurements, threshold=0.95)
    summarize(measurements, horizon_flags)
    ```

4. **Visualize**
    ```python
    plt.figure(figsize=(12, 4))
    plt.plot(df['step'], df['info'], label='info density')
    plt.plot(df['step'], df['resonance'], label='resonance')
    plt.plot(df['step'], df['entropy'], label='entropy')
    plt.legend(); plt.grid(alpha=0.3)
    ```

5. **Compare vs simulation**
    ```python
    sim = pd.read_csv('d:/nas_backup/outputs/lumen_auto_eval_runs.csv')
    sim.groupby('day')['info'].mean()
    ```

6. **Next Steps**
    - Adjust threshold / sensitivity per dataset
    - Integrate per-phase emotion tags (Love~Peace) and evaluate mapping alignment
    - Feed summarized metrics back into conscious_resonance_map JSON for combined dashboards
