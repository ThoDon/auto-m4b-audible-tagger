#!/usr/bin/env python3
"""
Cleanup script to remove temporary files and invalid content from incoming folder
"""

import logging
from pathlib import Path
from typing import Tuple

def setup_cleanup_logging():
    """Setup logging for cleanup operations"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def cleanup_incoming_folder(directory: str = "incoming", auto_mode: bool = False) -> Tuple[int, int, int]:
    """
    Comprehensive cleanup of incoming folder:
    - Remove temporary files
    - Remove non-m4b files
    - Remove empty folders
    - Remove folders without m4b files
    """
    dir_path = Path(directory)
    logger = setup_cleanup_logging()
    
    if not dir_path.exists():
        logger.warning(f"Directory {directory} does not exist")
        return 0, 0, 0
    
    temp_files_removed = 0
    invalid_files_removed = 0
    empty_folders_removed = 0
    
    # Patterns to match temporary files
    temp_patterns = [
        "temp-*.m4b",
        "*_temp_*.m4b", 
        "*temp-*.m4b",
        "*.tmp",
        "*_tagged.m4b",
        "ap-*.m4b"
    ]
    
    logger.info(f"🧹 Starting cleanup of: {dir_path}")
    
    # Step 1: Remove temporary files
    logger.info("Step 1: Removing temporary files...")
    for pattern in temp_patterns:
        matching_files = list(dir_path.rglob(pattern))
        for temp_file in matching_files:
            try:
                temp_file.unlink()
                logger.info(f"✅ Removed temp file: {temp_file}")
                temp_files_removed += 1
            except Exception as e:
                logger.error(f"❌ Could not delete {temp_file}: {e}")
    
    # Step 2: Remove non-m4b files
    logger.info("Step 2: Removing non-m4b files...")
    for file_path in dir_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() != '.m4b':
            try:
                file_path.unlink()
                logger.info(f"✅ Removed non-m4b file: {file_path}")
                invalid_files_removed += 1
            except Exception as e:
                logger.error(f"❌ Could not delete {file_path}: {e}")
    
    # Step 3: Remove empty folders and folders without m4b files
    logger.info("Step 3: Removing empty folders and folders without m4b files...")
    folders_to_check = list(dir_path.rglob("*"))
    folders_to_check.sort(key=lambda x: len(x.parts), reverse=True)  # Process deepest folders first
    
    for folder_path in folders_to_check:
        if folder_path.is_dir() and folder_path != dir_path:
            # Check if folder is empty
            if not any(folder_path.iterdir()):
                try:
                    folder_path.rmdir()
                    logger.info(f"✅ Removed empty folder: {folder_path}")
                    empty_folders_removed += 1
                except Exception as e:
                    logger.error(f"❌ Could not remove empty folder {folder_path}: {e}")
            else:
                # Check if folder contains any m4b files
                m4b_files = list(folder_path.rglob("*.m4b"))
                if not m4b_files:
                    # Remove all contents and then the folder
                    try:
                        for item in folder_path.rglob("*"):
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                item.rmdir()
                        folder_path.rmdir()
                        logger.info(f"✅ Removed folder without m4b files: {folder_path}")
                        empty_folders_removed += 1
                    except Exception as e:
                        logger.error(f"❌ Could not remove folder {folder_path}: {e}")
    
    logger.info(f"🎉 Cleanup complete!")
    logger.info(f"   📁 Temp files removed: {temp_files_removed}")
    logger.info(f"   📄 Invalid files removed: {invalid_files_removed}")
    logger.info(f"   📂 Empty folders removed: {empty_folders_removed}")
    
    return temp_files_removed, invalid_files_removed, empty_folders_removed

def cleanup_temp_files(directory: str = "incoming"):
    """Legacy function for backward compatibility"""
    return cleanup_incoming_folder(directory, auto_mode=True)

if __name__ == "__main__":
    import sys
    
    # Check for auto mode flag
    auto_mode = "--auto" in sys.argv
    if auto_mode:
        sys.argv.remove("--auto")
    
    # Use command line argument if provided, otherwise default to "incoming"
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "incoming"
    
    if auto_mode:
        print(f"🧹 Automatic cleanup of: {target_dir}")
        cleanup_incoming_folder(target_dir, auto_mode=True)
    else:
        print(f"🧹 Audible Tagger - Folder Cleanup")
        print(f"Target directory: {target_dir}")
        print("This will remove:")
        print("  - Temporary files (temp-*.m4b, *.tmp, etc.)")
        print("  - Non-m4b files")
        print("  - Empty folders")
        print("  - Folders without m4b files")
        
        confirm = input("Proceed with cleanup? (y/n): ").strip().lower()
        if confirm == 'y':
            cleanup_incoming_folder(target_dir, auto_mode=False)
        else:
            print("Cleanup cancelled.") 