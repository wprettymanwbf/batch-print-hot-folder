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
from typing import List, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent


class HotFolderConfig:
    """Configuration for a single hot folder"""
    def __init__(self, name: str, watch_path: str, printer_name: str, 
                 success_folder: str, error_folder: str):
        self.name = name
        self.watch_path = watch_path
        self.printer_name = printer_name
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
            
        self.logger.info(f"New file detected: {file_path}")
        self.pending_files.add(file_path)
        
    def process_pending_files(self):
        """Process all pending files in alphabetical order"""
        if not self.pending_files:
            return
            
        # Get list of files that still exist
        existing_files = [f for f in self.pending_files if os.path.exists(f)]
        
        # Sort alphabetically by filename
        sorted_files = sorted(existing_files, key=lambda x: os.path.basename(x))
        
        for file_path in sorted_files:
            # Wait a bit to ensure file is completely written
            time.sleep(1)
            
            # Check if file still exists and is not being written to
            if not self._is_file_ready(file_path):
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
        printer_info = self.config.printer_name if self.config.printer_name else "default printer"
        self.logger.info(f"Attempting to print: {file_path} to {printer_info}")
        
        try:
            system = platform.system()
            
            if system == "Windows":
                # Windows printing
                import win32print
                import win32api
                
                # Set the printer if a specific one is configured
                if self.config.printer_name:
                    win32print.SetDefaultPrinter(self.config.printer_name)
                    # Print using ShellExecute with 'print' verb and specific printer
                    win32api.ShellExecute(
                        0,
                        "print",
                        file_path,
                        f'/d:"{self.config.printer_name}"',
                        ".",
                        0
                    )
                else:
                    # Use default printer (no printer parameter)
                    win32api.ShellExecute(
                        0,
                        "print",
                        file_path,
                        None,
                        ".",
                        0
                    )
                
            elif system == "Darwin":  # macOS
                # Use lpr command for printing
                cmd = ["lpr"]
                if self.config.printer_name:
                    cmd.extend(["-P", self.config.printer_name])
                cmd.append(file_path)
                
                subprocess.run(cmd, check=True)
                
            elif system == "Linux":
                # Use lp command for printing
                cmd = ["lp"]
                if self.config.printer_name:
                    cmd.extend(["-d", self.config.printer_name])
                cmd.append(file_path)
                
                subprocess.run(cmd, check=True)
                
            else:
                self.logger.error(f"Unsupported operating system: {system}")
                return False
            
            self.logger.info(f"Successfully sent to printer: {file_path}")
            # Wait a bit for print job to be queued
            time.sleep(2)
            return True
            
        except Exception as e:
            self.logger.error(f"Error printing file {file_path}: {str(e)}")
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
            self.logger.info(f"Moved to Success: {dest_path}")
            
        except Exception as e:
            self.logger.error(f"Error moving file to Success: {str(e)}")
    
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
            self.logger.info(f"Moved to Error: {dest_path}")
            
        except Exception as e:
            self.logger.error(f"Error moving file to Error: {str(e)}")


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
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.poll_interval = config.get('poll_interval', 5)
            
            for folder_config in config.get('hot_folders', []):
                hot_folder = HotFolderConfig(
                    name=folder_config['name'],
                    watch_path=folder_config['watch_path'],
                    printer_name=folder_config['printer_name'],
                    success_folder=folder_config['success_folder'],
                    error_folder=folder_config['error_folder']
                )
                self.hot_folders.append(hot_folder)
                
            self.logger.info(f"Loaded {len(self.hot_folders)} hot folder configurations")
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise
    
    def start(self):
        """Start monitoring all hot folders"""
        self.logger.info("Starting Batch Print Service...")
        
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
            
            self.logger.info(f"Monitoring: {hot_folder.watch_path} -> {hot_folder.printer_name}")
        
        try:
            while True:
                # Process pending files for all handlers
                for handler in self.handlers:
                    handler.process_pending_files()
                
                time.sleep(self.poll_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Stopping Batch Print Service...")
            self.stop()
    
    def stop(self):
        """Stop monitoring all hot folders"""
        for observer in self.observers:
            observer.stop()
            observer.join()
        
        self.logger.info("Batch Print Service stopped")


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('batch_print.log'),
            logging.StreamHandler(sys.stdout)
        ]
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
    logger.info("=" * 60)
    logger.info("Batch Print Hot Folder Service")
    logger.info("=" * 60)
    
    try:
        service = BatchPrintService()
        service.start()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
