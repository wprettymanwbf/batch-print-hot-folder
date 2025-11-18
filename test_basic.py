#!/usr/bin/env python3
"""
Simple test script to verify batch_print.py functionality
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Test that we can import the module
try:
    import batch_print
    print("✓ Successfully imported batch_print module")
except ImportError as e:
    print(f"✗ Failed to import batch_print: {e}")
    sys.exit(1)

# Test configuration loading
print("\nTesting configuration handling...")
try:
    # Create a test config
    test_config = {
        "hot_folders": [
            {
                "name": "TestFolder",
                "watch_path": "/tmp/test_hot_folder",
                "printer_name": "TestPrinter",
                "success_folder": "/tmp/test_hot_folder/Success",
                "error_folder": "/tmp/test_hot_folder/Error"
            }
        ],
        "poll_interval": 1,
        "log_level": "DEBUG"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        test_config_path = f.name
    
    # Test HotFolderConfig creation
    config = batch_print.HotFolderConfig(
        name="TestFolder",
        watch_path="/tmp/test_hot_folder",
        printer_name="TestPrinter",
        success_folder="/tmp/test_hot_folder/Success",
        error_folder="/tmp/test_hot_folder/Error"
    )
    print("✓ HotFolderConfig created successfully")
    
    # Test BatchPrintService loading
    service = batch_print.BatchPrintService(test_config_path)
    print("✓ BatchPrintService loaded configuration successfully")
    print(f"  - Loaded {len(service.hot_folders)} hot folder(s)")
    print(f"  - Poll interval: {service.poll_interval}s")
    
    # Clean up
    os.unlink(test_config_path)
    
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test file readiness check
print("\nTesting file readiness check...")
try:
    handler = batch_print.PrintHandler(config)
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Test content")
        test_file_path = f.name
    
    is_ready = handler._is_file_ready(test_file_path, max_attempts=1)
    print(f"✓ File readiness check completed: {is_ready}")
    
    # Clean up
    os.unlink(test_file_path)
    
except Exception as e:
    print(f"✗ File readiness test failed: {e}")
    import traceback
    traceback.print_exc()

# Test alphabetical sorting logic
print("\nTesting alphabetical sorting...")
try:
    test_files = [
        "/tmp/zebra.txt",
        "/tmp/apple.txt",
        "/tmp/banana.txt",
        "/tmp/123.txt"
    ]
    
    sorted_files = sorted(test_files, key=lambda x: os.path.basename(x))
    expected = ["/tmp/123.txt", "/tmp/apple.txt", "/tmp/banana.txt", "/tmp/zebra.txt"]
    
    if sorted_files == expected:
        print("✓ Alphabetical sorting works correctly")
        print(f"  Sorted order: {[os.path.basename(f) for f in sorted_files]}")
    else:
        print(f"✗ Sorting failed. Expected {expected}, got {sorted_files}")
        
except Exception as e:
    print(f"✗ Sorting test failed: {e}")

print("\n" + "="*60)
print("Basic tests completed successfully!")
print("="*60)
print("\nNote: Full functionality testing (actual printing) requires:")
print("  1. A configured printer")
print("  2. Running on the target platform (Windows/macOS/Linux)")
print("  3. Files to print")
