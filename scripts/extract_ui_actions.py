import os
import sys
import re
from pathlib import Path
import vertexai
from vertexai.generative_models import GenerativeModel

# Configuration
PROJECT_ID = "naeda-genesis"
LOCATION = "us-central1"
MODEL_NAME = "gemini-2.0-flash-exp"

INPUT_REPORT = Path(r"C:\workspace\agi\outputs\obs_learning\obs_learning_report.md")
OUTPUT_LIBRARY = Path(r"C:\workspace\agi\outputs\obs_learning\ui_action_library.md")

def init_vertex():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    return GenerativeModel(MODEL_NAME)

def parse_report(file_path):
    """Splits the report into sections by video."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
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
            current_video = None 
            
    return parsed_videos

def extract_actions_from_section(model, video_data):
    """Extracts UI action sequences from a video section."""
    print(f"Extracting actions from {video_data['video']}...")
    
    prompt = f"""
    You are an AI training specialist creating a "UI Action Library" for an autonomous agent.
    Your goal is to extract specific, reproducible **Action Sequences** from the screen recording log.
    
    Video File: {video_data['video']}
    
    Log Content:
    {video_data['content'][:30000]} 
    
    Focus ONLY on concrete UI interactions. Ignore general "thinking" or "planning" unless it involves a UI tool (e.g., writing a plan in a specific file).
    
    For each distinct task identified, extract:
    1. **Task Name**: (e.g., "Run Verification Script", "Open VS Code Terminal")
    2. **Context/Trigger**: When does the developer do this? (e.g., "After modifying a file")
    3. **Step-by-Step Actions**: Numbered list of specific actions. Be precise.
       - Bad: "Run the test."
       - Good: "1. Click on the Terminal tab. 2. Type `python scripts/verify.py`. 3. Press Enter."
    4. **Visual Cues**: What confirms the action? (e.g., "Terminal shows 'Exit code: 0'", "Green checkmark appears")
    
    Format the output as a list of these structured items.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error extracting from {video_data['video']}: {e}")
        return ""

def aggregate_library(model, extractions):
    """Aggregates individual extractions into a final library."""
    print("Aggregating Action Library...")
    
    combined_extractions = "\n\n".join([f"--- Source: {s['video']} ---\n{s['extraction']}" for s in extractions])
    
    prompt = f"""
    You are compiling a "Master UI Action Library" for an AGI.
    Below are raw extracted action sequences from multiple sessions.
    
    Consolidate these into a clean, de-duplicated, and organized library.
    Group similar actions together (e.g., "Terminal Operations", "File Management", "Browser Interactions").
    
    Input Data:
    {combined_extractions}
    
    Output Format (Markdown):
    # AGI UI Action Library
    
    ## [Category Name] (e.g., Terminal Operations)
    
    ### [Action Name] (e.g., Run Python Script)
    **Context**: [When to use this]
    **Steps**:
    1. [Step 1]
    2. [Step 2]
    ...
    **Visual Confirmation**: [What to look for]
    
    (Repeat for all unique actions)
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error aggregating library: {e}")
        return f"Error aggregating library: {e}"

def main():
    if not INPUT_REPORT.exists():
        print(f"Report file not found: {INPUT_REPORT}")
        return

    model = init_vertex()
    videos = parse_report(INPUT_REPORT)
    print(f"Found {len(videos)} video sections.")
    
    extractions = []
    for video in videos:
        extraction = extract_actions_from_section(model, video)
        if extraction:
            extractions.append({
                "video": video["video"],
                "extraction": extraction
            })
        
    final_library = aggregate_library(model, extractions)
    
    with open(OUTPUT_LIBRARY, "w", encoding="utf-8") as f:
        f.write(final_library)
        
    print(f"Action Library generated at {OUTPUT_LIBRARY}")

if __name__ == "__main__":
    main()
