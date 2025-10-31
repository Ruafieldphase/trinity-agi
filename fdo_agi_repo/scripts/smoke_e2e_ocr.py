import asyncio
from rpa.e2e_pipeline import E2EPipeline, E2EConfig
from rpa.youtube_learner import YouTubeLearnerConfig


async def main():
    # Light-weight OCR config: few frames, larger interval
    yt_cfg = YouTubeLearnerConfig(
        enable_ocr=True,
        max_ocr_frames=2,
        frame_interval=10.0,
        max_frames=10,
    )
    cfg = E2EConfig(
        enable_auto_execution=False,
        youtube_config=yt_cfg,
    )

    p = E2EPipeline(cfg)
    task = await p.run_learning_task("https://www.youtube.com/watch?v=kqtD5dpn9C8")
    print({
        "status": task.status,
        "steps": len(task.execution_steps or []),
    })


if __name__ == "__main__":
    asyncio.run(main())
