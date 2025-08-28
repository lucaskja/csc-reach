# Frontend Architecture

## Overview

CSC-Reach's frontend is built with PySide6 (Qt for Python), providing a professional, cross-platform desktop application with modern UI/UX principles. The frontend follows a component-based architecture with clear separation between presentation logic and business logic.

## Key Features

- **Cross-Platform Native UI**: Consistent experience across Windows and macOS
- **Professional Design**: Modern, clean interface with professional branding
- **Multi-Language Support**: Complete internationalization (English, Portuguese, Spanish)
- **Theme Management**: Dark/light themes with user customization
- **Accessibility**: Full accessibility support with keyboard navigation
- **Real-Time Updates**: Live progress tracking and status updates
- **Responsive Layout**: Adaptive interface for different screen sizes
- **Professional Dialogs**: Modal dialogs for complex operations

## Project Structure

```
src/multichannel_messaging/gui/
├── main_window.py                  # Primary application window
├── template_library_dialog.py     # Template management interface
├── progress_dialog.py             # Real-time progress tracking
├── preferences_dialog.py          # User settings and configuration
├── email_preview_dialog.py        # Email preview functionality
├── whatsapp_multi_message_dialog.py # WhatsApp message composition
├── csv_import_config_dialog.py    # Data import configuration
├── message_analytics_dialog.py    # Analytics and reporting
├── language_settings_dialog.py    # Language selection
└── variables_panel.py             # Dynamic variable management
```

## Component Architecture

### Main Window (`main_window.py`)

The central hub of the application, orchestrating all user interactions:

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_connections()
        self.setup_managers()
        
    def setup_ui(self):
        """Initialize the main user interface"""
        
    def setup_connections(self):
        """Connect signals and slots"""
        
    def setup_managers(self):
        """Initialize core managers"""
```

**Key Components**:
- **Menu Bar**: File, Edit, View, Tools, Help menus
- **Toolbar**: Quick access to common operations
- **Central Widget**: Main content area with tabs/panels
- **Status Bar**: Real-time status updates and progress indicators
- **Dock Widgets**: Collapsible panels for secondary functions

### Template Library Dialog (`template_library_dialog.py`)

Professional template management interface:

```python
class TemplateLibraryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.template_manager = TemplateManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Create template management interface"""
        # Category tree view
        # Template list with search/filter
        # Preview panel
        # Edit/Create/Delete controls
```

**Features**:
- **Category Tree**: Hierarchical organization of templates
- **Search & Filter**: Quick template discovery
- **Live Preview**: Real-time template preview with sample data
- **CRUD Operations**: Create, read, update, delete templates
- **Import/Export**: Template sharing and backup functionality
- **Usage Analytics**: Template popularity and usage statistics

### Progress Dialog (`progress_dialog.py`)

Real-time progress tracking with detailed analytics:

```python
class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.progress_manager = ProgressManager()
        self.setup_ui()
        
    def update_progress(self, current: int, total: int, status: str):
        """Update progress indicators"""
        
    def show_analytics(self, analytics_data: Dict):
        """Display real-time analytics"""
```

**Components**:
- **Progress Bars**: Overall and current operation progress
- **Status Display**: Current operation status and details
- **Analytics Panel**: Success/failure rates, timing information
- **Log Viewer**: Real-time log display with filtering
- **Control Buttons**: Pause, resume, cancel operations

### Preferences Dialog (`preferences_dialog.py`)

Comprehensive user settings management:

```python
class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.setup_ui()
        
    def setup_ui(self):
        """Create preferences interface"""
        # General settings tab
        # Appearance settings tab
        # Integration settings tab
        # Advanced settings tab
```

**Settings Categories**:
- **General**: Language, startup behavior, default paths
- **Appearance**: Theme selection, font settings, UI customization
- **Integration**: Outlook settings, WhatsApp configuration
- **Advanced**: Logging levels, performance tuning, debug options

## UI/UX Design Principles

### Visual Design
- **Professional Branding**: Consistent color scheme and typography
- **Clean Layout**: Minimal clutter with focus on essential functions
- **Visual Hierarchy**: Clear information hierarchy with proper spacing
- **Icon System**: Consistent iconography throughout the application
- **Status Indicators**: Clear visual feedback for all operations

### Interaction Design
- **Intuitive Navigation**: Logical flow between different functions
- **Keyboard Shortcuts**: Comprehensive keyboard navigation support
- **Context Menus**: Right-click menus for quick access to functions
- **Drag & Drop**: File import via drag and drop functionality
- **Tooltips**: Helpful tooltips for all interactive elements

### Responsive Design
- **Adaptive Layout**: Interface adapts to different window sizes
- **Collapsible Panels**: Panels can be collapsed to save space
- **Resizable Components**: Splitters allow user customization
- **Minimum Size Constraints**: Prevents interface from becoming unusable

## Theme Management

### Theme System Architecture
```python
class ThemeManager:
    def __init__(self):
        self.current_theme = "light"
        self.themes = {
            "light": LightTheme(),
            "dark": DarkTheme(),
            "custom": CustomTheme()
        }
        
    def apply_theme(self, theme_name: str):
        """Apply selected theme to all components"""
        
    def create_custom_theme(self, base_theme: str, customizations: Dict):
        """Create custom theme based on existing theme"""
```

### Theme Components
- **Color Palette**: Primary, secondary, accent colors
- **Typography**: Font families, sizes, weights
- **Spacing**: Margins, padding, component spacing
- **Borders**: Border styles, radius, shadows
- **Icons**: Theme-appropriate icon sets

## Internationalization (i18n)

### Language Support Architecture
```python
class I18nManager:
    def __init__(self):
        self.current_language = "en"
        self.supported_languages = ["en", "pt", "es"]
        self.translations = {}
        
    def load_translations(self, language: str):
        """Load translation files for specified language"""
        
    def translate(self, key: str, **kwargs) -> str:
        """Translate text with optional formatting"""
```

### Translation Features
- **Dynamic Language Switching**: Change language without restart
- **Pluralization Support**: Proper plural forms for different languages
- **Date/Time Formatting**: Locale-appropriate formatting
- **Number Formatting**: Currency and number formatting per locale
- **RTL Support**: Right-to-left language support framework

## Accessibility Features

### Keyboard Navigation
- **Tab Order**: Logical tab order through all interactive elements
- **Keyboard Shortcuts**: Comprehensive shortcut system
- **Focus Indicators**: Clear visual focus indicators
- **Skip Links**: Quick navigation to main content areas

### Screen Reader Support
- **ARIA Labels**: Proper labeling for screen readers
- **Role Definitions**: Semantic roles for UI components
- **State Announcements**: Dynamic state changes announced
- **Alternative Text**: Alt text for all images and icons

### Visual Accessibility
- **High Contrast**: High contrast theme option
- **Font Scaling**: Adjustable font sizes
- **Color Blind Support**: Color schemes that work for color blind users
- **Focus Management**: Proper focus management for modal dialogs

## State Management

### Application State
```python
class ApplicationState:
    def __init__(self):
        self.current_customers = []
        self.active_template = None
        self.selected_recipients = []
        self.operation_status = "idle"
        
    def update_state(self, key: str, value: Any):
        """Update application state with validation"""
        
    def get_state(self, key: str, default=None):
        """Get current state value"""
```

### State Synchronization
- **Observer Pattern**: Components observe state changes
- **Event System**: Custom event system for state updates
- **Validation**: State changes validated before application
- **Persistence**: Critical state persisted across sessions

## Build & Deploy

### Development Build
```bash
# Install dependencies
pip install -e ".[dev]"

# Run in development mode
python src/multichannel_messaging/main.py

# Run with hot reload (development)
python scripts/dev/run_with_reload.py
```

### Production Build
```bash
# Build for macOS
python scripts/build_macos.py

# Build for Windows
python scripts/build_windows.py

# Create installers
python scripts/create_installers.py
```

### Build Optimization
- **Resource Bundling**: All assets bundled into executable
- **Code Minification**: Python bytecode optimization
- **Dependency Analysis**: Only required dependencies included
- **Size Optimization**: Unused modules excluded from build

## Performance Considerations

### UI Performance
- **Lazy Loading**: Heavy components loaded on demand
- **Virtual Lists**: Large lists virtualized for performance
- **Debounced Updates**: Rapid updates debounced to prevent flicker
- **Background Processing**: Long operations moved to background threads

### Memory Management
- **Widget Cleanup**: Proper cleanup of Qt widgets
- **Event Handler Cleanup**: Disconnect event handlers when not needed
- **Image Caching**: Efficient caching of images and icons
- **Memory Monitoring**: Built-in memory usage monitoring

### Responsiveness
- **Non-Blocking Operations**: UI remains responsive during operations
- **Progress Feedback**: Immediate feedback for all user actions
- **Async Operations**: Heavy operations run asynchronously
- **Thread Safety**: Proper thread safety for UI updates

## Testing Strategy

### Unit Testing
```python
class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.app = QApplication([])
        self.window = MainWindow()
        
    def test_window_initialization(self):
        """Test main window initializes correctly"""
        
    def test_menu_actions(self):
        """Test all menu actions work correctly"""
```

### Integration Testing
- **Dialog Testing**: Test dialog interactions and data flow
- **Workflow Testing**: Test complete user workflows
- **Cross-Platform Testing**: Test on both Windows and macOS
- **Accessibility Testing**: Test keyboard navigation and screen readers

### UI Testing Tools
- **pytest-qt**: Qt-specific testing framework
- **QTest**: Qt's built-in testing utilities
- **Screenshot Testing**: Visual regression testing
- **Performance Testing**: UI performance benchmarking
