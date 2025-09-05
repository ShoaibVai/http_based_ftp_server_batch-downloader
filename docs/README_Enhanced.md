# FTP Batch Downloader - Enhanced Edition

A powerful, modern PyQt5-based application for efficiently downloading files from FTP and HTTP servers with advanced optimization features, intelligent caching, and memory management.

---

## 🚀 What's New in Enhanced Edition

### ⚡ Performance Optimizations
- **Directory Caching System**: Intelligent disk and memory caching with 24-hour expiration
- **Memory Monitoring**: Real-time memory usage display with automatic cleanup
- **Adaptive Chunking**: Dynamic chunk sizing based on file size for optimal performance
- **Speed Throttling**: Configurable bandwidth limiting
- **Lazy Loading**: Paginated directory listings for large directories

### 🔧 Advanced Features  
- **Favicon Integration**: Consistent branding across all windows
- **Memory Optimization**: Automatic garbage collection and threshold warnings
- **Enhanced Error Handling**: Improved retry mechanisms with exponential backoff
- **Project Reorganization**: Clean, modular codebase structure

---

## ✨ Features

### Core Functionality
- **Multi-Protocol Support**: Download from both FTP and HTTP/HTTPS servers
- **Batch Processing**: Download multiple files and directories simultaneously  
- **Resume Support**: Automatically resume interrupted downloads
- **Tree View**: Browse server directories in an intuitive hierarchical tree
- **Smart Selection**: Select individual files or entire directory structures

### 🎨 Modern User Interface
- **Multiple Themes**: Colorful, Dark, Light, Solarized, and Classic themes with real-time switching
- **Tabbed Interface**: Clean separation between Downloader, Downloads, and Settings
- **Real-time Progress**: Live download progress with speed indicators and ETA calculations
- **Memory Display**: Current memory usage monitoring in status bar
- **Integrated Logging**: Comprehensive logging system with themed log viewer
- **Favicon Support**: Consistent branding across all application windows

### ⚡ Performance Features
- **Directory Caching**: Two-tier caching system (memory + disk) for faster directory access
- **Memory Management**: Intelligent monitoring with automatic cleanup when thresholds are exceeded
- **Chunked Downloads**: Adaptive chunk sizing - larger chunks for bigger files
- **Speed Control**: Optional download speed limiting to manage bandwidth usage
- **Concurrent Downloads**: Configurable simultaneous downloads (1-10)
- **Lazy Loading**: Handle large directories with pagination (configurable page size)

### 🔧 Advanced Capabilities
- **Memory Optimization**: Automatic garbage collection and critical memory alerts
- **Error Handling**: Robust retry mechanisms with configurable attempts and delays
- **Settings Management**: Persistent JSON-based configuration with hot-reload
- **Disk Space Check**: Pre-download validation to ensure sufficient storage
- **Percent-Decoding**: Proper handling of URL-encoded filenames

---

## 📁 Project Structure

```
server_batch_downloader/
├── main.py                    # Application entry point
├── config.json               # Configuration settings
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── LICENSE                   # License information
├── src/                      # Source code (NEW STRUCTURE)
│   ├── ui/                   # User interface modules
│   │   ├── main_window.py    # Main application window
│   │   ├── downloads_tab.py  # Downloads management tab
│   │   └── settings_tab.py   # Settings configuration tab
│   ├── core/                 # Core functionality
│   │   ├── lister.py         # Directory listing with caching
│   │   ├── downloader.py     # Download management with optimization
│   │   ├── utils.py          # Utility functions
│   │   └── cache_manager.py  # NEW: Caching system
│   ├── config/               # Configuration management
│   │   └── manager.py        # Configuration file handling
│   └── utils/                # Utility modules
│       ├── logger.py         # Logging configuration
│       └── memory_monitor.py # NEW: Memory monitoring system
├── resources/                # Application resources
│   └── icons/
│       └── favicon.ico       # Application icon
├── data/                     # Data files (moved from root)
│   └── servers.json          # Server configurations
├── cache/                    # NEW: Directory listing cache
├── logs/                     # Application logs
├── tests/                    # Test files (cleaned up)
└── docs/                     # Documentation
```

---

## 🚀 Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Quick Start
1. **Clone or download this repository**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python main.py
   ```

### Dependencies
```
PyQt5==5.15.10
requests==2.31.0
beautifulsoup4==4.12.3
psutil==5.9.5          # NEW: For memory monitoring
```

---

## 🎯 Usage Guide

### Basic Operations
1. **Start Application**: Run `python main.py`
2. **Add Server URL**: Enter FTP or HTTP URL and click "Fetch Files"
3. **Browse Files**: Navigate the tree structure and select desired items
4. **Choose Destination**: Select download folder
5. **Start Download**: Click "Download Selected" and monitor progress

### Interface Overview
- **Downloader Tab**: URL input, file tree, download controls
- **Downloads Tab**: Progress monitoring, download management, file operations
- **Settings Tab**: Configuration options, theme selection, log viewer

### Advanced Features
- **Caching**: Directory listings are automatically cached for 24 hours
- **Memory Monitoring**: Real-time memory usage display in status bar
- **Speed Control**: Set download speed limits in configuration
- **Batch Operations**: Pause/resume/cancel all downloads simultaneously

---

## ⚙️ Configuration

The application uses `config.json` for persistent settings:

### Basic Settings
```json
{
    "default_download_path": "C:/Downloads",
    "max_concurrent_downloads": 2,
    "listing_depth": 10,
    "theme_name": "Classic"
}
```

### Performance Settings (NEW)
```json
{
    "chunk_size": 8192,
    "page_size": 1000,
    "cache_dir": "cache",
    "cache_expiry_hours": 24,
    "memory_cache_size": 50,
    "max_download_speed_kb": 0
}
```

### Memory Management (NEW)
```json
{
    "memory_warning_threshold": 80.0,
    "memory_critical_threshold": 90.0
}
```

### Configuration Options

| Setting | Description | Range | Default |
|---------|-------------|--------|---------|
| `max_concurrent_downloads` | Simultaneous downloads | 1-10 | 2 |
| `chunk_size` | Download chunk size (bytes) | 1024-65536 | 8192 |
| `page_size` | Directory listing pagination | 100-10000 | 1000 |
| `cache_expiry_hours` | Cache retention time | 1-168 | 24 |
| `memory_warning_threshold` | Memory warning level (%) | 50-95 | 80 |
| `max_download_speed_kb` | Speed limit (KB/s, 0=unlimited) | 0-∞ | 0 |

---

## 🔧 Advanced Features

### Caching System
- **Two-Tier Design**: Memory cache (fast) + Disk cache (persistent)
- **Smart Expiration**: 24-hour automatic invalidation
- **Cache Statistics**: Monitor performance and usage
- **Manual Control**: Clear cache through settings

### Memory Management
- **Real-Time Monitoring**: Live memory usage display
- **Threshold Alerts**: Warnings at 80%, critical at 90%
- **Automatic Cleanup**: Garbage collection when memory is low
- **Process Tracking**: Monitor application memory footprint

### Download Optimization
- **Adaptive Chunking**: Larger chunks for bigger files
- **Speed Monitoring**: Real-time speed calculation and display
- **Resume Support**: Automatic resumption of interrupted downloads
- **Retry Logic**: Configurable retry attempts with exponential backoff

### User Experience
- **Theme System**: 5 beautiful themes with instant switching
- **Progress Tracking**: Real-time progress with ETA calculations
- **Error Reporting**: Comprehensive error messages and logging
- **Keyboard Shortcuts**: Efficient navigation and control

---

## 🐛 Troubleshooting

### Common Issues

**High Memory Usage**
- Reduce concurrent downloads
- Clear cache in settings
- Lower memory cache size
- Close unused tabs

**Slow Directory Listings**
- Enable caching (enabled by default)
- Reduce listing depth
- Use pagination for large directories
- Check network connectivity

**Download Failures**
- Verify server URLs
- Check network connectivity
- Increase retry attempts
- Review logs for detailed errors

### Performance Optimization
- **For Large Downloads**: Increase chunk size (16KB-64KB)
- **For Many Small Files**: Reduce chunk size, increase concurrency
- **For Limited Bandwidth**: Set speed limits
- **For Large Directories**: Enable pagination

### Logging
Comprehensive logging available in `logs/app.log`:
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Rotation**: Automatic log file management
- **Viewer**: In-app log viewer with theme support

---

## 📊 Performance Metrics

The application provides real-time monitoring:

- **Memory Usage**: Process and system memory in status bar
- **Download Speed**: Live speed indicators with ETA
- **Cache Statistics**: Hit/miss ratios and cache size
- **Error Tracking**: Comprehensive error reporting and retry statistics

---

## 🎨 Themes

Choose from 5 professionally designed themes:

- **Colorful**: Modern, vibrant interface
- **Dark**: Easy on the eyes for long sessions
- **Light**: Clean, minimalist design
- **Solarized**: Professional, low-contrast scheme
- **Classic**: Traditional Windows-style interface

---

## 📝 Changelog

### Version 2.0.0 - Enhanced Edition (Current)
- ✅ Added comprehensive two-tier caching system
- ✅ Implemented real-time memory monitoring
- ✅ Enhanced download optimization with adaptive chunking
- ✅ Reorganized project structure for better maintainability
- ✅ Added favicon support across all windows
- ✅ Improved error handling with better retry mechanisms
- ✅ Added speed throttling and advanced configuration options
- ✅ Implemented lazy loading for large directories
- ✅ Enhanced memory management with automatic cleanup

### Version 1.0.0 - Original
- Basic FTP/HTTP download functionality
- Simple GUI interface with multiple themes
- Concurrent download support

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

For support, bug reports, or feature requests:

1. **Check Logs**: Review `logs/app.log` for detailed information
2. **Monitor Memory**: Watch memory usage in status bar
3. **Review Configuration**: Verify settings in `config.json`
4. **Use Debugging**: Enable DEBUG logging level for detailed output

The Enhanced Edition includes comprehensive monitoring and debugging tools to help diagnose and resolve issues quickly.
