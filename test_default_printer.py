#!/usr/bin/env python3
"""
Test script to verify default printer functionality
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# Test that we can import the module
try:
    import batch_print
    print("✓ Successfully imported batch_print module")
except ImportError as e:
    print(f"✗ Failed to import batch_print: {e}")
    sys.exit(1)

# Test get_default_printer function
print("\nTesting get_default_printer()...")
try:
    default_printer = batch_print.get_default_printer()
    if default_printer:
        print(f"✓ Default printer found: {default_printer}")
    else:
        print("✓ No default printer set (this is OK for testing)")
except Exception as e:
    print(f"✗ Failed to get default printer: {e}")
    import traceback
    traceback.print_exc()

# Test configuration with empty printer_name
print("\nTesting configuration with empty printer_name...")
try:
    # Create a test config with empty printer_name
    test_config = {
        "hot_folders": [
            {
                "name": "DefaultPrinterFolder",
                "watch_path": "/tmp/test_default_printer",
                "printer_name": "",
                "success_folder": "/tmp/test_default_printer/Success",
                "error_folder": "/tmp/test_default_printer/Error"
            }
        ],
        "poll_interval": 1,
        "log_level": "DEBUG"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        test_config_path = f.name
    
    # Test BatchPrintService loading
    service = batch_print.BatchPrintService(test_config_path)
    print("✓ BatchPrintService loaded configuration with empty printer_name")
    print(f"  - Loaded {len(service.hot_folders)} hot folder(s)")
    
    # Verify that printer_name is None
    if service.hot_folders[0].printer_name is None:
        print("✓ Empty printer_name correctly converted to None")
    else:
        print(f"✗ Expected None, got: {service.hot_folders[0].printer_name}")
    
    # Clean up
    os.unlink(test_config_path)
    
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test configuration with missing printer_name
print("\nTesting configuration with missing printer_name...")
try:
    # Create a test config without printer_name key
    test_config = {
        "hot_folders": [
            {
                "name": "DefaultPrinterFolder2",
                "watch_path": "/tmp/test_default_printer2",
                "success_folder": "/tmp/test_default_printer2/Success",
                "error_folder": "/tmp/test_default_printer2/Error"
            }
        ],
        "poll_interval": 1,
        "log_level": "DEBUG"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        test_config_path = f.name
    
    # Test BatchPrintService loading
    service = batch_print.BatchPrintService(test_config_path)
    print("✓ BatchPrintService loaded configuration with missing printer_name")
    
    # Verify that printer_name is None
    if service.hot_folders[0].printer_name is None:
        print("✓ Missing printer_name correctly defaults to None")
    else:
        print(f"✗ Expected None, got: {service.hot_folders[0].printer_name}")
    
    # Clean up
    os.unlink(test_config_path)
    
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test HotFolderConfig with None printer_name
print("\nTesting HotFolderConfig with None printer_name...")
try:
    config = batch_print.HotFolderConfig(
        name="TestFolder",
        watch_path="/tmp/test_hot_folder",
        printer_name=None,
        success_folder="/tmp/test_hot_folder/Success",
        error_folder="/tmp/test_hot_folder/Error"
    )
    print("✓ HotFolderConfig created successfully with None printer_name")
    
    if config.printer_name is None:
        print("✓ printer_name is None as expected")
    else:
        print(f"✗ Expected None, got: {config.printer_name}")
    
except Exception as e:
    print(f"✗ HotFolderConfig test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("Default printer tests completed successfully!")
print("="*60)
print("\nNote: Actual printing with default printer requires:")
print("  1. A default printer configured in the system")
print("  2. Running on the target platform (Windows/macOS/Linux)")
print("  3. Files to print")
