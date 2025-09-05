"""
Test script to verify the fixed DownloadManager.
"""

import os
import tempfile
import shutil
from config.manager import ConfigManager
from core.downloader import DownloadManager

def test_base_folder_fix():
    """Test that different base folders are maintained per download."""
    print("Testing base folder fix for the download manager...")
    
    # Create two temporary folders for different series
    temp_dir = tempfile.mkdtemp()
    try:
        series_a_folder = os.path.join(temp_dir, "Series_A")
        series_b_folder = os.path.join(temp_dir, "Series_B")
        os.makedirs(series_a_folder)
        os.makedirs(series_b_folder)
        
        # Create a config and download manager
        config_manager = ConfigManager()
        download_manager = DownloadManager(config_manager)
        
        # Create mock data for Series A
        series_a_files = [
            ("http://example.com/series_a/s1e1.mkv", "Season1/episode1.mkv"),
            ("http://example.com/series_a/s1e2.mkv", "Season1/episode2.mkv")
        ]
        
        # Create mock data for Series B
        series_b_files = [
            ("http://example.com/series_b/s1e1.mkv", "Season1/episode1.mkv"),
            ("http://example.com/series_b/s1e2.mkv", "Season1/episode2.mkv")
        ]
        
        # Mock size calculation for Series A
        print(f"\nAdding Series A files to: {series_a_folder}")
        download_manager._on_size_calc_finished(
            total_size=200000000,
            file_sizes_map={url: 100000000 for url, _ in series_a_files},
            file_tuples=series_a_files,
            base_folder=series_a_folder
        )
        
        # Mock size calculation for Series B
        print(f"\nAdding Series B files to: {series_b_folder}")
        download_manager._on_size_calc_finished(
            total_size=200000000,
            file_sizes_map={url: 100000000 for url, _ in series_b_files},
            file_tuples=series_b_files,
            base_folder=series_b_folder
        )
        
        # Verify each download has the correct base folder
        print("\nVerifying base folders for each download:")
        success = True
        
        # Check all downloads
        for download in download_manager.downloads:
            url = download['url']
            is_series_a = 'series_a' in url
            expected_folder = series_a_folder if is_series_a else series_b_folder
            series_name = "Series A" if is_series_a else "Series B"
            
            print(f"\n  {os.path.basename(download['rel_path'])} ({series_name}):")
            print(f"    Expected folder: {expected_folder}")
            print(f"    Actual folder:   {download['base_folder']}")
            print(f"    File path:       {download['file_path']}")
            
            if download['base_folder'] != expected_folder:
                print("    ERROR: Wrong folder!")
                success = False
            else:
                print("    ✓ Correct folder")
        
        # Check download queue too
        print("\nVerifying download queue:")
        for i, (url, rel_path, base_folder) in enumerate(download_manager.download_queue):
            is_series_a = 'series_a' in url
            expected_folder = series_a_folder if is_series_a else series_b_folder
            series_name = "Series A" if is_series_a else "Series B"
            
            print(f"\n  Queue item {i+1}: {os.path.basename(rel_path)} ({series_name}):")
            print(f"    Expected folder: {expected_folder}")
            print(f"    Actual folder:   {base_folder}")
            
            if base_folder != expected_folder:
                print("    ERROR: Wrong folder in queue!")
                success = False
            else:
                print("    ✓ Correct folder")
        
        if success:
            print("\n✅ BUG FIX SUCCESSFUL! Each download maintains its correct destination folder.")
        else:
            print("\n❌ BUG FIX FAILED! Some downloads have incorrect folders.")
        
    finally:
        # Clean up temp directories
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_base_folder_fix()
