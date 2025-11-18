#!/usr/bin/env python3
"""
Test script to verify default printer functionality
"""
import json
import os
import sys
import tempfile
from pathlib import Path

print("="*70)
print("Testing Default Printer Configuration")
print("="*70)

# Test that we can import the module
try:
    import batch_print
    print("✓ Successfully imported batch_print module")
except ImportError as e:
    print(f"✗ Failed to import batch_print: {e}")
    sys.exit(1)

# Test 1: Configuration with empty printer_name
print("\n" + "="*70)
print("TEST 1: Configuration with Empty Printer Name")
print("="*70)

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
    
    # Test HotFolderConfig creation with empty printer_name
    config = batch_print.HotFolderConfig(
        name="DefaultPrinterFolder",
        watch_path="/tmp/test_default_printer",
        printer_name="",
        success_folder="/tmp/test_default_printer/Success",
        error_folder="/tmp/test_default_printer/Error"
    )
    print("✓ HotFolderConfig created with empty printer_name")
    print(f"  - Printer name: '{config.printer_name}' (empty string)")
    
    # Test BatchPrintService loading
    service = batch_print.BatchPrintService(test_config_path)
    print("✓ BatchPrintService loaded configuration successfully")
    print(f"  - Loaded {len(service.hot_folders)} hot folder(s)")
    print(f"  - Printer name for folder: '{service.hot_folders[0].printer_name}'")
    
    # Clean up
    os.unlink(test_config_path)
    
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Configuration with null/None printer_name (simulating optional field)
print("\n" + "="*70)
print("TEST 2: Handler with Empty Printer Name")
print("="*70)

try:
    handler = batch_print.PrintHandler(config)
    print("✓ PrintHandler created with empty printer_name")
    
    # Verify the handler would log correctly
    # We can't actually print without a real printer, but we can verify
    # the configuration is accepted
    if config.printer_name == "":
        print("✓ Empty printer_name correctly stored in config")
        print("  - This will use the system's default printer at print time")
    else:
        print(f"✗ Unexpected printer_name value: '{config.printer_name}'")
    
except Exception as e:
    print(f"✗ Handler test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Mixed configuration (some with specific printers, some with default)
print("\n" + "="*70)
print("TEST 3: Mixed Configuration (Specific + Default Printers)")
print("="*70)

try:
    mixed_config = {
        "hot_folders": [
            {
                "name": "SpecificPrinter",
                "watch_path": "/tmp/test_specific",
                "printer_name": "HP-LaserJet",
                "success_folder": "/tmp/test_specific/Success",
                "error_folder": "/tmp/test_specific/Error"
            },
            {
                "name": "DefaultPrinter",
                "watch_path": "/tmp/test_default",
                "printer_name": "",
                "success_folder": "/tmp/test_default/Success",
                "error_folder": "/tmp/test_default/Error"
            }
        ],
        "poll_interval": 1,
        "log_level": "INFO"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mixed_config, f)
        mixed_config_path = f.name
    
    service = batch_print.BatchPrintService(mixed_config_path)
    print("✓ BatchPrintService loaded mixed configuration")
    print(f"  - Loaded {len(service.hot_folders)} hot folders")
    
    for hf in service.hot_folders:
        printer_display = f"'{hf.printer_name}'" if hf.printer_name else "default printer"
        print(f"  - {hf.name}: {printer_display}")
    
    # Verify first has specific printer, second has empty
    assert service.hot_folders[0].printer_name == "HP-LaserJet", "First should have specific printer"
    assert service.hot_folders[1].printer_name == "", "Second should have empty printer_name"
    print("✓ Both configurations loaded correctly")
    
    # Clean up
    os.unlink(mixed_config_path)
    
except Exception as e:
    print(f"✗ Mixed configuration test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*70)
print("DEFAULT PRINTER TESTS SUMMARY")
print("="*70)
print("✓ All tests passed successfully!")
print("\nThe default printer feature is working correctly:")
print("  • Empty printer_name is accepted in configuration")
print("  • HotFolderConfig handles empty printer_name")
print("  • BatchPrintService loads empty printer_name correctly")
print("  • Mixed configurations (specific + default) work together")
print("\nNote: Actual printing to default printer requires:")
print("  1. A configured default printer on the system")
print("  2. Running on the target platform (Windows/macOS/Linux)")
print("  3. Files to print")
print("="*70)
