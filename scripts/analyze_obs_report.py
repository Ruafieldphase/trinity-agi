import os
import sys
import re
from pathlib import Path
from workspace_root import get_workspace_root
from datetime import datetime
import vertexai
from vertexai.generative_models import GenerativeModel

# Configuration
PROJECT_ID = "naeda-genesis"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-exp"

WORKSPACE_ROOT = get_workspace_root()
INPUT_REPORT = WORKSPACE_ROOT / "outputs" / "obs_learning" / "obs_learning_report.md"
OUTPUT_INSIGHTS = WORKSPACE_ROOT / "outputs" / "obs_learning" / "obs_insights.md"

def init_vertex():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    return GenerativeModel(MODEL_NAME)

def parse_report(file_path):
    """Splits the report into sections by video."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split by "## Video:"
    sections = re.split(r'(^## Video: .*$)', content, flags=re.MULTILINE)
    
    parsed_videos = []
    current_video = None
    
    for section in sections:
        if section.startswith("## Video:"):
            current_video = section.strip().replace("## Video: ", "")
        elif current_video and section.strip():
            parsed_videos.append({
                "video": current_video,
                "content": section.strip()
            })
            current_video = None # Reset for next pair
            
    return parsed_videos

def analyze_video_section(model, video_data):
    """Analyzes a single video section."""
    print(f"Analyzing {video_data['video']}...")
    
    prompt = f"""
    You are an expert behavioral analyst and AI researcher.
    Analyze the following log of screen activity from a developer's workspace recording.
    
    Video File: {video_data['video']}
    
    Log Content:
    {video_data['content'][:30000]} # Truncate if too long, though flash model has large context
    
    Please extract the following in a structured format:
    1. **Main Project/Task**: What is the developer primarily working on?
    2. **Key Activities**: List the specific actions (e.g., Debugging X, Writing Y, Researching Z).
    3. **Tools & Environment**: What software, websites, or tools are visible?
    4. **Context & Notes**: Any specific text, code snippets, or notes that reveal the "why" or "how".
    5. **Atmosphere/State**: Describe the developer's focus, emotional state (if inferable), or working style (e.g., chaotic, focused, multitasking).
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error analyzing {video_data['video']}: {e}")
        return f"Error analyzing {video_data['video']}: {e}"

def aggregate_insights(model, summaries):
    """Aggregates individual video summaries into a final report."""
    print("Aggregating insights...")
    
    combined_summaries = "\n\n".join([f"--- Analysis of {s['video']} ---\n{s['analysis']}" for s in summaries])
    
    prompt = f"""
    You are an AGI system trying to understand your creator/collaborator.
    Below are analyses of multiple screen recording sessions of the developer.
    
    Synthesize these into a comprehensive "Developer Persona & Workflow Analysis" report.
    
    Input Summaries:
    {combined_summaries}
    
    Output Format (Markdown):
    # Developer Persona & Workflow Insights
    
    ## Executive Summary
    (Brief overview of who the developer is and what they are building)
    
    ## Core Projects & Objectives
    (Detailed breakdown of the main projects like 'Antigravity', 'AGI', etc.)
    
    ## Workflow & Habits
    (How do they work? Multitasking? Music? Research style? Debugging patterns?)
    
    ## Toolchain & Environment
    (What is their stack? VS Code, specific libraries, OS, etc.)
    
    ## Cognitive Style & Atmosphere
    (Are they structured? Exploratory? Do they struggle with specific things? What is the 'vibe'?)
    
    ## Key Context for AGI
    (What should the AGI remember to better assist this user? e.g., "They prefer X", "They are working on Y feature")
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error aggregating insights: {e}")
        return f"Error aggregating insights: {e}"

def main():
    if not INPUT_REPORT.exists():
        print(f"Report file not found: {INPUT_REPORT}")
        return

    model = init_vertex()
    videos = parse_report(INPUT_REPORT)
    print(f"Found {len(videos)} video sections.")
    
    summaries = []
    for video in videos:
        analysis = analyze_video_section(model, video)
        summaries.append({
            "video": video["video"],
            "analysis": analysis
        })
        
    final_report = aggregate_insights(model, summaries)
    
    with open(OUTPUT_INSIGHTS, "w", encoding="utf-8") as f:
        f.write(final_report)
        
    print(f"Insights generated at {OUTPUT_INSIGHTS}")

if __name__ == "__main__":
    main()
