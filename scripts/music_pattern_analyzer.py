#!/usr/bin/env python3
"""
Music Pattern Analyzer - Detect recurring patterns in music files
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import hashlib

def load_music_index(workspace_root):
    """Load music index from outputs"""
    index_path = os.path.join(workspace_root, "outputs", "music_index.json")
    if not os.path.exists(index_path):
        print(f"❌ Music index not found at {index_path}")
        print("   Run: scripts/build_music_index.ps1 first")
        return None
    
    with open(index_path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)

def analyze_file_patterns(music_files):
    """Analyze patterns in music file collection"""
    patterns = {
        "by_extension": {},
        "by_size_range": {},
        "by_directory": {},
        "by_creators": {},
        "by_rhythm_state": {},
        "by_theme": {}
    }
    
    for file_info in music_files:
        # Extension distribution
        filename = file_info.get('filename', file_info.get('name', ''))
        ext = os.path.splitext(filename)[1] if filename else 'unknown'
        patterns['by_extension'][ext] = patterns['by_extension'].get(ext, 0) + 1
        
        # Size ranges (in MB)
        size_mb = file_info.get('size_mb', 0)
        if size_mb < 1:
            range_key = "< 1 MB"
        elif size_mb < 5:
            range_key = "1-5 MB"
        elif size_mb < 10:
            range_key = "5-10 MB"
        elif size_mb < 50:
            range_key = "10-50 MB"
        else:
            range_key = "> 50 MB"
        patterns['by_size_range'][range_key] = patterns['by_size_range'].get(range_key, 0) + 1
        
        # Creators
        creators = file_info.get('creators', [])
        for creator in creators:
            patterns['by_creators'][creator] = patterns['by_creators'].get(creator, 0) + 1
        
        # Rhythm states
        rhythm_states = file_info.get('rhythm_states', [])
        for state in rhythm_states:
            patterns['by_rhythm_state'][state] = patterns['by_rhythm_state'].get(state, 0) + 1
        
        # Themes
        theme = file_info.get('theme', 'unknown')
        patterns['by_theme'][theme] = patterns['by_theme'].get(theme, 0) + 1
    
    return patterns

def detect_naming_conventions(music_files):
    """Detect naming patterns (e.g., numbered tracks, dates)"""
    conventions = {
        "has_numbers": 0,
        "has_dates": 0,
        "has_underscores": 0,
        "has_dashes": 0,
        "all_lowercase": 0,
        "all_uppercase": 0
    }
    
    for file_info in music_files:
        name = file_info.get('name', '')
        
        if any(c.isdigit() for c in name):
            conventions['has_numbers'] += 1
        if any(c in name for c in ['_']):
            conventions['has_underscores'] += 1
        if any(c in name for c in ['-']):
            conventions['has_dashes'] += 1
        if name.islower():
            conventions['all_lowercase'] += 1
        if name.isupper():
            conventions['all_uppercase'] += 1
    
    return conventions

def check_reaper_project(music_dir):
    """Check if Reaper project file exists"""
    reaper_files = []
    for root, dirs, files in os.walk(music_dir):
        for file in files:
            if file.lower().endswith(('.rpp', '.rpp-bak')):
                reaper_files.append({
                    'path': os.path.join(root, file),
                    'name': file,
                    'size': os.path.getsize(os.path.join(root, file))
                })
    return reaper_files

def main():
    parser = argparse.ArgumentParser(description="Analyze music file patterns")
    parser.add_argument('--music-dir', default=None, help="Music directory to analyze")
    parser.add_argument('--reaper-check', action='store_true', help="Check for Reaper project files")
    args = parser.parse_args()
    
    # Determine workspace root
    script_dir = Path(__file__).parent
    workspace_root = script_dir.parent
    
    print("🎵 Music Pattern Analyzer")
    print("=" * 60)
    
    # Load music index
    music_index = load_music_index(workspace_root)
    if not music_index:
        return 1
    
    # Try both 'music_library' and 'files' keys
    music_files = music_index.get('music_library', music_index.get('files', []))
    print(f"📊 Loaded {len(music_files)} music files from index")
    
    # Analyze patterns
    print("\n🔍 Analyzing patterns...")
    patterns = analyze_file_patterns(music_files)
    naming_conventions = detect_naming_conventions(music_files)
    
    # Check for Reaper projects if requested
    reaper_projects = []
    if args.reaper_check and args.music_dir:
        print(f"\n🎸 Checking for Reaper projects in {args.music_dir}...")
        reaper_projects = check_reaper_project(args.music_dir)
    
    # Build analysis report
    analysis = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(music_files),
        'patterns': patterns,
        'naming_conventions': naming_conventions,
        'reaper_projects': reaper_projects,
        'summary': {
            'most_common_extension': max(patterns['by_extension'].items(), key=lambda x: x[1])[0] if patterns['by_extension'] else None,
            'most_common_size_range': max(patterns['by_size_range'].items(), key=lambda x: x[1])[0] if patterns['by_size_range'] else None,
            'unique_directories': len(patterns['by_directory'])
        }
    }
    
    # Save analysis
    output_path = os.path.join(workspace_root, "outputs", "music_pattern_analysis.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analysis saved to: {output_path}")
    
    # Print summary
    print("\n📈 Pattern Summary:")
    print(f"  • Total files: {analysis['total_files']}")
    print(f"  • Most common extension: {analysis['summary']['most_common_extension']}")
    print(f"  • Most common size range: {analysis['summary']['most_common_size_range']}")
    print(f"  • Unique directories: {analysis['summary']['unique_directories']}")
    
    if reaper_projects:
        print(f"\n🎸 Found {len(reaper_projects)} Reaper project(s):")
        for proj in reaper_projects:
            print(f"  • {proj['name']}")
    
    print("\n✨ Pattern analysis complete!")
    return 0

if __name__ == '__main__':
    sys.exit(main())
