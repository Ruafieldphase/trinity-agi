
import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import cv2
from PIL import Image
import google.generativeai as genai

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ArchVideoAnalyzer")

class ArchVideoAnalyzer:
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        self.output_dir = Path("c:/workspace/agi/outputs/arch_analysis")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure Gemini
        # Note: In this environment, the API key is usually pre-configured or handled by the system
        # If explicitly needed, we would use os.environ.get('GEMINI_API_KEY')
        
    def extract_keyframes(self, interval_sec=30, max_frames=100):
        logger.info(f"Extracting frames from {self.video_path}...")
        cam = cv2.VideoCapture(str(self.video_path))
        fps = cam.get(cv2.CAP_PROP_FPS)
        total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Video duration: {duration:.2f}s, FPS: {fps}")
        
        frames_images = []
        current_time = 0
        
        while current_time < duration:
            cam.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
            ret, frame = cam.read()
            if ret:
                # Convert BGR to RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(rgb_frame)
                
                # Resize for context efficiency
                # Resize for context efficiency
                pil_img.thumbnail((1024, 1024))
                frames_images.append(pil_img)

                # Save all frames to disk for analysis relay
                frame_filename = f"frame_{len(frames_images)}.jpg"
                pil_img.save(self.output_dir / frame_filename)
                
                # Save first few frames for verification if needed
                if len(frames_images) <= 3:
                     pil_img.save(self.output_dir / f"check_frame_{len(frames_images)}.jpg")
            
            current_time += interval_sec
            if len(frames_images) >= max_frames:
                break
                
        cam.release()
        logger.info(f"Extracted {len(frames_images)} frames.")
        return frames_images

    async def analyze_with_gemini(self, frames):
        logger.info("Analyzing frames with Google AI Studio (GenAI)...")
        
        # Configure the key
        api_key = "YOUR_GOOGLE_API_KEY_HERE"
        genai.configure(api_key=api_key)
        
        # Use a model that we confirmed exists in the list
        model_name = 'gemini-2.0-flash'
        logger.info(f"Using model: {model_name}")
        model = genai.GenerativeModel(model_name)
            
        prompt = """
        Analyze this sequence of keyframes from an architectural modeling session in Blender.
        
        Goal: Understand the user's specific workflow for converting 2D CAD drawings into 3D models.
        
        Specific points of interest:
        1. Spatial Folding: Does the user 'stand up' (rotate 90 degrees) elevation drawings at the edges of the floor plan?
        2. FSD Process: Observe the 'Inference -> Execution -> Positioning -> Depth' loop.
        3. 적분상수 C (Integration Constant C): Look for any visual or textual references to 'C' or a fundamental constant used to determine wall heights, thicknesses, or structural offsets.
        4. Collection Management: How does the user toggle layers/collections to focus on specific faces of the building?
        
        Output a detailed JSON report:
        {
            "workflow_steps": ["step1", "step2", ...],
            "spatial_folding_confirmed": true/false,
            "constant_c_insight": "description of what C represents in this context",
            "modeling_rhythm": "description of the iterative process",
            "snapping_techniques": "observed snapping or alignment methods",
            "recommendations_for_automation": ["advice1", "advice2"]
        }
        """
        
        # Interleave prompt and images for GenAI
        content = [prompt]
        for i, img in enumerate(frames):
            # Convert to bytes for GenAI part format
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            content.append({"mime_type": "image/jpeg", "data": img_bytes})

        try:
            # GenAI generate_content is synchronous normally, but we call it here
            # In a real async loop we'd wrap it, but for a script it's fine.
            response = model.generate_content(
                content, 
                generation_config={"temperature": 0.1}
            )
            
            text = response.text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            return json.loads(text.strip())
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return None

    async def run(self):
        frames = self.extract_keyframes()
        if not frames:
            logger.error("No frames extracted.")
            return
            
        analysis = await self.analyze_with_gemini(frames)
        if analysis:
            report_path = self.output_dir / "arch_video_analysis_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=4, ensure_ascii=False)
            logger.info(f"✅ Analysis complete. Report saved to {report_path}")
            
            # Also generate a markdown summary
            md_path = self.output_dir / "arch_video_analysis_report.md"
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# 🏛️ Architectural Workflow Analysis Report\n\n")
                f.write(f"**Source**: {self.video_path.name}\n")
                f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"## 🌊 Workflow Insights\n\n")
                for step in analysis.get('workflow_steps', []):
                    f.write(f"- {step}\n")
                f.write(f"\n## 📏 Operational Constants (적분상수 C)\n\n")
                f.write(f"> {analysis.get('constant_c_insight', 'N/A')}\n\n")
                f.write(f"## 📐 Spatial Folding\n\n")
                f.write(f"- **Confirmed**: {'Yes' if analysis.get('spatial_folding_confirmed') else 'No'}\n")
                f.write(f"- **Rhythm**: {analysis.get('modeling_rhythm', 'N/A')}\n\n")
                f.write(f"## 🛠️ Automation Recommendations\n\n")
                for rec in analysis.get('recommendations_for_automation', []):
                    f.write(f"- {rec}\n")
            logger.info(f"✅ Markdown report saved to {md_path}")

if __name__ == "__main__":
    video = "E:/Backup/obs_recode/2026-01-04 12-31-31.mp4"
    analyzer = ArchVideoAnalyzer(video)
    asyncio.run(analyzer.run())
