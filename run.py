#!/usr/bin/env python3
"""
Launcher script for Audible Tagger
Runs the main tagger from the scripts directory
"""

import sys
from pathlib import Path

# Add scripts directory to Python path
scripts_dir = Path(__file__).parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import and run the tagger
from tagger import AudibleTagger

if __name__ == "__main__":
    # Check if cleaning up temporary files
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        from cleanup import cleanup_incoming_folder
        target_dir = sys.argv[2] if len(sys.argv) > 2 else "incoming"
        auto_mode = "--auto" in sys.argv
        cleanup_incoming_folder(target_dir, auto_mode=auto_mode)
    # Check if testing cover art
    elif len(sys.argv) > 1 and sys.argv[1] == "--test-cover":
        tagger = AudibleTagger()
        if len(sys.argv) > 2:
            tagger.test_cover_art(sys.argv[2])
        else:
            print("Usage: python run.py --test-cover <file_path>")

    # Check if testing ffmpeg
    elif len(sys.argv) > 1 and sys.argv[1] == "--test-ffmpeg":
        if len(sys.argv) > 2:
            file_path = sys.argv[2]
            print("🔧 ffmpeg Tagging Test")
            print("=" * 30)
            
            tagger = AudibleTagger()
            
            # Test metadata
            test_metadata = {
                'title': 'Test Title',
                'author': 'Test Author',
                'narrator': 'Test Narrator',
                'description': 'Test Description',
                'series': 'Test Series',
                'series_part': '1'
            }
            
            success = tagger.tag_with_ffmpeg(Path(file_path), test_metadata)
            
            if success:
                tagger.verify_ffmpeg_tags(Path(file_path), test_metadata)
            
            print("\n🎉 ffmpeg testing complete!")
        else:
            print("Usage: python run.py --test-ffmpeg <file_path>")
    else:
        tagger = AudibleTagger()
        tagger.run() 