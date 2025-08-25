"""
Workspace layout manager for CSC-Reach application.
Provides workspace layout management with save/restore functionality.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from PySide6.QtWidgets import QMainWindow, QSplitter, QWidget
from PySide6.QtCore import QObject, Signal, QByteArray
from PySide6.QtGui import QAction

from ..utils.logger import get_logger
from ..utils.platform_utils import get_config_dir

logger = get_logger(__name__)


@dataclass
class WorkspaceLayout:
    """Represents a workspace layout configuration."""
    id: str
    name: str
    description: str = ""
    created_date: str = ""
    modified_date: str = ""
    window_geometry: Dict[str, int] = field(default_factory=dict)
    window_state: str = ""  # Base64 encoded QByteArray
    splitter_states: Dict[str, str] = field(default_factory=dict)  # splitter_id -> state
    toolbar_configuration: Dict[str, Any] = field(default_factory=dict)
    panel_visibility: Dict[str, bool] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkspaceManager(QObject):
    """Manages workspace layouts and configurations."""
    
    # Signals
    layout_saved = Signal(str)      # layout_id
    layout_loaded = Signal(str)     # layout_id
    layout_deleted = Signal(str)    # layout_id
    layouts_changed = Signal()
    
    def __init__(self, main_window: QMainWindow, preferences_manager=None):
        super().__init__()
        self.main_window = main_window
        self.preferences_manager = preferences_manager
        
        # Workspace layouts
        self.layouts: Dict[str, WorkspaceLayout] = {}
        self.current_layout_id: Optional[str] = None
        
        # Configuration directory
        self.config_dir = get_config_dir()
        self.layouts_file = self.config_dir / "workspace_layouts.json"
        
        # Tracked splitters and panels
        self.tracked_splitters: Dict[str, QSplitter] = {}
        self.tracked_panels: Dict[str, QWidget] = {}
        
        # Load existing layouts
        self.load_layouts()
        
        # Create default layouts if none exist
        if not self.layouts:
            self.create_default_layouts()
    
    def register_splitter(self, splitter_id: str, splitter: QSplitter):
        """Register a splitter for state tracking."""
        self.tracked_splitters[splitter_id] = splitter
        logger.debug(f"Registered splitter: {splitter_id}")
    
    def register_panel(self, panel_id: str, panel: QWidget):
        """Register a panel for visibility tracking."""
        self.tracked_panels[panel_id] = panel
        logger.debug(f"Registered panel: {panel_id}")
    
    def capture_current_layout(self) -> Dict[str, Any]:
        """Capture the current workspace layout."""
        layout_data = {}
        
        # Window geometry
        geometry = self.main_window.geometry()
        layout_data['window_geometry'] = {
            'x': geometry.x(),
            'y': geometry.y(),
            'width': geometry.width(),
            'height': geometry.height(),
            'maximized': self.main_window.isMaximized()
        }
        
        # Window state (toolbars, docks, etc.)
        window_state = self.main_window.saveState()
        layout_data['window_state'] = window_state.toBase64().data().decode('utf-8')
        
        # Splitter states
        splitter_states = {}
        for splitter_id, splitter in self.tracked_splitters.items():
            if splitter:
                state = splitter.saveState()
                splitter_states[splitter_id] = state.toBase64().data().decode('utf-8')
        layout_data['splitter_states'] = splitter_states
        
        # Panel visibility
        panel_visibility = {}
        for panel_id, panel in self.tracked_panels.items():
            if panel:
                panel_visibility[panel_id] = panel.isVisible()
        layout_data['panel_visibility'] = panel_visibility
        
        # Toolbar configuration (if toolbar manager is available)
        if hasattr(self.main_window, 'toolbar_manager'):
            layout_data['toolbar_configuration'] = self.main_window.toolbar_manager.export_toolbar_configuration()
        
        return layout_data
    
    def apply_layout(self, layout_data: Dict[str, Any]):
        """Apply a workspace layout."""
        try:
            # Window geometry
            if 'window_geometry' in layout_data:
                geometry = layout_data['window_geometry']
                
                if geometry.get('maximized', False):
                    self.main_window.showMaximized()
                else:
                    self.main_window.resize(geometry.get('width', 1200), geometry.get('height', 800))
                    if geometry.get('x', -1) >= 0 and geometry.get('y', -1) >= 0:
                        self.main_window.move(geometry['x'], geometry['y'])
            
            # Window state
            if 'window_state' in layout_data:
                try:
                    state_data = layout_data['window_state'].encode('utf-8')
                    window_state = QByteArray.fromBase64(state_data)
                    self.main_window.restoreState(window_state)
                except Exception as e:
                    logger.warning(f"Failed to restore window state: {e}")
            
            # Splitter states
            if 'splitter_states' in layout_data:
                for splitter_id, state_str in layout_data['splitter_states'].items():
                    if splitter_id in self.tracked_splitters:
                        splitter = self.tracked_splitters[splitter_id]
                        if splitter:
                            try:
                                state_data = state_str.encode('utf-8')
                                splitter_state = QByteArray.fromBase64(state_data)
                                splitter.restoreState(splitter_state)
                            except Exception as e:
                                logger.warning(f"Failed to restore splitter state for {splitter_id}: {e}")
            
            # Panel visibility
            if 'panel_visibility' in layout_data:
                for panel_id, visible in layout_data['panel_visibility'].items():
                    if panel_id in self.tracked_panels:
                        panel = self.tracked_panels[panel_id]
                        if panel:
                            panel.setVisible(visible)
            
            # Toolbar configuration
            if 'toolbar_configuration' in layout_data and hasattr(self.main_window, 'toolbar_manager'):
                self.main_window.toolbar_manager.import_toolbar_configuration(layout_data['toolbar_configuration'])
            
            logger.info("Applied workspace layout successfully")
            
        except Exception as e:
            logger.error(f"Failed to apply workspace layout: {e}")
            raise
    
    def save_layout(self, layout_id: str, name: str, description: str = "") -> WorkspaceLayout:
        """Save the current workspace as a layout."""
        # Capture current layout
        layout_data = self.capture_current_layout()
        
        # Create layout object
        now = datetime.now().isoformat()
        layout = WorkspaceLayout(
            id=layout_id,
            name=name,
            description=description,
            created_date=now,
            modified_date=now,
            window_geometry=layout_data.get('window_geometry', {}),
            window_state=layout_data.get('window_state', ''),
            splitter_states=layout_data.get('splitter_states', {}),
            toolbar_configuration=layout_data.get('toolbar_configuration', {}),
            panel_visibility=layout_data.get('panel_visibility', {}),
            metadata={}
        )
        
        # Update existing layout if it exists
        if layout_id in self.layouts:
            existing_layout = self.layouts[layout_id]
            layout.created_date = existing_layout.created_date
        
        self.layouts[layout_id] = layout
        self.current_layout_id = layout_id
        
        # Save to file
        self.save_layouts()
        
        self.layout_saved.emit(layout_id)
        self.layouts_changed.emit()
        
        logger.info(f"Saved workspace layout: {name}")
        return layout
    
    def load_layout(self, layout_id: str) -> bool:
        """Load a workspace layout."""
        if layout_id not in self.layouts:
            logger.warning(f"Layout not found: {layout_id}")
            return False
        
        layout = self.layouts[layout_id]
        
        try:
            # Prepare layout data for application
            layout_data = {
                'window_geometry': layout.window_geometry,
                'window_state': layout.window_state,
                'splitter_states': layout.splitter_states,
                'toolbar_configuration': layout.toolbar_configuration,
                'panel_visibility': layout.panel_visibility
            }
            
            # Apply the layout
            self.apply_layout(layout_data)
            
            self.current_layout_id = layout_id
            self.layout_loaded.emit(layout_id)
            
            logger.info(f"Loaded workspace layout: {layout.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load workspace layout {layout_id}: {e}")
            return False
    
    def delete_layout(self, layout_id: str) -> bool:
        """Delete a workspace layout."""
        if layout_id not in self.layouts:
            return False
        
        layout_name = self.layouts[layout_id].name
        del self.layouts[layout_id]
        
        # Clear current layout if it was deleted
        if self.current_layout_id == layout_id:
            self.current_layout_id = None
        
        # Save to file
        self.save_layouts()
        
        self.layout_deleted.emit(layout_id)
        self.layouts_changed.emit()
        
        logger.info(f"Deleted workspace layout: {layout_name}")
        return True
    
    def get_layouts(self) -> Dict[str, WorkspaceLayout]:
        """Get all available layouts."""
        return self.layouts.copy()
    
    def get_layout(self, layout_id: str) -> Optional[WorkspaceLayout]:
        """Get a specific layout."""
        return self.layouts.get(layout_id)
    
    def get_current_layout_id(self) -> Optional[str]:
        """Get the current layout ID."""
        return self.current_layout_id
    
    def create_default_layouts(self):
        """Create default workspace layouts."""
        # Standard layout
        standard_layout = WorkspaceLayout(
            id="standard",
            name="Standard Layout",
            description="Default layout with all panels visible",
            created_date=datetime.now().isoformat(),
            modified_date=datetime.now().isoformat()
        )
        
        # Compact layout
        compact_layout = WorkspaceLayout(
            id="compact",
            name="Compact Layout",
            description="Compact layout for smaller screens",
            created_date=datetime.now().isoformat(),
            modified_date=datetime.now().isoformat()
        )
        
        # Focus layout
        focus_layout = WorkspaceLayout(
            id="focus",
            name="Focus Layout",
            description="Minimal layout for focused work",
            created_date=datetime.now().isoformat(),
            modified_date=datetime.now().isoformat()
        )
        
        self.layouts["standard"] = standard_layout
        self.layouts["compact"] = compact_layout
        self.layouts["focus"] = focus_layout
        
        # Save default layouts
        self.save_layouts()
        
        logger.info("Created default workspace layouts")
    
    def save_layouts(self):
        """Save layouts to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Convert layouts to dictionary format
            layouts_data = {}
            for layout_id, layout in self.layouts.items():
                layouts_data[layout_id] = asdict(layout)
            
            # Save to file
            with open(self.layouts_file, 'w', encoding='utf-8') as f:
                json.dump(layouts_data, f, indent=2)
            
            logger.debug("Saved workspace layouts to file")
            
        except Exception as e:
            logger.error(f"Failed to save workspace layouts: {e}")
    
    def load_layouts(self):
        """Load layouts from file."""
        try:
            if not self.layouts_file.exists():
                return
            
            with open(self.layouts_file, 'r', encoding='utf-8') as f:
                layouts_data = json.load(f)
            
            # Convert dictionary data to layout objects
            for layout_id, data in layouts_data.items():
                layout = WorkspaceLayout(
                    id=data.get('id', layout_id),
                    name=data.get('name', layout_id),
                    description=data.get('description', ''),
                    created_date=data.get('created_date', ''),
                    modified_date=data.get('modified_date', ''),
                    window_geometry=data.get('window_geometry', {}),
                    window_state=data.get('window_state', ''),
                    splitter_states=data.get('splitter_states', {}),
                    toolbar_configuration=data.get('toolbar_configuration', {}),
                    panel_visibility=data.get('panel_visibility', {}),
                    metadata=data.get('metadata', {})
                )
                self.layouts[layout_id] = layout
            
            logger.info(f"Loaded {len(self.layouts)} workspace layouts")
            
        except Exception as e:
            logger.error(f"Failed to load workspace layouts: {e}")
    
    def export_layout(self, layout_id: str, file_path: Path):
        """Export a layout to file."""
        if layout_id not in self.layouts:
            raise ValueError(f"Layout not found: {layout_id}")
        
        layout = self.layouts[layout_id]
        layout_data = asdict(layout)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2)
        
        logger.info(f"Exported layout '{layout.name}' to {file_path}")
    
    def import_layout(self, file_path: Path) -> str:
        """Import a layout from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            layout_data = json.load(f)
        
        # Create layout object
        layout = WorkspaceLayout(
            id=layout_data.get('id', 'imported_layout'),
            name=layout_data.get('name', 'Imported Layout'),
            description=layout_data.get('description', ''),
            created_date=layout_data.get('created_date', datetime.now().isoformat()),
            modified_date=datetime.now().isoformat(),
            window_geometry=layout_data.get('window_geometry', {}),
            window_state=layout_data.get('window_state', ''),
            splitter_states=layout_data.get('splitter_states', {}),
            toolbar_configuration=layout_data.get('toolbar_configuration', {}),
            panel_visibility=layout_data.get('panel_visibility', {}),
            metadata=layout_data.get('metadata', {})
        )
        
        # Ensure unique ID
        original_id = layout.id
        counter = 1
        while layout.id in self.layouts:
            layout.id = f"{original_id}_{counter}"
            counter += 1
        
        self.layouts[layout.id] = layout
        self.save_layouts()
        
        self.layouts_changed.emit()
        
        logger.info(f"Imported layout '{layout.name}' with ID: {layout.id}")
        return layout.id
    
    def create_workspace_menu_actions(self, parent) -> List[QAction]:
        """Create workspace menu actions."""
        actions = []
        
        # Save current layout
        save_action = QAction("Save Current Layout...", parent)
        save_action.triggered.connect(self.show_save_layout_dialog)
        actions.append(save_action)
        
        # Manage layouts
        manage_action = QAction("Manage Layouts...", parent)
        manage_action.triggered.connect(self.show_layout_manager)
        actions.append(manage_action)
        
        # Separator
        separator = QAction(parent)
        separator.setSeparator(True)
        actions.append(separator)
        
        # Layout list
        for layout_id, layout in self.layouts.items():
            layout_action = QAction(layout.name, parent)
            layout_action.setData(layout_id)
            layout_action.triggered.connect(lambda checked, lid=layout_id: self.load_layout(lid))
            
            # Mark current layout
            if layout_id == self.current_layout_id:
                layout_action.setCheckable(True)
                layout_action.setChecked(True)
            
            actions.append(layout_action)
        
        return actions
    
    def show_save_layout_dialog(self):
        """Show dialog to save current layout."""
        from PySide6.QtWidgets import QInputDialog, QMessageBox
        
        name, ok = QInputDialog.getText(
            self.main_window,
            "Save Workspace Layout",
            "Layout name:"
        )
        
        if ok and name:
            layout_id = name.lower().replace(" ", "_")
            
            # Check if layout exists
            if layout_id in self.layouts:
                reply = QMessageBox.question(
                    self.main_window,
                    "Layout Exists",
                    f"A layout named '{name}' already exists. Do you want to overwrite it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply != QMessageBox.Yes:
                    return
            
            self.save_layout(layout_id, name)
            QMessageBox.information(
                self.main_window,
                "Layout Saved",
                f"Workspace layout '{name}' has been saved successfully."
            )
    
    def show_layout_manager(self):
        """Show layout manager dialog."""
        # This would open a comprehensive layout management dialog
        # For now, just show a simple message
        from PySide6.QtWidgets import QMessageBox
        
        layouts_list = "\n".join([f"• {layout.name}" for layout in self.layouts.values()])
        
        QMessageBox.information(
            self.main_window,
            "Workspace Layouts",
            f"Available layouts:\n\n{layouts_list}\n\nUse the View menu to switch between layouts."
        )