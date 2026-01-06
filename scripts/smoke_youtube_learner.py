import os
import asyncio

from rpa.youtube_learner import YouTubeLearner, YouTubeLearnerConfig


async def main():
    url = os.environ.get("YT_TEST_URL", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    cfg = YouTubeLearnerConfig(max_frames=1, frame_interval=30.0)
    yl = YouTubeLearner(cfg)

    video = await yl._fetch_video_metadata(url)
    vid = yl._extract_video_id(url)
    subs = await yl._extract_subtitles(vid)

    print("TITLE:", getattr(video, "title", "")[:120])
    print("DURATION:", getattr(video, "length", 0))
    print("SUBS_COUNT:", len(subs))

    if os.environ.get("WITH_FRAMES") == "1":
        frames = await yl._extract_frames(video)
        print("FRAMES_COUNT:", len(frames))


if __name__ == "__main__":
    asyncio.run(main())
