"""
Modern progress dialog with advanced progress tracking and status display.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, 
    QPushButton, QTextEdit, QGroupBox, QScrollArea, QWidget,
    QFrame, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor

from ..core.progress_manager import ProgressManager, Operation, OperationStatus
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ModernProgressDialog(QDialog):
    """Modern progress dialog with detailed status information."""
    
    # Signals
    cancel_requested = Signal(str)  # operation_id
    pause_requested = Signal(str)   # operation_id
    resume_requested = Signal(str)  # operation_id
    
    def __init__(self, progress_manager: ProgressManager, operation_id: str, parent=None):
        super().__init__(parent)
        self.progress_manager = progress_manager
        self.operation_id = operation_id
        self.i18n = get_i18n_manager()
        
        self.operation = self.progress_manager.get_operation(operation_id)
        if not self.operation:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        self.setup_ui()
        self.connect_signals()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)  # Update every 500ms
        
        # Initial update
        self.update_display()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle(self.i18n.tr("operation_progress"))
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Header section
        self.create_header_section(layout)
        
        # Progress section
        self.create_progress_section(layout)
        
        # Steps section
        self.create_steps_section(layout)
        
        # Log section
        self.create_log_section(layout)
        
        # Button section
        self.create_button_section(layout)
    
    def create_header_section(self, parent_layout):
        """Create the header section with operation info."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        
        header_layout = QVBoxLayout(header_frame)
        
        # Operation name
        self.operation_name_label = QLabel(self.operation.name)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.operation_name_label.setFont(font)
        header_layout.addWidget(self.operation_name_label)
        
        # Operation details
        details_layout = QGridLayout()
        
        # Type
        details_layout.addWidget(QLabel(self.i18n.tr("operation_type") + ":"), 0, 0)
        self.type_label = QLabel(self.operation.operation_type.value.replace("_", " ").title())
        details_layout.addWidget(self.type_label, 0, 1)
        
        # Status
        details_layout.addWidget(QLabel(self.i18n.tr("status") + ":"), 0, 2)
        self.status_label = QLabel()
        details_layout.addWidget(self.status_label, 0, 3)
        
        # Start time
        details_layout.addWidget(QLabel(self.i18n.tr("started") + ":"), 1, 0)
        self.start_time_label = QLabel()
        details_layout.addWidget(self.start_time_label, 1, 1)
        
        # Duration
        details_layout.addWidget(QLabel(self.i18n.tr("duration") + ":"), 1, 2)
        self.duration_label = QLabel()
        details_layout.addWidget(self.duration_label, 1, 3)
        
        header_layout.addLayout(details_layout)
        parent_layout.addWidget(header_frame)
    
    def create_progress_section(self, parent_layout):
        """Create the progress section."""
        progress_group = QGroupBox(self.i18n.tr("progress"))
        progress_layout = QVBoxLayout(progress_group)
        
        # Overall progress
        overall_layout = QHBoxLayout()
        overall_layout.addWidget(QLabel(self.i18n.tr("overall_progress") + ":"))
        
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setMinimum(0)
        self.overall_progress_bar.setMaximum(100)
        self.overall_progress_bar.setTextVisible(True)
        overall_layout.addWidget(self.overall_progress_bar)
        
        self.overall_percentage_label = QLabel("0%")
        overall_layout.addWidget(self.overall_percentage_label)
        
        progress_layout.addLayout(overall_layout)
        
        # Current step progress
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel(self.i18n.tr("current_step") + ":"))
        
        self.step_progress_bar = QProgressBar()
        self.step_progress_bar.setMinimum(0)
        self.step_progress_bar.setMaximum(100)
        self.step_progress_bar.setTextVisible(True)
        step_layout.addWidget(self.step_progress_bar)
        
        self.step_percentage_label = QLabel("0%")
        step_layout.addWidget(self.step_percentage_label)
        
        progress_layout.addLayout(step_layout)
        
        # Status text
        self.status_text_label = QLabel(self.i18n.tr("initializing"))
        self.status_text_label.setWordWrap(True)
        progress_layout.addWidget(self.status_text_label)
        
        # Time estimates
        estimates_layout = QHBoxLayout()
        
        estimates_layout.addWidget(QLabel(self.i18n.tr("estimated_remaining") + ":"))
        self.remaining_time_label = QLabel(self.i18n.tr("calculating"))
        estimates_layout.addWidget(self.remaining_time_label)
        
        estimates_layout.addStretch()
        
        estimates_layout.addWidget(QLabel(self.i18n.tr("estimated_completion") + ":"))
        self.completion_time_label = QLabel(self.i18n.tr("calculating"))
        estimates_layout.addWidget(self.completion_time_label)
        
        progress_layout.addLayout(estimates_layout)
        
        parent_layout.addWidget(progress_group)
    
    def create_steps_section(self, parent_layout):
        """Create the steps section."""
        steps_group = QGroupBox(self.i18n.tr("operation_steps"))
        steps_layout = QVBoxLayout(steps_group)
        
        # Steps scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(150)
        
        self.steps_widget = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_widget)
        
        scroll_area.setWidget(self.steps_widget)
        steps_layout.addWidget(scroll_area)
        
        parent_layout.addWidget(steps_group)
    
    def create_log_section(self, parent_layout):
        """Create the log section."""
        log_group = QGroupBox(self.i18n.tr("operation_log"))
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(120)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 10px;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        parent_layout.addWidget(log_group)
    
    def create_button_section(self, parent_layout):
        """Create the button section."""
        button_layout = QHBoxLayout()
        
        # Pause/Resume button
        self.pause_resume_btn = QPushButton()
        self.pause_resume_btn.clicked.connect(self.toggle_pause_resume)
        button_layout.addWidget(self.pause_resume_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton(self.i18n.tr("cancel"))
        self.cancel_btn.clicked.connect(self.cancel_operation)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        # Close button (only enabled when operation is complete)
        self.close_btn = QPushButton(self.i18n.tr("close"))
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        button_layout.addWidget(self.close_btn)
        
        parent_layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect progress manager signals."""
        self.progress_manager.operation_updated.connect(self.on_operation_updated)
        self.progress_manager.operation_step_changed.connect(self.on_step_changed)
        self.progress_manager.operation_completed.connect(self.on_operation_completed)
        self.progress_manager.operation_cancelled.connect(self.on_operation_cancelled)
        self.progress_manager.operation_paused.connect(self.on_operation_paused)
        self.progress_manager.operation_resumed.connect(self.on_operation_resumed)
    
    def update_display(self):
        """Update the display with current operation status."""
        if not self.operation:
            return
        
        # Update status
        status_text = self.operation.status.value.replace("_", " ").title()
        self.status_label.setText(status_text)
        
        # Update status color
        if self.operation.status == OperationStatus.RUNNING:
            self.status_label.setStyleSheet("color: #007bff;")
        elif self.operation.status == OperationStatus.COMPLETED:
            self.status_label.setStyleSheet("color: #28a745;")
        elif self.operation.status == OperationStatus.FAILED:
            self.status_label.setStyleSheet("color: #dc3545;")
        elif self.operation.status == OperationStatus.CANCELLED:
            self.status_label.setStyleSheet("color: #6c757d;")
        elif self.operation.status == OperationStatus.PAUSED:
            self.status_label.setStyleSheet("color: #ffc107;")
        
        # Update times
        if self.operation.start_time:
            self.start_time_label.setText(self.operation.start_time.strftime("%H:%M:%S"))
        
        duration = self.operation.get_duration()
        if duration:
            self.duration_label.setText(self.format_duration(duration))
        
        # Update progress
        progress_percent = int(self.operation.progress * 100)
        self.overall_progress_bar.setValue(progress_percent)
        self.overall_percentage_label.setText(f"{progress_percent}%")
        
        # Update current step
        if self.operation.steps and self.operation.current_step < len(self.operation.steps):
            current_step = self.operation.steps[self.operation.current_step]
            step_percent = int(current_step.progress * 100)
            self.step_progress_bar.setValue(step_percent)
            self.step_percentage_label.setText(f"{step_percent}%")
        
        # Update time estimates
        remaining = self.operation.get_estimated_remaining()
        if remaining and remaining.total_seconds() > 0:
            self.remaining_time_label.setText(self.format_duration(remaining))
        else:
            self.remaining_time_label.setText(self.i18n.tr("calculating"))
        
        if self.operation.estimated_completion:
            completion_str = self.operation.estimated_completion.strftime("%H:%M:%S")
            self.completion_time_label.setText(completion_str)
        else:
            self.completion_time_label.setText(self.i18n.tr("calculating"))
        
        # Update buttons
        self.update_buttons()
        
        # Update steps display
        self.update_steps_display()
    
    def update_buttons(self):
        """Update button states."""
        if not self.operation:
            return
        
        # Pause/Resume button
        if self.operation.can_pause:
            if self.operation.status == OperationStatus.RUNNING:
                self.pause_resume_btn.setText(self.i18n.tr("pause"))
                self.pause_resume_btn.setEnabled(True)
            elif self.operation.status == OperationStatus.PAUSED:
                self.pause_resume_btn.setText(self.i18n.tr("resume"))
                self.pause_resume_btn.setEnabled(True)
            else:
                self.pause_resume_btn.setEnabled(False)
        else:
            self.pause_resume_btn.setVisible(False)
        
        # Cancel button
        can_cancel = (self.operation.can_cancel and 
                     self.operation.status in [OperationStatus.RUNNING, OperationStatus.PAUSED])
        self.cancel_btn.setEnabled(can_cancel)
        
        # Close button
        is_finished = self.operation.status in [
            OperationStatus.COMPLETED, OperationStatus.CANCELLED, OperationStatus.FAILED
        ]
        self.close_btn.setEnabled(is_finished)
    
    def update_steps_display(self):
        """Update the steps display."""
        # Clear existing steps
        for i in reversed(range(self.steps_layout.count())):
            child = self.steps_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        # Add current steps
        for i, step in enumerate(self.operation.steps):
            step_widget = self.create_step_widget(i, step)
            self.steps_layout.addWidget(step_widget)
        
        self.steps_layout.addStretch()
    
    def create_step_widget(self, index: int, step) -> QWidget:
        """Create a widget for displaying a step."""
        widget = QFrame()
        widget.setFrameStyle(QFrame.StyledPanel)
        
        # Highlight current step
        if index == self.operation.current_step:
            widget.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #2196f3;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
        else:
            widget.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Step number and status icon
        status_icon = self.get_status_icon(step.status)
        status_label = QLabel(f"{index + 1}. {status_icon}")
        layout.addWidget(status_label)
        
        # Step name
        name_label = QLabel(step.name)
        layout.addWidget(name_label)
        
        layout.addStretch()
        
        # Progress for current step
        if index == self.operation.current_step and step.status == OperationStatus.RUNNING:
            progress_bar = QProgressBar()
            progress_bar.setMinimum(0)
            progress_bar.setMaximum(100)
            progress_bar.setValue(int(step.progress * 100))
            progress_bar.setMaximumWidth(100)
            layout.addWidget(progress_bar)
        
        return widget
    
    def get_status_icon(self, status: OperationStatus) -> str:
        """Get status icon for display."""
        icons = {
            OperationStatus.PENDING: "⏳",
            OperationStatus.RUNNING: "🔄",
            OperationStatus.PAUSED: "⏸️",
            OperationStatus.COMPLETED: "✅",
            OperationStatus.CANCELLED: "❌",
            OperationStatus.FAILED: "❌"
        }
        return icons.get(status, "❓")
    
    def format_duration(self, duration: timedelta) -> str:
        """Format duration for display."""
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def add_log_message(self, message: str):
        """Add a message to the log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def toggle_pause_resume(self):
        """Toggle pause/resume state."""
        if self.operation.status == OperationStatus.RUNNING:
            self.pause_requested.emit(self.operation_id)
        elif self.operation.status == OperationStatus.PAUSED:
            self.resume_requested.emit(self.operation_id)
    
    def cancel_operation(self):
        """Cancel the operation."""
        self.cancel_requested.emit(self.operation_id)
    
    # Signal handlers
    def on_operation_updated(self, operation_id: str, progress: float, status_text: str):
        """Handle operation update."""
        if operation_id == self.operation_id:
            if status_text:
                self.status_text_label.setText(status_text)
                self.add_log_message(status_text)
    
    def on_step_changed(self, operation_id: str, step_number: int, step_name: str):
        """Handle step change."""
        if operation_id == self.operation_id:
            message = self.i18n.tr("step_started", step=step_number + 1, name=step_name)
            self.add_log_message(message)
    
    def on_operation_completed(self, operation_id: str, success: bool, message: str):
        """Handle operation completion."""
        if operation_id == self.operation_id:
            status = self.i18n.tr("completed_successfully") if success else self.i18n.tr("completed_with_errors")
            self.add_log_message(f"{status}: {message}")
            self.update_timer.stop()
    
    def on_operation_cancelled(self, operation_id: str):
        """Handle operation cancellation."""
        if operation_id == self.operation_id:
            self.add_log_message(self.i18n.tr("operation_cancelled"))
            self.update_timer.stop()
    
    def on_operation_paused(self, operation_id: str):
        """Handle operation pause."""
        if operation_id == self.operation_id:
            self.add_log_message(self.i18n.tr("operation_paused"))
    
    def on_operation_resumed(self, operation_id: str):
        """Handle operation resume."""
        if operation_id == self.operation_id:
            self.add_log_message(self.i18n.tr("operation_resumed"))
    
    def closeEvent(self, event):
        """Handle close event."""
        self.update_timer.stop()
        super().closeEvent(event)