"""
Message Analytics Dialog - GUI for viewing message logs and analytics.
Provides users with comprehensive control and visibility over their messaging activity.
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QDateEdit, QTextEdit, QGroupBox, QGridLayout,
    QProgressBar, QSpinBox, QCheckBox, QMessageBox, QFileDialog, QSplitter,
    QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal, QThread, pyqtSignal
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QPieSeries, QBarSeries, QBarSet

from ..core.message_logger import MessageLogger, MessageLogEntry, SessionSummary, AnalyticsReport
from ..core.models import MessageStatus
from ..utils.logger import get_logger


class AnalyticsWorker(QThread):
    """Worker thread for generating analytics reports."""
    
    report_ready = pyqtSignal(object)  # AnalyticsReport
    error_occurred = pyqtSignal(str)
    
    def __init__(self, message_logger: MessageLogger, days: int):
        super().__init__()
        self.message_logger = message_logger
        self.days = days
    
    def run(self):
        try:
            report = self.message_logger.generate_analytics_report(self.days)
            self.report_ready.emit(report)
        except Exception as e:
            self.error_occurred.emit(str(e))


class MessageAnalyticsDialog(QDialog):
    """
    Comprehensive message analytics and logging dialog.
    
    Provides users with:
    - Real-time message logs
    - Session history
    - Analytics and insights
    - Data export capabilities
    - Data management controls
    """
    
    def __init__(self, message_logger: MessageLogger, parent=None):
        super().__init__(parent)
        self.message_logger = message_logger
        self.logger = get_logger(__name__)
        
        self.setWindowTitle("Message Analytics & Logs")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_current_tab)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
        
        self.setup_ui()
        self.load_initial_data()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        
        # Header with quick stats
        self.setup_header(layout)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Set up tabs
        self.setup_overview_tab()
        self.setup_message_logs_tab()
        self.setup_session_history_tab()
        self.setup_analytics_tab()
        self.setup_data_management_tab()
        
        # Footer with controls
        self.setup_footer(layout)
    
    def setup_header(self, layout: QVBoxLayout):
        """Set up the header with quick statistics."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header_frame)
        
        # Quick stats
        self.stats_labels = {}
        stats = [
            ("messages_30d", "Messages (30d)", "0"),
            ("success_rate", "Success Rate", "0%"),
            ("active_session", "Active Session", "No"),
            ("most_used_channel", "Top Channel", "None")
        ]
        
        for key, label, default in stats:
            group = QGroupBox(label)
            group_layout = QVBoxLayout(group)
            
            value_label = QLabel(default)
            value_label.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(14)
            font.setBold(True)
            value_label.setFont(font)
            
            group_layout.addWidget(value_label)
            header_layout.addWidget(group)
            
            self.stats_labels[key] = value_label
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_stats)
        header_layout.addWidget(refresh_btn)
        
        layout.addWidget(header_frame)
    
    def setup_overview_tab(self):
        """Set up the overview tab with key metrics."""
        overview_widget = QWidget()
        layout = QVBoxLayout(overview_widget)
        
        # Charts area
        charts_splitter = QSplitter(Qt.Horizontal)
        
        # Success rate chart
        self.success_chart = self.create_success_rate_chart()
        charts_splitter.addWidget(self.success_chart)
        
        # Channel usage chart
        self.channel_chart = self.create_channel_usage_chart()
        charts_splitter.addWidget(self.channel_chart)
        
        layout.addWidget(charts_splitter)
        
        # Recent activity
        recent_group = QGroupBox("Recent Activity")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_activity_table = QTableWidget()
        self.recent_activity_table.setColumnCount(5)
        self.recent_activity_table.setHorizontalHeaderLabels([
            "Time", "Channel", "Recipient", "Status", "Template"
        ])
        recent_layout.addWidget(self.recent_activity_table)
        
        layout.addWidget(recent_group)
        
        self.tab_widget.addTab(overview_widget, "Overview")
    
    def setup_message_logs_tab(self):
        """Set up the message logs tab."""
        logs_widget = QWidget()
        layout = QVBoxLayout(logs_widget)
        
        # Filters
        filters_frame = QFrame()
        filters_layout = QHBoxLayout(filters_frame)
        
        # Date range
        filters_layout.addWidget(QLabel("Days:"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(1, 365)
        self.days_spin.setValue(30)
        self.days_spin.valueChanged.connect(self.refresh_message_logs)
        filters_layout.addWidget(self.days_spin)
        
        # Channel filter
        filters_layout.addWidget(QLabel("Channel:"))
        self.channel_filter = QComboBox()
        self.channel_filter.addItems(["All", "email", "whatsapp"])
        self.channel_filter.currentTextChanged.connect(self.refresh_message_logs)
        filters_layout.addWidget(self.channel_filter)
        
        # Status filter
        filters_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "sent", "failed", "pending", "cancelled"])
        self.status_filter.currentTextChanged.connect(self.refresh_message_logs)
        filters_layout.addWidget(self.status_filter)
        
        filters_layout.addStretch()
        
        # Export button
        export_btn = QPushButton("Export Logs")
        export_btn.clicked.connect(self.export_message_logs)
        filters_layout.addWidget(export_btn)
        
        layout.addWidget(filters_frame)
        
        # Message logs table
        self.message_logs_table = QTableWidget()
        self.message_logs_table.setColumnCount(8)
        self.message_logs_table.setHorizontalHeaderLabels([
            "Timestamp", "Channel", "Template", "Recipient", "Company", 
            "Status", "Error", "Message ID"
        ])
        self.message_logs_table.setSortingEnabled(True)
        layout.addWidget(self.message_logs_table)
        
        self.tab_widget.addTab(logs_widget, "Message Logs")
    
    def setup_session_history_tab(self):
        """Set up the session history tab."""
        sessions_widget = QWidget()
        layout = QVBoxLayout(sessions_widget)
        
        # Session history table
        self.sessions_table = QTableWidget()
        self.sessions_table.setColumnCount(9)
        self.sessions_table.setHorizontalHeaderLabels([
            "Session ID", "Start Time", "End Time", "Channel", "Template",
            "Total", "Successful", "Failed", "Success Rate"
        ])
        self.sessions_table.setSortingEnabled(True)
        self.sessions_table.itemSelectionChanged.connect(self.on_session_selected)
        layout.addWidget(self.sessions_table)
        
        # Session details
        details_group = QGroupBox("Session Details")
        details_layout = QVBoxLayout(details_group)
        
        self.session_details_text = QTextEdit()
        self.session_details_text.setMaximumHeight(150)
        details_layout.addWidget(self.session_details_text)
        
        layout.addWidget(details_group)
        
        self.tab_widget.addTab(sessions_widget, "Session History")
    
    def setup_analytics_tab(self):
        """Set up the analytics tab."""
        analytics_widget = QWidget()
        layout = QVBoxLayout(analytics_widget)
        
        # Analytics controls
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("Analysis Period:"))
        self.analytics_days = QSpinBox()
        self.analytics_days.setRange(7, 365)
        self.analytics_days.setValue(30)
        controls_layout.addWidget(self.analytics_days)
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_analytics_report)
        controls_layout.addWidget(generate_btn)
        
        controls_layout.addStretch()
        
        # Export analytics button
        export_analytics_btn = QPushButton("Export Report")
        export_analytics_btn.clicked.connect(self.export_analytics_report)
        controls_layout.addWidget(export_analytics_btn)
        
        layout.addWidget(controls_frame)
        
        # Analytics content
        self.analytics_scroll = QScrollArea()
        self.analytics_content = QWidget()
        self.analytics_layout = QVBoxLayout(self.analytics_content)
        
        # Placeholder for analytics
        placeholder_label = QLabel("Click 'Generate Report' to view analytics")
        placeholder_label.setAlignment(Qt.AlignCenter)
        self.analytics_layout.addWidget(placeholder_label)
        
        self.analytics_scroll.setWidget(self.analytics_content)
        self.analytics_scroll.setWidgetResizable(True)
        layout.addWidget(self.analytics_scroll)
        
        self.tab_widget.addTab(analytics_widget, "Analytics")
    
    def setup_data_management_tab(self):
        """Set up the data management tab."""
        management_widget = QWidget()
        layout = QVBoxLayout(management_widget)
        
        # Data export section
        export_group = QGroupBox("Data Export")
        export_layout = QGridLayout(export_group)
        
        export_layout.addWidget(QLabel("Export Format:"), 0, 0)
        self.export_format = QComboBox()
        self.export_format.addItems(["JSON", "CSV"])
        export_layout.addWidget(self.export_format, 0, 1)
        
        export_layout.addWidget(QLabel("Days to Export:"), 1, 0)
        self.export_days = QSpinBox()
        self.export_days.setRange(1, 365)
        self.export_days.setValue(30)
        export_layout.addWidget(self.export_days, 1, 1)
        
        export_data_btn = QPushButton("Export All Data")
        export_data_btn.clicked.connect(self.export_all_data)
        export_layout.addWidget(export_data_btn, 2, 0, 1, 2)
        
        layout.addWidget(export_group)
        
        # Data cleanup section
        cleanup_group = QGroupBox("Data Management")
        cleanup_layout = QGridLayout(cleanup_group)
        
        cleanup_layout.addWidget(QLabel("Delete data older than:"), 0, 0)
        self.cleanup_days = QSpinBox()
        self.cleanup_days.setRange(30, 365)
        self.cleanup_days.setValue(90)
        cleanup_layout.addWidget(self.cleanup_days, 0, 1)
        cleanup_layout.addWidget(QLabel("days"), 0, 2)
        
        cleanup_btn = QPushButton("Delete Old Data")
        cleanup_btn.clicked.connect(self.cleanup_old_data)
        cleanup_layout.addWidget(cleanup_btn, 1, 0, 1, 3)
        
        layout.addWidget(cleanup_group)
        
        # Database info
        info_group = QGroupBox("Database Information")
        info_layout = QVBoxLayout(info_group)
        
        self.db_info_label = QLabel("Loading database information...")
        info_layout.addWidget(self.db_info_label)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(management_widget, "Data Management")
    
    def setup_footer(self, layout: QVBoxLayout):
        """Set up the footer with action buttons."""
        footer_layout = QHBoxLayout()
        
        # Auto-refresh checkbox
        self.auto_refresh_cb = QCheckBox("Auto-refresh (30s)")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.toggled.connect(self.toggle_auto_refresh)
        footer_layout.addWidget(self.auto_refresh_cb)
        
        footer_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addLayout(footer_layout)
    
    def create_success_rate_chart(self) -> QChartView:
        """Create success rate chart."""
        chart = QChart()
        chart.setTitle("Success Rate Over Time")
        
        # This would be populated with actual data
        series = QLineSeries()
        series.setName("Success Rate %")
        
        chart.addSeries(series)
        chart.createDefaultAxes()
        
        chart_view = QChartView(chart)
        return chart_view
    
    def create_channel_usage_chart(self) -> QChartView:
        """Create channel usage pie chart."""
        chart = QChart()
        chart.setTitle("Channel Usage")
        
        series = QPieSeries()
        series.append("Email", 70)
        series.append("WhatsApp", 30)
        
        chart.addSeries(series)
        
        chart_view = QChartView(chart)
        return chart_view
    
    def load_initial_data(self):
        """Load initial data for all tabs."""
        self.refresh_stats()
        self.refresh_message_logs()
        self.refresh_session_history()
        self.update_db_info()
    
    def refresh_stats(self):
        """Refresh the header statistics."""
        try:
            stats = self.message_logger.get_quick_stats()
            
            self.stats_labels["messages_30d"].setText(str(stats["messages_last_30_days"]))
            self.stats_labels["success_rate"].setText(f"{stats['success_rate_30_days']}%")
            self.stats_labels["active_session"].setText("Yes" if stats["current_session_active"] else "No")
            self.stats_labels["most_used_channel"].setText(stats["most_used_channel"])
            
        except Exception as e:
            self.logger.error(f"Error refreshing stats: {e}")
    
    def refresh_message_logs(self):
        """Refresh the message logs table."""
        try:
            days = self.days_spin.value()
            channel = self.channel_filter.currentText()
            status = self.status_filter.currentText()
            
            # Get filtered logs
            channel_filter = None if channel == "All" else channel
            status_filter = None if status == "All" else MessageStatus(status)
            
            logs = self.message_logger.get_message_history(
                days=days, 
                channel=channel_filter, 
                status=status_filter
            )
            
            # Populate table
            self.message_logs_table.setRowCount(len(logs))
            
            for row, log in enumerate(logs):
                self.message_logs_table.setItem(row, 0, QTableWidgetItem(
                    log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                ))
                self.message_logs_table.setItem(row, 1, QTableWidgetItem(log.channel))
                self.message_logs_table.setItem(row, 2, QTableWidgetItem(log.template_name))
                self.message_logs_table.setItem(row, 3, QTableWidgetItem(log.recipient_email))
                self.message_logs_table.setItem(row, 4, QTableWidgetItem(log.recipient_company))
                self.message_logs_table.setItem(row, 5, QTableWidgetItem(log.message_status))
                self.message_logs_table.setItem(row, 6, QTableWidgetItem(log.error_message or ""))
                self.message_logs_table.setItem(row, 7, QTableWidgetItem(log.message_id or ""))
            
            self.message_logs_table.resizeColumnsToContents()
            
            # Update recent activity in overview
            self.update_recent_activity(logs[:10])  # Show last 10
            
        except Exception as e:
            self.logger.error(f"Error refreshing message logs: {e}")
    
    def refresh_session_history(self):
        """Refresh the session history table."""
        try:
            sessions = self.message_logger.get_session_history(days=30)
            
            self.sessions_table.setRowCount(len(sessions))
            
            for row, session in enumerate(sessions):
                self.sessions_table.setItem(row, 0, QTableWidgetItem(session.session_id))
                self.sessions_table.setItem(row, 1, QTableWidgetItem(
                    session.start_time.strftime("%Y-%m-%d %H:%M:%S")
                ))
                self.sessions_table.setItem(row, 2, QTableWidgetItem(
                    session.end_time.strftime("%Y-%m-%d %H:%M:%S") if session.end_time else "Active"
                ))
                self.sessions_table.setItem(row, 3, QTableWidgetItem(session.channel))
                self.sessions_table.setItem(row, 4, QTableWidgetItem(session.template_used))
                self.sessions_table.setItem(row, 5, QTableWidgetItem(str(session.total_messages)))
                self.sessions_table.setItem(row, 6, QTableWidgetItem(str(session.successful_messages)))
                self.sessions_table.setItem(row, 7, QTableWidgetItem(str(session.failed_messages)))
                self.sessions_table.setItem(row, 8, QTableWidgetItem(f"{session.success_rate:.1f}%"))
            
            self.sessions_table.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error refreshing session history: {e}")
    
    def update_recent_activity(self, logs: List[MessageLogEntry]):
        """Update the recent activity table in overview."""
        self.recent_activity_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            self.recent_activity_table.setItem(row, 0, QTableWidgetItem(
                log.timestamp.strftime("%H:%M:%S")
            ))
            self.recent_activity_table.setItem(row, 1, QTableWidgetItem(log.channel))
            self.recent_activity_table.setItem(row, 2, QTableWidgetItem(log.recipient_email))
            self.recent_activity_table.setItem(row, 3, QTableWidgetItem(log.message_status))
            self.recent_activity_table.setItem(row, 4, QTableWidgetItem(log.template_name))
        
        self.recent_activity_table.resizeColumnsToContents()
    
    def on_session_selected(self):
        """Handle session selection in the history table."""
        current_row = self.sessions_table.currentRow()
        if current_row >= 0:
            session_id = self.sessions_table.item(current_row, 0).text()
            # Get session details and display them
            # This would fetch more detailed session information
            self.session_details_text.setText(f"Selected session: {session_id}")
    
    def generate_analytics_report(self):
        """Generate comprehensive analytics report."""
        days = self.analytics_days.value()
        
        # Show loading indicator
        self.analytics_layout.addWidget(QLabel("Generating analytics report..."))
        
        # Start worker thread
        self.analytics_worker = AnalyticsWorker(self.message_logger, days)
        self.analytics_worker.report_ready.connect(self.display_analytics_report)
        self.analytics_worker.error_occurred.connect(self.handle_analytics_error)
        self.analytics_worker.start()
    
    def display_analytics_report(self, report: AnalyticsReport):
        """Display the generated analytics report."""
        # Clear existing content
        for i in reversed(range(self.analytics_layout.count())):
            self.analytics_layout.itemAt(i).widget().setParent(None)
        
        # Display report sections
        self.add_analytics_section("Overview", {
            "Total Messages": report.total_messages_sent,
            "Total Sessions": report.total_sessions,
            "Overall Success Rate": f"{report.overall_success_rate:.1f}%",
            "Avg Messages/Session": f"{report.average_messages_per_session:.1f}"
        })
        
        # Add more sections as needed...
        
        self.analytics_layout.addStretch()
    
    def add_analytics_section(self, title: str, data: Dict[str, Any]):
        """Add a section to the analytics display."""
        group = QGroupBox(title)
        layout = QGridLayout(group)
        
        row = 0
        for key, value in data.items():
            layout.addWidget(QLabel(f"{key}:"), row, 0)
            layout.addWidget(QLabel(str(value)), row, 1)
            row += 1
        
        self.analytics_layout.addWidget(group)
    
    def handle_analytics_error(self, error_message: str):
        """Handle analytics generation error."""
        QMessageBox.warning(self, "Analytics Error", f"Failed to generate analytics: {error_message}")
    
    def export_message_logs(self):
        """Export message logs to file."""
        try:
            days = self.days_spin.value()
            channel = self.channel_filter.currentText()
            status = self.status_filter.currentText()
            
            # Get filtered logs
            channel_filter = None if channel == "All" else channel
            status_filter = None if status == "All" else MessageStatus(status)
            
            logs = self.message_logger.get_message_history(
                days=days, 
                channel=channel_filter, 
                status=status_filter
            )
            
            # Save to file
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Message Logs", 
                f"message_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "JSON Files (*.json);;CSV Files (*.csv)"
            )
            
            if filename:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump([log.__dict__ for log in logs], f, indent=2, default=str)
                else:
                    # CSV export logic would go here
                    pass
                
                QMessageBox.information(self, "Export Complete", f"Logs exported to {filename}")
        
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export logs: {e}")
    
    def export_analytics_report(self):
        """Export analytics report to file."""
        # Implementation for exporting analytics report
        pass
    
    def export_all_data(self):
        """Export all user data."""
        try:
            format_type = self.export_format.currentText().lower()
            days = self.export_days.value()
            
            data = self.message_logger.export_data(format_type, days)
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export All Data",
                f"messaging_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format_type}",
                f"{format_type.upper()} Files (*.{format_type})"
            )
            
            if filename:
                with open(filename, 'w') as f:
                    f.write(data)
                
                QMessageBox.information(self, "Export Complete", f"Data exported to {filename}")
        
        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export data: {e}")
    
    def cleanup_old_data(self):
        """Delete old data from the database."""
        days = self.cleanup_days.value()
        
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete all data older than {days} days?\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                deleted_count = self.message_logger.delete_old_data(days)
                QMessageBox.information(
                    self, "Cleanup Complete",
                    f"Deleted {deleted_count} old records."
                )
                self.refresh_current_tab()
                self.update_db_info()
            
            except Exception as e:
                QMessageBox.warning(self, "Cleanup Error", f"Failed to cleanup data: {e}")
    
    def update_db_info(self):
        """Update database information display."""
        try:
            # Get database file size and record counts
            db_path = self.message_logger.db_path
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                
                # Get record counts (simplified)
                stats = self.message_logger.get_quick_stats()
                
                info_text = f"""
Database Path: {db_path}
Database Size: {size_mb:.2f} MB
Messages (30d): {stats['messages_last_30_days']}
Sessions (30d): {stats['sessions_last_30_days']}
                """.strip()
                
                self.db_info_label.setText(info_text)
            else:
                self.db_info_label.setText("Database not found")
        
        except Exception as e:
            self.db_info_label.setText(f"Error loading database info: {e}")
    
    def toggle_auto_refresh(self, enabled: bool):
        """Toggle auto-refresh functionality."""
        if enabled:
            self.refresh_timer.start(30000)
        else:
            self.refresh_timer.stop()
    
    def refresh_current_tab(self):
        """Refresh data for the currently active tab."""
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # Overview
            self.refresh_stats()
            self.refresh_message_logs()  # For recent activity
        elif current_index == 1:  # Message Logs
            self.refresh_message_logs()
        elif current_index == 2:  # Session History
            self.refresh_session_history()
        # Analytics and Data Management tabs don't auto-refresh
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        self.refresh_timer.stop()
        if hasattr(self, 'analytics_worker') and self.analytics_worker.isRunning():
            self.analytics_worker.terminate()
            self.analytics_worker.wait()
        super().closeEvent(event)