# Architecture Automation: Project Survival & Dream

**Goal:** Automate the conversion of 2D architectural blueprints into 3D visualizations (Renderings & Models) using AGI, Stable Diffusion, and Blender.

## 1. Project Structure
- `inputs/`: Drop CAD images/blueprints here.
- `outputs/`: 
    - `renders/`: AI-generated visualizations.
    - `models/`: Blender `.blend` or `.obj` files.
- `scripts/`: Python automation scripts.

## 2. Phase 1: AI Rendering Pipeline (The "Quick Win")
**Objective:** Turn a rough sketch/blueprint into a high-quality render in < 1 minute.
- **Tools:** Stable Diffusion WebUI (Automatic1111) API + ControlNet.
- **Workflow:**
    1. `blueprint_watcher.py` detects new file in `inputs/`.
    2. Binoche analyzes the image (Vision) to determine "Building Type" & "Atmosphere".
    3. Generate Prompt: "Modern architectural rendering, glass facade, sunset..."
    4. Send to SD API with ControlNet (MLSD/Canny) enabled.
    5. Save result to `outputs/renders/`.

## 3. Phase 2: 3D Modeling Automation (The "Architect's Power")
**Objective:** Convert 2D floor plan into 3D walls/windows automatically.
- **Tools:** Blender Python API (`bpy`) + OpenCV.
- **Workflow:**
    1. `blueprint_to_wall.py` reads the floor plan.
    2. OpenCV detects lines (walls) and determines thickness.
    3. Blender script extrudes walls to 2400mm height.
    4. Detects specific markers for Windows/Doors and cuts holes.
    5. Exports `.blend` file.

## 4. Requirements
- Local GPU with Stable Diffusion WebUI installed (OR use an API key if local not available).
- Blender 3.6+ installed.
- Python libraries: `requests`, `opencv-python`, `watchdog`.

---
**"We build the world, then the world builds us."**
