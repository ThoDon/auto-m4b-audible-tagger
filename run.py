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
   
        if len(sys.argv) > 2:
            file_path = sys.argv[2]
            print("🔧 Mutagen Tagging Test")
            print("=" * 30)
            
            tagger = AudibleTagger()
            
            # Test metadata
            test_metadata = {
                'title': 'Test Title',
                'author': 'Test Author',
                'narrator': 'Test Narrator',
                'description': 'Test Description',
                'series': 'Test Series',
                'series_part': '1',
                'asin': 'B00TEST123',
                'isbn': '978-0-123456-78-9',
                'copyright': 'Test Copyright 2024',
                'language': 'en',
                'format_type': 'Audiobook',
                'publisher_name': 'Test Publisher',
                'subtitle': 'Test Subtitle',
                'release_time': '2024-01-01',
                'genres': ['Fiction', 'Test'],
                'rating': '4.5',
                'is_adult_product': False
            }
            
            success = tagger.tag_with_mutagen(Path(file_path), test_metadata)
            
            if success:
                tagger.verify_mutagen_tags(Path(file_path), test_metadata)
            
            print("\n🎉 Mutagen testing complete!")
        else:
            print("Usage: python run.py --test-mutagen <file_path>")
    else:
        tagger = AudibleTagger()
        tagger.run() 