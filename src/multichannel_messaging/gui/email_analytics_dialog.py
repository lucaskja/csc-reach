"""
Email analytics dashboard dialog for viewing email performance metrics and reports.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QTableWidget,
    QTableWidgetItem, QLabel, QPushButton, QComboBox, QGroupBox, QGridLayout,
    QProgressBar, QTextEdit, QDateEdit, QSplitter, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer, QThread
from PySide6.QtGui import QFont, QPalette, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QPieSeries, QBarSeries, QBarSet
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ..core.email_analytics import EmailAnalyticsManager, EmailPerformanceReport, EmailCampaignStats
from ..core.i18n_manager import get_i18n_manager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AnalyticsWorker(QThread):
    """Worker thread for loading analytics data."""
    
    data_loaded = Signal(object)
    error_occurred = Signal(str)
    
    def __init__(self, analytics_manager: EmailAnalyticsManager, start_date: datetime, end_date: datetime):
        super().__init__()
        self.analytics_manager = analytics_manager
        self.start_date = start_date
        self.end_date = end_date
    
    def run(self):
        """Load analytics data in background thread."""
        try:
            report = self.analytics_manager.generate_performance_report(
                start_date=self.start_date,
                end_date=self.end_date
            )
            self.data_loaded.emit(report)
        except Exception as e:
            self.error_occurred.emit(str(e))


class EmailAnalyticsDialog(QDialog):
    """Email analytics dashboard dialog."""
    
    def __init__(self, parent=None):
        """Initialize the analytics dialog."""
        super().__init__(parent)
        self.i18n_manager = get_i18n_manager()
        self.analytics_manager = EmailAnalyticsManager()
        
        # Current data
        self.current_report = None
        self.worker_thread = None
        
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()
        self._load_initial_data()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle(self.i18n_manager.tr("email_analytics_title"))
        self.setModal(True)
        self.resize(1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        
        # Top controls
        controls_layout = self._create_controls()
        main_layout.addLayout(controls_layout)
        
        # Main content tabs
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Overview tab
        overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(overview_tab, self.i18n_manager.tr("overview"))
        
        # Campaigns tab
        campaigns_tab = self._create_campaigns_tab()
        self.tab_widget.addTab(campaigns_tab, self.i18n_manager.tr("campaigns"))
        
        # Performance tab
        performance_tab = self._create_performance_tab()
        self.tab_widget.addTab(performance_tab, self.i18n_manager.tr("performance"))
        
        # Recommendations tab
        recommendations_tab = self._create_recommendations_tab()
        self.tab_widget.addTab(recommendations_tab, self.i18n_manager.tr("recommendations"))
        
        # Bottom buttons
        button_layout = self._create_button_layout()
        main_layout.addLayout(button_layout)
    
    def _create_controls(self) -> QHBoxLayout:
        """Create the top control panel."""
        layout = QHBoxLayout()
        
        # Date range selection
        date_group = QGroupBox(self.i18n_manager.tr("date_range"))
        date_layout = QHBoxLayout(date_group)
        
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.start_date_edit.setCalendarPopup(True)
        
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        
        date_layout.addWidget(QLabel(self.i18n_manager.tr("from")))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QLabel(self.i18n_manager.tr("to")))
        date_layout.addWidget(self.end_date_edit)
        
        # Quick date ranges
        quick_ranges = QComboBox()
        quick_ranges.addItems([
            self.i18n_manager.tr("last_7_days"),
            self.i18n_manager.tr("last_30_days"),
            self.i18n_manager.tr("last_90_days"),
            self.i18n_manager.tr("custom_range")
        ])
        quick_ranges.setCurrentIndex(1)  # Default to last 30 days
        
        # Refresh button
        self.refresh_btn = QPushButton(self.i18n_manager.tr("refresh_data"))
        
        # Loading indicator
        self.loading_label = QLabel(self.i18n_manager.tr("loading"))
        self.loading_label.hide()
        
        layout.addWidget(date_group)
        layout.addWidget(QLabel(self.i18n_manager.tr("quick_range")))
        layout.addWidget(quick_ranges)
        layout.addWidget(self.refresh_btn)
        layout.addStretch()
        layout.addWidget(self.loading_label)
        
        return layout
    
    def _create_overview_tab(self) -> QWidget:
        """Create the overview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Key metrics cards
        metrics_layout = QHBoxLayout()
        
        # Total emails sent card
        self.total_sent_card = self._create_metric_card(
            self.i18n_manager.tr("total_emails_sent"), "0"
        )
        metrics_layout.addWidget(self.total_sent_card)
        
        # Average delivery rate card
        self.delivery_rate_card = self._create_metric_card(
            self.i18n_manager.tr("avg_delivery_rate"), "0%"
        )
        metrics_layout.addWidget(self.delivery_rate_card)
        
        # Average open rate card
        self.open_rate_card = self._create_metric_card(
            self.i18n_manager.tr("avg_open_rate"), "0%"
        )
        metrics_layout.addWidget(self.open_rate_card)
        
        # Average click rate card
        self.click_rate_card = self._create_metric_card(
            self.i18n_manager.tr("avg_click_rate"), "0%"
        )
        metrics_layout.addWidget(self.click_rate_card)
        
        layout.addLayout(metrics_layout)
        
        # Charts section
        charts_splitter = QSplitter(Qt.Horizontal)
        
        # Performance trend chart
        self.trend_chart_view = QChartView()
        self.trend_chart_view.setMinimumHeight(300)
        charts_splitter.addWidget(self.trend_chart_view)
        
        # Email status pie chart
        self.status_chart_view = QChartView()
        self.status_chart_view.setMinimumHeight(300)
        charts_splitter.addWidget(self.status_chart_view)
        
        layout.addWidget(charts_splitter)
        
        return tab
    
    def _create_campaigns_tab(self) -> QWidget:
        """Create the campaigns tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Campaigns table
        self.campaigns_table = QTableWidget()
        self.campaigns_table.setColumnCount(8)
        self.campaigns_table.setHorizontalHeaderLabels([
            self.i18n_manager.tr("campaign_name"),
            self.i18n_manager.tr("sent"),
            self.i18n_manager.tr("delivered"),
            self.i18n_manager.tr("opened"),
            self.i18n_manager.tr("clicked"),
            self.i18n_manager.tr("delivery_rate"),
            self.i18n_manager.tr("open_rate"),
            self.i18n_manager.tr("click_rate")
        ])
        
        # Make table sortable and resizable
        self.campaigns_table.setSortingEnabled(True)
        header = self.campaigns_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.campaigns_table)
        
        return tab
    
    def _create_performance_tab(self) -> QWidget:
        """Create the performance analysis tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance metrics
        metrics_group = QGroupBox(self.i18n_manager.tr("performance_metrics"))
        metrics_layout = QGridLayout(metrics_group)
        
        # Best performing templates
        best_label = QLabel(self.i18n_manager.tr("best_templates"))
        self.best_templates_list = QListWidget()
        self.best_templates_list.setMaximumHeight(150)
        
        # Worst performing templates
        worst_label = QLabel(self.i18n_manager.tr("worst_templates"))
        self.worst_templates_list = QListWidget()
        self.worst_templates_list.setMaximumHeight(150)
        
        metrics_layout.addWidget(best_label, 0, 0)
        metrics_layout.addWidget(self.best_templates_list, 1, 0)
        metrics_layout.addWidget(worst_label, 0, 1)
        metrics_layout.addWidget(self.worst_templates_list, 1, 1)
        
        layout.addWidget(metrics_group)
        
        # Trend analysis chart
        trend_group = QGroupBox(self.i18n_manager.tr("trend_analysis"))
        trend_layout = QVBoxLayout(trend_group)
        
        self.performance_trend_chart = QChartView()
        self.performance_trend_chart.setMinimumHeight(300)
        trend_layout.addWidget(self.performance_trend_chart)
        
        layout.addWidget(trend_group)
        
        return tab
    
    def _create_recommendations_tab(self) -> QWidget:
        """Create the recommendations tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Recommendations list
        recommendations_group = QGroupBox(self.i18n_manager.tr("recommendations"))
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.recommendations_text)
        
        layout.addWidget(recommendations_group)
        
        # Action items
        actions_group = QGroupBox(self.i18n_manager.tr("suggested_actions"))
        actions_layout = QVBoxLayout(actions_group)
        
        self.actions_list = QListWidget()
        actions_layout.addWidget(self.actions_list)
        
        layout.addWidget(actions_group)
        
        return tab
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Create the bottom button layout."""
        layout = QHBoxLayout()
        
        # Export button
        self.export_btn = QPushButton(self.i18n_manager.tr("export_report"))
        
        # Close button
        self.close_btn = QPushButton(self.i18n_manager.tr("close"))
        
        layout.addStretch()
        layout.addWidget(self.export_btn)
        layout.addWidget(self.close_btn)
        
        return layout
    
    def _create_metric_card(self, title: str, value: str) -> QGroupBox:
        """Create a metric card widget."""
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setFont(QFont("Arial", 24, QFont.Bold))
        
        layout.addWidget(value_label)
        card.value_label = value_label  # Store reference for updates
        
        return card
    
    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self.refresh_btn.clicked.connect(self._refresh_data)
        self.export_btn.clicked.connect(self._export_report)
        self.close_btn.clicked.connect(self.close)
    
    def _apply_styles(self) -> None:
        """Apply custom styles to the dialog."""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
            }
            QTableWidget {
                border: 1px solid #cccccc;
                border-radius: 5px;
                gridline-color: #e0e0e0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 5px;
                border: 1px solid #cccccc;
                background-color: #f8f9fa;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
    
    def _load_initial_data(self) -> None:
        """Load initial analytics data."""
        self._refresh_data()
    
    def _refresh_data(self) -> None:
        """Refresh analytics data."""
        # Show loading indicator
        self.loading_label.show()
        self.refresh_btn.setEnabled(False)
        
        # Get date range
        start_date = self.start_date_edit.date().toPython()
        end_date = self.end_date_edit.date().toPython()
        
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        
        # Start worker thread
        self.worker_thread = AnalyticsWorker(
            self.analytics_manager,
            start_datetime,
            end_datetime
        )
        self.worker_thread.data_loaded.connect(self._on_data_loaded)
        self.worker_thread.error_occurred.connect(self._on_error_occurred)
        self.worker_thread.start()
    
    def _on_data_loaded(self, report: EmailPerformanceReport) -> None:
        """Handle loaded analytics data."""
        self.current_report = report
        
        # Update UI
        self._update_overview_tab()
        self._update_campaigns_tab()
        self._update_performance_tab()
        self._update_recommendations_tab()
        
        # Hide loading indicator
        self.loading_label.hide()
        self.refresh_btn.setEnabled(True)
        
        logger.info("Analytics data loaded successfully")
    
    def _on_error_occurred(self, error_message: str) -> None:
        """Handle error during data loading."""
        logger.error(f"Failed to load analytics data: {error_message}")
        
        # Hide loading indicator
        self.loading_label.hide()
        self.refresh_btn.setEnabled(True)
        
        # Show error message
        self.recommendations_text.setPlainText(f"Error loading data: {error_message}")
    
    def _update_overview_tab(self) -> None:
        """Update the overview tab with current data."""
        if not self.current_report:
            return
        
        # Update metric cards
        self.total_sent_card.value_label.setText(str(self.current_report.total_emails_sent))
        self.delivery_rate_card.value_label.setText(f"{self.current_report.average_delivery_rate:.1f}%")
        self.open_rate_card.value_label.setText(f"{self.current_report.average_open_rate:.1f}%")
        self.click_rate_card.value_label.setText(f"{self.current_report.average_click_rate:.1f}%")
        
        # Update charts
        self._update_trend_chart()
        self._update_status_chart()
    
    def _update_campaigns_tab(self) -> None:
        """Update the campaigns tab with current data."""
        if not self.current_report:
            return
        
        # Clear existing data
        self.campaigns_table.setRowCount(0)
        
        # Add campaign data
        for i, campaign in enumerate(self.current_report.campaign_stats):
            self.campaigns_table.insertRow(i)
            
            # Campaign name
            self.campaigns_table.setItem(i, 0, QTableWidgetItem(campaign.campaign_name))
            
            # Metrics
            self.campaigns_table.setItem(i, 1, QTableWidgetItem(str(campaign.total_sent)))
            self.campaigns_table.setItem(i, 2, QTableWidgetItem(str(campaign.total_delivered)))
            self.campaigns_table.setItem(i, 3, QTableWidgetItem(str(campaign.total_opened)))
            self.campaigns_table.setItem(i, 4, QTableWidgetItem(str(campaign.total_clicked)))
            
            # Rates
            self.campaigns_table.setItem(i, 5, QTableWidgetItem(f"{campaign.delivery_rate:.1f}%"))
            self.campaigns_table.setItem(i, 6, QTableWidgetItem(f"{campaign.open_rate:.1f}%"))
            self.campaigns_table.setItem(i, 7, QTableWidgetItem(f"{campaign.click_rate:.1f}%"))
    
    def _update_performance_tab(self) -> None:
        """Update the performance tab with current data."""
        if not self.current_report:
            return
        
        # Update best performing templates
        self.best_templates_list.clear()
        for template in self.current_report.best_performing_templates:
            item_text = f"{template.get('name', 'Unknown')} - {template.get('open_rate', 0):.1f}% open rate"
            self.best_templates_list.addItem(item_text)
        
        # Update worst performing templates
        self.worst_templates_list.clear()
        for template in self.current_report.worst_performing_templates:
            item_text = f"{template.get('name', 'Unknown')} - {template.get('open_rate', 0):.1f}% open rate"
            self.worst_templates_list.addItem(item_text)
        
        # Update performance trend chart
        self._update_performance_trend_chart()
    
    def _update_recommendations_tab(self) -> None:
        """Update the recommendations tab with current data."""
        if not self.current_report:
            return
        
        # Update recommendations text
        recommendations_text = "\n".join([
            f"• {rec}" for rec in self.current_report.recommendations
        ])
        
        if not recommendations_text:
            recommendations_text = self.i18n_manager.tr("no_recommendations")
        
        self.recommendations_text.setPlainText(recommendations_text)
        
        # Update action items
        self.actions_list.clear()
        
        # Generate action items based on performance
        if self.current_report.average_delivery_rate < 95:
            self.actions_list.addItem(self.i18n_manager.tr("action_check_email_lists"))
        
        if self.current_report.average_open_rate < 20:
            self.actions_list.addItem(self.i18n_manager.tr("action_improve_subject_lines"))
        
        if self.current_report.average_click_rate < 2:
            self.actions_list.addItem(self.i18n_manager.tr("action_improve_content"))
    
    def _update_trend_chart(self) -> None:
        """Update the trend chart."""
        # Create a simple line chart for demonstration
        chart = QChart()
        chart.setTitle(self.i18n_manager.tr("performance_trends"))
        
        # Create series for different metrics
        delivery_series = QLineSeries()
        delivery_series.setName(self.i18n_manager.tr("delivery_rate"))
        
        open_series = QLineSeries()
        open_series.setName(self.i18n_manager.tr("open_rate"))
        
        click_series = QLineSeries()
        click_series.setName(self.i18n_manager.tr("click_rate"))
        
        # Add sample data points (in a real implementation, use actual trend data)
        for i in range(7):
            delivery_series.append(i, 95 + (i % 3))
            open_series.append(i, 20 + (i % 5))
            click_series.append(i, 2 + (i % 2))
        
        chart.addSeries(delivery_series)
        chart.addSeries(open_series)
        chart.addSeries(click_series)
        chart.createDefaultAxes()
        
        self.trend_chart_view.setChart(chart)
    
    def _update_status_chart(self) -> None:
        """Update the status pie chart."""
        if not self.current_report:
            return
        
        chart = QChart()
        chart.setTitle(self.i18n_manager.tr("email_status_distribution"))
        
        series = QPieSeries()
        
        # Calculate totals across all campaigns
        total_delivered = sum(c.total_delivered for c in self.current_report.campaign_stats)
        total_bounced = sum(c.total_bounced for c in self.current_report.campaign_stats)
        total_opened = sum(c.total_opened for c in self.current_report.campaign_stats)
        
        if total_delivered > 0:
            series.append(self.i18n_manager.tr("delivered"), total_delivered)
        if total_bounced > 0:
            series.append(self.i18n_manager.tr("bounced"), total_bounced)
        if total_opened > 0:
            series.append(self.i18n_manager.tr("opened"), total_opened)
        
        chart.addSeries(series)
        self.status_chart_view.setChart(chart)
    
    def _update_performance_trend_chart(self) -> None:
        """Update the performance trend chart."""
        # Similar to trend chart but focused on performance metrics
        chart = QChart()
        chart.setTitle(self.i18n_manager.tr("performance_over_time"))
        
        # Use trend data from report if available
        if self.current_report and self.current_report.open_rate_trend:
            series = QLineSeries()
            series.setName(self.i18n_manager.tr("open_rate_trend"))
            
            for date, rate in self.current_report.open_rate_trend:
                # Convert datetime to numeric value for chart
                timestamp = date.timestamp()
                series.append(timestamp, rate)
            
            chart.addSeries(series)
            chart.createDefaultAxes()
        
        self.performance_trend_chart.setChart(chart)
    
    def _export_report(self) -> None:
        """Export the current report."""
        if not self.current_report:
            return
        
        try:
            # Generate report content
            report_content = self._generate_report_content()
            
            # Save to file (simplified - in real implementation, use file dialog)
            from pathlib import Path
            report_path = Path.home() / f"email_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"Report exported to {report_path}")
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
    
    def _generate_report_content(self) -> str:
        """Generate text content for the report."""
        if not self.current_report:
            return ""
        
        content = []
        content.append("EMAIL ANALYTICS REPORT")
        content.append("=" * 50)
        content.append(f"Generated: {self.current_report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Period: {self.current_report.period_start.strftime('%Y-%m-%d')} to {self.current_report.period_end.strftime('%Y-%m-%d')}")
        content.append("")
        
        content.append("OVERVIEW")
        content.append("-" * 20)
        content.append(f"Total Campaigns: {self.current_report.total_campaigns}")
        content.append(f"Total Emails Sent: {self.current_report.total_emails_sent}")
        content.append(f"Average Delivery Rate: {self.current_report.average_delivery_rate:.1f}%")
        content.append(f"Average Open Rate: {self.current_report.average_open_rate:.1f}%")
        content.append(f"Average Click Rate: {self.current_report.average_click_rate:.1f}%")
        content.append("")
        
        if self.current_report.recommendations:
            content.append("RECOMMENDATIONS")
            content.append("-" * 20)
            for rec in self.current_report.recommendations:
                content.append(f"• {rec}")
            content.append("")
        
        return "\n".join(content)