"""
User preferences dialog for CSC-Reach application.
Provides comprehensive customization options.
"""

from typing import Dict, Any, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QCheckBox, QSpinBox, QGroupBox,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QFontComboBox, QSlider, QGridLayout, QScrollArea,
    QMessageBox, QFileDialog, QKeySequenceEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QSplitter, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence

from ..core.user_preferences import (
    UserPreferencesManager, ToolbarPosition, WindowLayout,
    KeyboardShortcut
)
from ..core.theme_manager import ThemeManager, ThemeMode
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PreferencesDialog(QDialog):
    """Comprehensive preferences dialog."""
    
    # Signals
    preferences_applied = Signal()
    theme_changed = Signal(str)
    
    def __init__(self, preferences_manager: UserPreferencesManager, 
                 theme_manager: ThemeManager, parent=None):
        super().__init__(parent)
        self.preferences_manager = preferences_manager
        self.theme_manager = theme_manager
        self.i18n = get_i18n_manager()
        
        # Store original preferences for cancel functionality
        self.original_preferences = None
        
        self.setup_ui()
        self.load_current_preferences()
        
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.i18n.tr("preferences"))
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_appearance_tab()
        self.create_interface_tab()
        self.create_keyboard_shortcuts_tab()
        self.create_accessibility_tab()
        self.create_advanced_tab()
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Import/Export buttons
        self.import_btn = QPushButton(self.i18n.tr("import_preferences"))
        self.import_btn.clicked.connect(self.import_preferences)
        button_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton(self.i18n.tr("export_preferences"))
        self.export_btn.clicked.connect(self.export_preferences)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        # Reset button
        self.reset_btn = QPushButton(self.i18n.tr("reset_to_defaults"))
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        # Standard buttons
        self.apply_btn = QPushButton(self.i18n.tr("apply"))
        self.apply_btn.clicked.connect(self.apply_preferences)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton(self.i18n.tr("ok"))
        self.ok_btn.clicked.connect(self.accept_preferences)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton(self.i18n.tr("cancel"))
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def create_appearance_tab(self):
        """Create appearance preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Theme settings
        theme_group = QGroupBox(self.i18n.tr("theme_settings"))
        theme_layout = QGridLayout(theme_group)
        
        theme_layout.addWidget(QLabel(self.i18n.tr("theme") + ":"), 0, 0)
        self.theme_combo = QComboBox()
        theme_options = {
            "system": self.i18n.tr("system_default"),
            "light": self.i18n.tr("light_mode"),
            "dark": self.i18n.tr("dark_mode")
        }
        for value, text in theme_options.items():
            self.theme_combo.addItem(text, value)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        layout.addWidget(theme_group)
        
        # Font settings
        font_group = QGroupBox(self.i18n.tr("font_settings"))
        font_layout = QGridLayout(font_group)
        
        font_layout.addWidget(QLabel(self.i18n.tr("font_family") + ":"), 0, 0)
        self.font_family_combo = QFontComboBox()
        font_layout.addWidget(self.font_family_combo, 0, 1)
        
        font_layout.addWidget(QLabel(self.i18n.tr("font_size") + ":"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setSuffix(" pt")
        font_layout.addWidget(self.font_size_spin, 1, 1)
        
        layout.addWidget(font_group)
        
        # Visual effects
        effects_group = QGroupBox(self.i18n.tr("visual_effects"))
        effects_layout = QVBoxLayout(effects_group)
        
        self.animations_check = QCheckBox(self.i18n.tr("enable_animations"))
        effects_layout.addWidget(self.animations_check)
        
        self.tooltips_check = QCheckBox(self.i18n.tr("show_tooltips"))
        effects_layout.addWidget(self.tooltips_check)
        
        self.high_contrast_check = QCheckBox(self.i18n.tr("high_contrast_mode"))
        effects_layout.addWidget(self.high_contrast_check)
        
        layout.addWidget(effects_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.i18n.tr("appearance"))
    
    def create_interface_tab(self):
        """Create interface preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Window layout
        layout_group = QGroupBox(self.i18n.tr("window_layout"))
        layout_layout = QGridLayout(layout_group)
        
        layout_layout.addWidget(QLabel(self.i18n.tr("layout_style") + ":"), 0, 0)
        self.layout_combo = QComboBox()
        layout_options = {
            WindowLayout.STANDARD: self.i18n.tr("standard_layout"),
            WindowLayout.COMPACT: self.i18n.tr("compact_layout"),
            WindowLayout.WIDE: self.i18n.tr("wide_layout"),
            WindowLayout.MINIMAL: self.i18n.tr("minimal_layout")
        }
        for layout_enum, text in layout_options.items():
            self.layout_combo.addItem(text, layout_enum)
        layout_layout.addWidget(self.layout_combo, 0, 1)
        
        self.remember_geometry_check = QCheckBox(self.i18n.tr("remember_window_geometry"))
        layout_layout.addWidget(self.remember_geometry_check, 1, 0, 1, 2)
        
        self.remember_splitter_check = QCheckBox(self.i18n.tr("remember_splitter_state"))
        layout_layout.addWidget(self.remember_splitter_check, 2, 0, 1, 2)
        
        layout.addWidget(layout_group)
        
        # Toolbar settings
        toolbar_group = QGroupBox(self.i18n.tr("toolbar_settings"))
        toolbar_layout = QGridLayout(toolbar_group)
        
        toolbar_layout.addWidget(QLabel(self.i18n.tr("toolbar_position") + ":"), 0, 0)
        self.toolbar_position_combo = QComboBox()
        position_options = {
            ToolbarPosition.TOP: self.i18n.tr("top"),
            ToolbarPosition.BOTTOM: self.i18n.tr("bottom"),
            ToolbarPosition.LEFT: self.i18n.tr("left"),
            ToolbarPosition.RIGHT: self.i18n.tr("right")
        }
        for pos_enum, text in position_options.items():
            self.toolbar_position_combo.addItem(text, pos_enum)
        toolbar_layout.addWidget(self.toolbar_position_combo, 0, 1)
        
        self.toolbar_visible_check = QCheckBox(self.i18n.tr("show_toolbar"))
        toolbar_layout.addWidget(self.toolbar_visible_check, 1, 0, 1, 2)
        
        self.toolbar_text_check = QCheckBox(self.i18n.tr("show_toolbar_text"))
        toolbar_layout.addWidget(self.toolbar_text_check, 2, 0, 1, 2)
        
        toolbar_layout.addWidget(QLabel(self.i18n.tr("icon_size") + ":"), 3, 0)
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(16, 48)
        self.icon_size_spin.setSuffix(" px")
        toolbar_layout.addWidget(self.icon_size_spin, 3, 1)
        
        layout.addWidget(toolbar_group)
        
        # Status bar settings
        status_group = QGroupBox(self.i18n.tr("status_bar_settings"))
        status_layout = QVBoxLayout(status_group)
        
        self.status_bar_check = QCheckBox(self.i18n.tr("show_status_bar"))
        status_layout.addWidget(self.status_bar_check)
        
        self.progress_details_check = QCheckBox(self.i18n.tr("show_detailed_progress"))
        status_layout.addWidget(self.progress_details_check)
        
        layout.addWidget(status_group)
        
        # Interface mode
        mode_group = QGroupBox(self.i18n.tr("interface_mode"))
        mode_layout = QVBoxLayout(mode_group)
        
        self.compact_mode_check = QCheckBox(self.i18n.tr("compact_mode"))
        mode_layout.addWidget(self.compact_mode_check)
        
        layout.addWidget(mode_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.i18n.tr("interface"))
    
    def create_keyboard_shortcuts_tab(self):
        """Create keyboard shortcuts tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        info_label = QLabel(self.i18n.tr("keyboard_shortcuts_info"))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # Shortcuts table
        self.shortcuts_table = QTableWidget()
        self.shortcuts_table.setColumnCount(3)
        self.shortcuts_table.setHorizontalHeaderLabels([
            self.i18n.tr("action"),
            self.i18n.tr("shortcut"),
            self.i18n.tr("category")
        ])
        
        # Make table fill width
        header = self.shortcuts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        self.shortcuts_table.itemDoubleClicked.connect(self.edit_shortcut)
        layout.addWidget(self.shortcuts_table)
        
        # Shortcut buttons
        shortcut_buttons = QHBoxLayout()
        
        self.edit_shortcut_btn = QPushButton(self.i18n.tr("edit_shortcut"))
        self.edit_shortcut_btn.clicked.connect(self.edit_selected_shortcut)
        shortcut_buttons.addWidget(self.edit_shortcut_btn)
        
        self.reset_shortcut_btn = QPushButton(self.i18n.tr("reset_shortcut"))
        self.reset_shortcut_btn.clicked.connect(self.reset_selected_shortcut)
        shortcut_buttons.addWidget(self.reset_shortcut_btn)
        
        shortcut_buttons.addStretch()
        
        self.reset_all_shortcuts_btn = QPushButton(self.i18n.tr("reset_all_shortcuts"))
        self.reset_all_shortcuts_btn.clicked.connect(self.reset_all_shortcuts)
        shortcut_buttons.addWidget(self.reset_all_shortcuts_btn)
        
        layout.addLayout(shortcut_buttons)
        
        self.tab_widget.addTab(tab, self.i18n.tr("keyboard_shortcuts"))
    
    def create_accessibility_tab(self):
        """Create accessibility preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Screen reader support
        screen_reader_group = QGroupBox(self.i18n.tr("screen_reader_support"))
        screen_reader_layout = QVBoxLayout(screen_reader_group)
        
        self.screen_reader_check = QCheckBox(self.i18n.tr("enable_screen_reader_support"))
        screen_reader_layout.addWidget(self.screen_reader_check)
        
        self.enhanced_focus_check = QCheckBox(self.i18n.tr("enhanced_focus_indicators"))
        screen_reader_layout.addWidget(self.enhanced_focus_check)
        
        layout.addWidget(screen_reader_group)
        
        # Visual accessibility
        visual_group = QGroupBox(self.i18n.tr("visual_accessibility"))
        visual_layout = QVBoxLayout(visual_group)
        
        self.large_fonts_check = QCheckBox(self.i18n.tr("use_large_fonts"))
        visual_layout.addWidget(self.large_fonts_check)
        
        self.high_contrast_mode_check = QCheckBox(self.i18n.tr("high_contrast_mode"))
        visual_layout.addWidget(self.high_contrast_mode_check)
        
        layout.addWidget(visual_group)
        
        # Input accessibility
        input_group = QGroupBox(self.i18n.tr("input_accessibility"))
        input_layout = QVBoxLayout(input_group)
        
        self.keyboard_only_check = QCheckBox(self.i18n.tr("keyboard_navigation_only"))
        input_layout.addWidget(self.keyboard_only_check)
        
        self.voice_control_check = QCheckBox(self.i18n.tr("voice_control_support"))
        input_layout.addWidget(self.voice_control_check)
        
        layout.addWidget(input_group)
        
        # Accessibility info
        info_text = QTextEdit()
        info_text.setMaximumHeight(100)
        info_text.setReadOnly(True)
        info_text.setPlainText(self.i18n.tr("accessibility_info_text"))
        info_text.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6;")
        layout.addWidget(info_text)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.i18n.tr("accessibility"))
    
    def create_advanced_tab(self):
        """Create advanced preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance settings
        performance_group = QGroupBox(self.i18n.tr("performance_settings"))
        performance_layout = QVBoxLayout(performance_group)
        
        # Add performance-related settings here if needed
        performance_info = QLabel(self.i18n.tr("performance_settings_info"))
        performance_info.setWordWrap(True)
        performance_layout.addWidget(performance_info)
        
        layout.addWidget(performance_group)
        
        # Debug settings
        debug_group = QGroupBox(self.i18n.tr("debug_settings"))
        debug_layout = QVBoxLayout(debug_group)
        
        debug_info = QLabel(self.i18n.tr("debug_settings_info"))
        debug_info.setWordWrap(True)
        debug_layout.addWidget(debug_info)
        
        layout.addWidget(debug_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, self.i18n.tr("advanced"))
    
    def load_current_preferences(self):
        """Load current preferences into the UI."""
        prefs = self.preferences_manager.preferences
        
        # Appearance tab
        theme_index = self.theme_combo.findData(prefs.interface.theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        if prefs.interface.font_family:
            font_index = self.font_family_combo.findText(prefs.interface.font_family)
            if font_index >= 0:
                self.font_family_combo.setCurrentIndex(font_index)
        
        self.font_size_spin.setValue(prefs.interface.font_size)
        self.animations_check.setChecked(prefs.interface.animations_enabled)
        self.tooltips_check.setChecked(prefs.interface.show_tooltips)
        self.high_contrast_check.setChecked(prefs.interface.high_contrast)
        
        # Interface tab
        layout_index = self.layout_combo.findData(prefs.window.layout)
        if layout_index >= 0:
            self.layout_combo.setCurrentIndex(layout_index)
        
        self.remember_geometry_check.setChecked(prefs.window.remember_geometry)
        self.remember_splitter_check.setChecked(prefs.window.remember_splitter_state)
        
        position_index = self.toolbar_position_combo.findData(prefs.toolbar.position)
        if position_index >= 0:
            self.toolbar_position_combo.setCurrentIndex(position_index)
        
        self.toolbar_visible_check.setChecked(prefs.toolbar.visible)
        self.toolbar_text_check.setChecked(prefs.toolbar.show_text)
        self.icon_size_spin.setValue(prefs.toolbar.icon_size)
        
        self.status_bar_check.setChecked(prefs.interface.show_status_bar)
        self.progress_details_check.setChecked(prefs.interface.show_progress_details)
        self.compact_mode_check.setChecked(prefs.interface.compact_mode)
        
        # Accessibility tab
        self.screen_reader_check.setChecked(prefs.accessibility.screen_reader_support)
        self.enhanced_focus_check.setChecked(prefs.accessibility.focus_indicators_enhanced)
        self.large_fonts_check.setChecked(prefs.accessibility.large_fonts)
        self.high_contrast_mode_check.setChecked(prefs.accessibility.high_contrast_mode)
        self.keyboard_only_check.setChecked(prefs.accessibility.keyboard_navigation_only)
        self.voice_control_check.setChecked(prefs.accessibility.voice_control_enabled)
        
        # Load keyboard shortcuts
        self.load_keyboard_shortcuts()
    
    def load_keyboard_shortcuts(self):
        """Load keyboard shortcuts into the table."""
        shortcuts = self.preferences_manager.get_keyboard_shortcuts()
        
        self.shortcuts_table.setRowCount(len(shortcuts))
        
        for row, shortcut in enumerate(shortcuts):
            # Action
            action_item = QTableWidgetItem(shortcut.description)
            action_item.setData(Qt.UserRole, shortcut.action)
            self.shortcuts_table.setItem(row, 0, action_item)
            
            # Shortcut
            shortcut_item = QTableWidgetItem(shortcut.sequence)
            self.shortcuts_table.setItem(row, 1, shortcut_item)
            
            # Category
            category_item = QTableWidgetItem(shortcut.category.title())
            self.shortcuts_table.setItem(row, 2, category_item)
    
    def on_theme_changed(self):
        """Handle theme change."""
        theme_value = self.theme_combo.currentData()
        if theme_value:
            try:
                theme_mode = ThemeMode(theme_value)
                self.theme_manager.set_theme(theme_mode)
            except ValueError:
                pass
    
    def edit_shortcut(self, item):
        """Edit a keyboard shortcut."""
        if item.column() == 1:  # Shortcut column
            self.edit_selected_shortcut()
    
    def edit_selected_shortcut(self):
        """Edit the selected keyboard shortcut."""
        current_row = self.shortcuts_table.currentRow()
        if current_row < 0:
            return
        
        action_item = self.shortcuts_table.item(current_row, 0)
        shortcut_item = self.shortcuts_table.item(current_row, 1)
        
        if not action_item or not shortcut_item:
            return
        
        action = action_item.data(Qt.UserRole)
        current_sequence = shortcut_item.text()
        
        # Create shortcut edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(self.i18n.tr("edit_keyboard_shortcut"))
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"{self.i18n.tr('action')}: {action_item.text()}"))
        
        sequence_edit = QKeySequenceEdit()
        sequence_edit.setKeySequence(QKeySequence(current_sequence))
        layout.addWidget(sequence_edit)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton(self.i18n.tr("ok"))
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton(self.i18n.tr("cancel"))
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.Accepted:
            new_sequence = sequence_edit.keySequence().toString()
            shortcut_item.setText(new_sequence)
    
    def reset_selected_shortcut(self):
        """Reset the selected shortcut to default."""
        current_row = self.shortcuts_table.currentRow()
        if current_row < 0:
            return
        
        # This would need to be implemented with default shortcuts lookup
        QMessageBox.information(self, self.i18n.tr("info"), 
                               self.i18n.tr("shortcut_reset_not_implemented"))
    
    def reset_all_shortcuts(self):
        """Reset all shortcuts to defaults."""
        reply = QMessageBox.question(
            self, 
            self.i18n.tr("confirm_reset"),
            self.i18n.tr("reset_all_shortcuts_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.preferences_manager.reset_shortcuts_to_default()
            self.load_keyboard_shortcuts()
    
    def apply_preferences(self):
        """Apply current preferences."""
        self.save_preferences_from_ui()
        self.preferences_applied.emit()
    
    def accept_preferences(self):
        """Accept and apply preferences."""
        self.apply_preferences()
        self.accept()
    
    def save_preferences_from_ui(self):
        """Save preferences from UI to preferences manager."""
        # Theme
        theme_value = self.theme_combo.currentData()
        if theme_value:
            self.preferences_manager.set_theme(theme_value)
        
        # Font settings
        font_family = self.font_family_combo.currentText()
        font_size = self.font_size_spin.value()
        self.preferences_manager.set_font_settings(font_family, font_size)
        
        # Interface settings
        self.preferences_manager.preferences.interface.animations_enabled = self.animations_check.isChecked()
        self.preferences_manager.preferences.interface.show_tooltips = self.tooltips_check.isChecked()
        self.preferences_manager.preferences.interface.high_contrast = self.high_contrast_check.isChecked()
        self.preferences_manager.preferences.interface.show_status_bar = self.status_bar_check.isChecked()
        self.preferences_manager.preferences.interface.show_progress_details = self.progress_details_check.isChecked()
        self.preferences_manager.preferences.interface.compact_mode = self.compact_mode_check.isChecked()
        
        # Window settings
        layout_value = self.layout_combo.currentData()
        if layout_value:
            self.preferences_manager.set_window_layout(layout_value)
        
        self.preferences_manager.preferences.window.remember_geometry = self.remember_geometry_check.isChecked()
        self.preferences_manager.preferences.window.remember_splitter_state = self.remember_splitter_check.isChecked()
        
        # Toolbar settings
        position_value = self.toolbar_position_combo.currentData()
        if position_value:
            self.preferences_manager.set_toolbar_position(position_value)
        
        self.preferences_manager.preferences.toolbar.visible = self.toolbar_visible_check.isChecked()
        self.preferences_manager.preferences.toolbar.show_text = self.toolbar_text_check.isChecked()
        self.preferences_manager.preferences.toolbar.icon_size = self.icon_size_spin.value()
        
        # Accessibility settings
        self.preferences_manager.set_accessibility_option("screen_reader_support", self.screen_reader_check.isChecked())
        self.preferences_manager.set_accessibility_option("focus_indicators_enhanced", self.enhanced_focus_check.isChecked())
        self.preferences_manager.set_accessibility_option("large_fonts", self.large_fonts_check.isChecked())
        self.preferences_manager.set_accessibility_option("high_contrast_mode", self.high_contrast_mode_check.isChecked())
        self.preferences_manager.set_accessibility_option("keyboard_navigation_only", self.keyboard_only_check.isChecked())
        self.preferences_manager.set_accessibility_option("voice_control_enabled", self.voice_control_check.isChecked())
        
        # Save keyboard shortcuts
        for row in range(self.shortcuts_table.rowCount()):
            action_item = self.shortcuts_table.item(row, 0)
            shortcut_item = self.shortcuts_table.item(row, 1)
            
            if action_item and shortcut_item:
                action = action_item.data(Qt.UserRole)
                sequence = shortcut_item.text()
                self.preferences_manager.update_keyboard_shortcut(action, sequence)
        
        # Save all preferences
        self.preferences_manager.save_preferences()
    
    def import_preferences(self):
        """Import preferences from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.i18n.tr("import_preferences"),
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                from pathlib import Path
                self.preferences_manager.import_preferences(Path(file_path))
                self.load_current_preferences()
                QMessageBox.information(self, self.i18n.tr("success"), 
                                      self.i18n.tr("preferences_imported_successfully"))
            except Exception as e:
                QMessageBox.critical(self, self.i18n.tr("error"), 
                                   self.i18n.tr("failed_to_import_preferences", error=str(e)))
    
    def export_preferences(self):
        """Export preferences to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.i18n.tr("export_preferences"),
            "csc_reach_preferences.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                from pathlib import Path
                self.preferences_manager.export_preferences(Path(file_path))
                QMessageBox.information(self, self.i18n.tr("success"), 
                                      self.i18n.tr("preferences_exported_successfully"))
            except Exception as e:
                QMessageBox.critical(self, self.i18n.tr("error"), 
                                   self.i18n.tr("failed_to_export_preferences", error=str(e)))
    
    def reset_to_defaults(self):
        """Reset all preferences to defaults."""
        reply = QMessageBox.question(
            self,
            self.i18n.tr("confirm_reset"),
            self.i18n.tr("reset_preferences_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.preferences_manager.reset_to_defaults()
            self.load_current_preferences()
            QMessageBox.information(self, self.i18n.tr("success"), 
                                  self.i18n.tr("preferences_reset_successfully"))