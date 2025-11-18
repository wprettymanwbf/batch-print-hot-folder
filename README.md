# Batch Print Hot Folder

A Python-based solution for automatically printing files from hot folders. This application monitors designated folders and automatically prints any files copied into them using the OS default application for each file type.

## Quick Start

1. **Install**: Clone the repository and install dependencies
   ```bash
   git clone https://github.com/wprettymanwbf/batch-print-hot-folder.git
   cd batch-print-hot-folder
   pip install -r requirements.txt
   ```

2. **Configure**: Copy and edit the configuration file
   ```bash
   cp config.example.json config.json
   # Edit config.json with your folder paths and printer names
   ```

3. **Run**: Start the service
   ```bash
   python batch_print.py
   ```

4. **Use**: Copy files to your configured hot folder(s) and they will be automatically printed

5. **Monitor**: Check `batch_print.log` for detailed activity logs

## Features

- **Multiple Hot Folders**: Configure as many hot folders as needed, each with its own printer
- **Alphabetical Processing**: Files are printed in alphabetical order by filename
- **Success/Error Handling**: Successfully printed files are moved to a Success folder, failed files to an Error folder
- **Multi-platform Support**: Works on Windows, macOS, and Linux
- **Configurable**: Simple JSON configuration file
- **Automatic Folder Creation**: Success and Error folders are created automatically
- **File Type Agnostic**: Prints any file type using the OS default application
- **Human-Readable Logs**: Detailed logging with timestamps and visual indicators for easy monitoring

## Requirements

- Python 3.7 or higher
- Operating System: Windows, macOS, or Linux

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/wprettymanwbf/batch-print-hot-folder.git
   cd batch-print-hot-folder
   ```

2. Run the setup script:
   
   **Linux/macOS:**
   ```bash
   ./setup.sh
   ```
   
   **Windows:**
   ```cmd
   setup.bat
   ```
   
   Or install manually:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy the example configuration file:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` to configure your hot folders:

```json
{
  "hot_folders": [
    {
      "name": "MainPrinter",
      "watch_path": "/path/to/hot/folder1",
      "printer_name": "Your Printer Name",
      "success_folder": "/path/to/hot/folder1/Success",
      "error_folder": "/path/to/hot/folder1/Error"
    }
  ],
  "poll_interval": 5,
  "log_level": "INFO"
}
```

### Configuration Parameters

- **name**: A descriptive name for the hot folder (for logging purposes)
- **watch_path**: The folder to monitor for new files
- **printer_name**: The name of the printer to use (must match the printer name in your OS)
- **success_folder**: Where successfully printed files will be moved
- **error_folder**: Where failed files will be moved
- **poll_interval**: How often (in seconds) to check for pending files
- **log_level**: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Finding Printer Names

**Windows:**
```cmd
wmic printer get name
```
or open Control Panel > Devices and Printers

**macOS:**
```bash
lpstat -p | awk '{print $2}'
```

**Linux:**
```bash
lpstat -p | awk '{print $2}'
```

## Usage

Run the batch print service:

```bash
python batch_print.py
```

The service will:
1. Monitor all configured hot folders
2. Detect new files as they are copied in
3. Sort files alphabetically by filename
4. Print each file using the configured printer
5. Move successfully printed files to the Success folder
6. Move failed files to the Error folder

To stop the service, press `Ctrl+C`.

## How It Works

```
┌─────────────────┐
│   Hot Folder    │  ← User copies files here
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  File Detection & Monitoring    │  (watchdog library)
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  File Readiness Check           │  (ensures complete copy)
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Alphabetical Sorting           │  (sort by filename)
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Print to Configured Printer    │  (OS default app)
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌───────┐
│Success │ │ Error │  ← Files moved here based on print result
└────────┘ └───────┘
```

### Process Details

1. **File Detection**: The application uses the `watchdog` library to monitor hot folders for new files
2. **File Readiness**: Before processing, the app ensures files are completely written (not still being copied)
3. **Alphabetical Sorting**: Pending files are sorted alphabetically by filename
4. **Printing**: Files are printed using OS-specific methods:
   - **Windows**: Uses `win32api.ShellExecute` with the "print" verb
   - **macOS**: Uses the `lpr` command
   - **Linux**: Uses the `lp` command
5. **File Movement**: After printing (success or failure), files are moved to the appropriate folder

## Logging

The application provides comprehensive, human-readable logging to help you monitor the service:

### Log Output Locations
- **Console**: Real-time status updates displayed in your terminal
- **Log File**: `batch_print.log` in the application directory with full timestamps

### Log Format
Logs use a clean, easy-to-read format with visual indicators:
```
2025-11-18 14:30:15 | INFO     | ======================================================================
2025-11-18 14:30:15 | INFO     |   BATCH PRINT HOT FOLDER SERVICE
2025-11-18 14:30:15 | INFO     | ======================================================================
2025-11-18 14:30:15 | INFO     | Watching Folder: /path/to/hot/folder
2025-11-18 14:30:15 | INFO     |   → Printer: My Printer
2025-11-18 14:30:20 | INFO     | 📄 NEW FILE DETECTED: document.pdf
2025-11-18 14:30:22 | INFO     | 🖨️  PRINTING: document.pdf (125.3 KB)
2025-11-18 14:30:24 | INFO     | ✅ Print job sent successfully: document.pdf
2025-11-18 14:30:24 | INFO     |    ➜ Moved to Success folder: document.pdf
```

### Log Levels
Configure the detail level in `config.json` using the `log_level` parameter:
- **DEBUG**: Detailed diagnostic information for troubleshooting
- **INFO**: General information about service operation (default)
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may stop the service

### Viewing Logs
- **Real-time**: Watch the console while the service runs
- **Historical**: Open `batch_print.log` in any text editor
- **Tail logs**: Use `tail -f batch_print.log` (Linux/macOS) to follow in real-time

## Example Workflow

1. User copies `document.pdf` to the hot folder
2. Application detects the new file
3. Application waits to ensure the file is fully copied
4. Application prints `document.pdf` to the configured printer
5. Application moves `document.pdf` to the Success folder
6. Log entry confirms the action

## Troubleshooting

### Files not printing
- Verify the printer name matches exactly (case-sensitive)
- Check that the printer is online and accessible
- Review the `batch_print.log` file for error messages
- Ensure the file type has a default application configured

### Files stuck in hot folder
- Check file permissions
- Ensure files are not locked by another process
- Check the Error folder - files may have moved there

### Service crashes
- Review `batch_print.log` for error details
- Verify all paths in `config.json` are valid
- Ensure required dependencies are installed

## Platform-Specific Notes

### Windows
- Requires `pywin32` package (installed automatically via requirements.txt)
- Uses Windows printing API
- Supports all file types registered with default applications

### macOS
- Uses CUPS printing system (`lpr` command)
- May require printer setup via System Preferences first

### Linux
- Uses CUPS printing system (`lp` command)
- Ensure CUPS is installed and configured

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
