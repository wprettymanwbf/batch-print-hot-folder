"""
Batch Print Hot Folder - A solution for automatically printing files from hot folders
"""
import os
import sys
import time
import json
import logging
import shutil
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


def get_default_printer() -> Optional[str]:
    """Get the system's default printer name"""
    try:
        system = platform.system()
        
        if system == "Windows":
            # Windows: Get default printer using win32print
            import win32print
            return win32print.GetDefaultPrinter()
            
        elif system == "Darwin":  # macOS
            # Use lpstat -d to get default printer
            result = subprocess.run(
                ["lpstat", "-d"],
                capture_output=True,
                text=True,
                check=True
            )
            # Output format: "system default destination: PrinterName"
            output = result.stdout.strip()
            if ":" in output:
                return output.split(":")[-1].strip()
            return None
            
        elif system == "Linux":
            # Use lpstat -d to get default printer
            result = subprocess.run(
                ["lpstat", "-d"],
                capture_output=True,
                text=True,
                check=True
            )
            # Output format: "system default destination: PrinterName"
            output = result.stdout.strip()
            if ":" in output:
                return output.split(":")[-1].strip()
            return None
            
        else:
            return None
            
    except Exception:
        # If we can't get the default printer, return None
        return None


class HotFolderConfig:
    """Configuration for a single hot folder"""
    def __init__(self, name: str, watch_path: str, printer_name: Optional[str], 
                 success_folder: str, error_folder: str):
        self.name = name
        self.watch_path = watch_path
        self.printer_name = printer_name if printer_name else None
        self.success_folder = success_folder
        self.error_folder = error_folder
        
        # Create success and error folders if they don't exist
        os.makedirs(self.success_folder, exist_ok=True)
        os.makedirs(self.error_folder, exist_ok=True)


class PrintHandler(FileSystemEventHandler):
    """Handler for file system events in hot folders"""
    
    def __init__(self, config: HotFolderConfig):
        self.config = config
        self.logger = logging.getLogger(f"PrintHandler-{config.name}")
        self.pending_files = set()
        
    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # Ignore files in Success or Error folders
        if (self.config.success_folder in file_path or 
            self.config.error_folder in file_path):
            return
            
        filename = os.path.basename(file_path)
        self.logger.info(f"📄 NEW FILE DETECTED: {filename}")
        self.pending_files.add(file_path)
        
    def process_pending_files(self):
        """Process all pending files in alphabetical order"""
        if not self.pending_files:
            return
            
        # Get list of files that still exist
        existing_files = [f for f in self.pending_files if os.path.exists(f)]
        
        # Sort alphabetically by filename
        sorted_files = sorted(existing_files, key=lambda x: os.path.basename(x))
        
        if sorted_files:
            self.logger.info(f"Processing {len(sorted_files)} file(s) in alphabetical order...")
        
        for file_path in sorted_files:
            filename = os.path.basename(file_path)
            
            # Wait a bit to ensure file is completely written
            time.sleep(1)
            
            # Check if file still exists and is not being written to
            if not self._is_file_ready(file_path):
                self.logger.warning(f"⏳ File not ready yet, will retry: {filename}")
                continue
                
            success = self.print_file(file_path)
            
            if success:
                self.move_to_success(file_path)
            else:
                self.move_to_error(file_path)
                
            self.pending_files.discard(file_path)
    
    def _is_file_ready(self, file_path: str, max_attempts: int = 3) -> bool:
        """Check if file is ready to be processed (not being written)"""
        for attempt in range(max_attempts):
            try:
                # Try to get file size
                size1 = os.path.getsize(file_path)
                time.sleep(0.5)
                size2 = os.path.getsize(file_path)
                
                # If size hasn't changed, file is likely ready
                if size1 == size2 and size1 > 0:
                    return True
            except (OSError, FileNotFoundError):
                return False
        
        return False
    
    def print_file(self, file_path: str) -> bool:
        """Print a file using the OS default application"""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_kb = file_size / 1024
        
        # Determine which printer to use
        printer_to_use = self.config.printer_name
        if not printer_to_use:
            # Get default printer if none specified
            printer_to_use = get_default_printer()
            if not printer_to_use:
                self.logger.error(f"❌ No printer specified and no default printer available")
                return False
            self.logger.info(f"Using default printer: {printer_to_use}")
        
        self.logger.info(f"🖨️  PRINTING: {filename} ({size_kb:.1f} KB)")
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows printing
                import win32print
                import win32api
                
                # Set the printer
                win32print.SetDefaultPrinter(printer_to_use)
                
                # Print using ShellExecute with 'print' verb
                win32api.ShellExecute(
                    0,
                    "print",
                    file_path,
                    f'/d:"{printer_to_use}"',
                    ".",
                    0
                )
                
            elif system == "Darwin":  # macOS
                # Use lpr command for printing
                cmd = ["lpr", "-P", printer_to_use, file_path]
                subprocess.run(cmd, check=True)
                
            elif system == "Linux":
                # Use lp command for printing
                cmd = ["lp", "-d", printer_to_use, file_path]
                subprocess.run(cmd, check=True)
                
            else:
                self.logger.error(f"❌ Unsupported operating system: {system}")
                return False
            
            self.logger.info(f"✅ Print job sent successfully: {filename}")
            # Wait a bit for print job to be queued
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ PRINT FAILED: {filename} - {str(e)}")
            return False
    
    def move_to_success(self, file_path: str):
        """Move file to success folder"""
        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.config.success_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(
                    self.config.success_folder, 
                    f"{name}_{counter}{ext}"
                )
                counter += 1
            
            shutil.move(file_path, dest_path)
            dest_filename = os.path.basename(dest_path)
            self.logger.info(f"   ➜ Moved to Success folder: {dest_filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Error moving file to Success: {str(e)}")
    
    def move_to_error(self, file_path: str):
        """Move file to error folder"""
        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.config.error_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(
                    self.config.error_folder, 
                    f"{name}_{counter}{ext}"
                )
                counter += 1
            
            shutil.move(file_path, dest_path)
            dest_filename = os.path.basename(dest_path)
            self.logger.info(f"   ➜ Moved to Error folder: {dest_filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Error moving file to Error folder: {str(e)}")


class BatchPrintService:
    """Main service for managing hot folder printing"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.hot_folders: List[HotFolderConfig] = []
        self.observers: List[Observer] = []
        self.handlers: List[PrintHandler] = []
        self.poll_interval = 5
        self.logger = logging.getLogger("BatchPrintService")
        
        self.load_config()
        
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            self.logger.info(f"Loading configuration from: {self.config_file}")
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.poll_interval = config.get('poll_interval', 5)
            
            for folder_config in config.get('hot_folders', []):
                # Get printer name, allowing it to be None/empty for default printer
                printer_name = folder_config.get('printer_name')
                if printer_name == "":
                    printer_name = None
                    
                hot_folder = HotFolderConfig(
                    name=folder_config['name'],
                    watch_path=folder_config['watch_path'],
                    printer_name=printer_name,
                    success_folder=folder_config['success_folder'],
                    error_folder=folder_config['error_folder']
                )
                self.hot_folders.append(hot_folder)
                
            self.logger.info(f"✅ Configuration loaded: {len(self.hot_folders)} hot folder(s) configured")
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise
    
    def start(self):
        """Start monitoring all hot folders"""
        self.logger.info("SERVICE STARTING...")
        self.logger.info("")
        
        for hot_folder in self.hot_folders:
            # Create watch folder if it doesn't exist
            os.makedirs(hot_folder.watch_path, exist_ok=True)
            
            # Create handler and observer
            handler = PrintHandler(hot_folder)
            observer = Observer()
            observer.schedule(handler, hot_folder.watch_path, recursive=False)
            observer.start()
            
            self.handlers.append(handler)
            self.observers.append(observer)
            
            self.logger.info(f"Watching Folder: {hot_folder.watch_path}")
            if hot_folder.printer_name:
                self.logger.info(f"  → Printer: {hot_folder.printer_name}")
            else:
                default_printer = get_default_printer()
                if default_printer:
                    self.logger.info(f"  → Printer: {default_printer} (system default)")
                else:
                    self.logger.info(f"  → Printer: System default (none currently set)")
            self.logger.info(f"  → Success: {hot_folder.success_folder}")
            self.logger.info(f"  → Error: {hot_folder.error_folder}")
            self.logger.info("")
        
        self.logger.info(f"Checking for files every {self.poll_interval} seconds...")
        self.logger.info("Press Ctrl+C to stop the service")
        self.logger.info("-" * 70)
        
        try:
            while True:
                # Process pending files for all handlers
                for handler in self.handlers:
                    handler.process_pending_files()
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("")
            self.logger.info("-" * 70)
            self.logger.info("Shutdown requested by user (Ctrl+C)")
            self.stop()
    
    def stop(self):
        """Stop monitoring all hot folders"""
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.logger.info("All monitors stopped successfully")
        self.logger.info("=" * 70)
        self.logger.info("  SERVICE STOPPED")
        self.logger.info("=" * 70)


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application with human-readable format"""
    # Create a custom formatter for more readable logs
    file_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler('batch_print.log')
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        handlers=[file_handler, console_handler]
    )


def main():
    """Main entry point"""
    # Load log level from config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            log_level = config.get('log_level', 'INFO')
    except:
        log_level = 'INFO'
    
    setup_logging(log_level)
    
    logger = logging.getLogger("Main")
    logger.info("=" * 70)
    logger.info("  BATCH PRINT HOT FOLDER SERVICE")
    logger.info("=" * 70)
    logger.info(f"Platform: {platform.system()}")
    logger.info(f"Python Version: {sys.version.split()[0]}")
    logger.info(f"Log Level: {log_level}")
    logger.info("=" * 70)
    
    try:
        service = BatchPrintService()
        service.start()
    except Exception as e:
        logger.error(f"FATAL ERROR: {str(e)}", exc_info=True)
        logger.info("=" * 70)
        logger.info("  SERVICE STOPPED DUE TO ERROR")
        logger.info("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
