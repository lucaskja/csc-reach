"""
Advanced progress tracking and status management for CSC-Reach.
Provides detailed progress indicators and operation history.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from PySide6.QtCore import QObject, Signal, QTimer, QThread

from ..utils.logger import get_logger

logger = get_logger(__name__)


class OperationStatus(Enum):
    """Operation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OperationType(Enum):
    """Operation type enumeration."""
    EMAIL_SENDING = "email_sending"
    WHATSAPP_SENDING = "whatsapp_sending"
    CSV_IMPORT = "csv_import"
    TEMPLATE_EXPORT = "template_export"
    TEMPLATE_IMPORT = "template_import"
    BULK_OPERATION = "bulk_operation"


@dataclass
class OperationStep:
    """Individual step within an operation."""
    id: str
    name: str
    description: str
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0  # 0.0 to 1.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Operation:
    """Represents a trackable operation."""
    id: str
    name: str
    operation_type: OperationType
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0  # Overall progress 0.0 to 1.0
    current_step: int = 0
    total_steps: int = 1
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None
    can_cancel: bool = True
    can_pause: bool = False
    steps: List[OperationStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_duration(self) -> Optional[timedelta]:
        """Get operation duration."""
        if self.start_time:
            end_time = self.end_time or datetime.now()
            return end_time - self.start_time
        return None
    
    def get_estimated_remaining(self) -> Optional[timedelta]:
        """Get estimated remaining time."""
        if self.estimated_completion:
            remaining = self.estimated_completion - datetime.now()
            return remaining if remaining.total_seconds() > 0 else None
        return None


class ProgressManager(QObject):
    """Manages operation progress tracking and history."""
    
    # Signals
    operation_started = Signal(str)  # operation_id
    operation_updated = Signal(str, float, str)  # operation_id, progress, status_text
    operation_step_changed = Signal(str, int, str)  # operation_id, step_number, step_name
    operation_completed = Signal(str, bool, str)  # operation_id, success, message
    operation_cancelled = Signal(str)  # operation_id
    operation_paused = Signal(str)  # operation_id
    operation_resumed = Signal(str)  # operation_id
    
    def __init__(self):
        super().__init__()
        self.operations: Dict[str, Operation] = {}
        self.operation_history: List[Operation] = []
        self.max_history_size = 100
        
        # Timer for progress updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_estimations)
        self.update_timer.start(1000)  # Update every second
    
    def create_operation(
        self,
        operation_id: str,
        name: str,
        operation_type: OperationType,
        total_steps: int = 1,
        can_cancel: bool = True,
        can_pause: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Operation:
        """Create a new operation."""
        operation = Operation(
            id=operation_id,
            name=name,
            operation_type=operation_type,
            total_steps=total_steps,
            can_cancel=can_cancel,
            can_pause=can_pause,
            metadata=metadata or {}
        )
        
        self.operations[operation_id] = operation
        logger.info(f"Created operation: {name} ({operation_id})")
        return operation
    
    def add_operation_steps(self, operation_id: str, steps: List[Dict[str, str]]):
        """Add steps to an operation."""
        if operation_id not in self.operations:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        for i, step_data in enumerate(steps):
            step = OperationStep(
                id=f"{operation_id}_step_{i}",
                name=step_data.get("name", f"Step {i+1}"),
                description=step_data.get("description", "")
            )
            operation.steps.append(step)
        
        operation.total_steps = len(operation.steps)
    
    def start_operation(self, operation_id: str):
        """Start an operation."""
        if operation_id not in self.operations:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        operation.status = OperationStatus.RUNNING
        operation.start_time = datetime.now()
        
        self.operation_started.emit(operation_id)
        logger.info(f"Started operation: {operation.name}")
    
    def update_operation_progress(
        self,
        operation_id: str,
        progress: float,
        status_text: str = "",
        current_step: Optional[int] = None,
        step_progress: Optional[float] = None
    ):
        """Update operation progress."""
        if operation_id not in self.operations:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        operation.progress = max(0.0, min(1.0, progress))
        
        if current_step is not None:
            operation.current_step = current_step
            
            # Update step progress
            if 0 <= current_step < len(operation.steps):
                step = operation.steps[current_step]
                if step.status == OperationStatus.PENDING:
                    step.status = OperationStatus.RUNNING
                    step.start_time = datetime.now()
                
                if step_progress is not None:
                    step.progress = max(0.0, min(1.0, step_progress))
        
        # Update estimation
        self._update_operation_estimation(operation)
        
        self.operation_updated.emit(operation_id, progress, status_text)
    
    def complete_operation_step(self, operation_id: str, step_index: int, success: bool = True, error_message: str = ""):
        """Complete a specific operation step."""
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        if 0 <= step_index < len(operation.steps):
            step = operation.steps[step_index]
            step.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
            step.progress = 1.0
            step.end_time = datetime.now()
            if error_message:
                step.error_message = error_message
            
            self.operation_step_changed.emit(operation_id, step_index, step.name)
    
    def complete_operation(self, operation_id: str, success: bool = True, message: str = ""):
        """Complete an operation."""
        if operation_id not in self.operations:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        operation.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
        operation.progress = 1.0
        operation.end_time = datetime.now()
        
        if message:
            operation.error_message = message if not success else None
        
        # Complete all remaining steps
        for step in operation.steps:
            if step.status in [OperationStatus.PENDING, OperationStatus.RUNNING]:
                step.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
                step.end_time = datetime.now()
        
        # Move to history
        self._move_to_history(operation_id)
        
        self.operation_completed.emit(operation_id, success, message)
        logger.info(f"Completed operation: {operation.name} (success: {success})")
    
    def cancel_operation(self, operation_id: str):
        """Cancel an operation."""
        if operation_id not in self.operations:
            logger.error(f"Operation not found: {operation_id}")
            return
        
        operation = self.operations[operation_id]
        if not operation.can_cancel:
            logger.warning(f"Operation cannot be cancelled: {operation_id}")
            return
        
        operation.status = OperationStatus.CANCELLED
        operation.end_time = datetime.now()
        
        # Cancel all running steps
        for step in operation.steps:
            if step.status == OperationStatus.RUNNING:
                step.status = OperationStatus.CANCELLED
                step.end_time = datetime.now()
        
        # Move to history
        self._move_to_history(operation_id)
        
        self.operation_cancelled.emit(operation_id)
        logger.info(f"Cancelled operation: {operation.name}")
    
    def pause_operation(self, operation_id: str):
        """Pause an operation."""
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        if not operation.can_pause or operation.status != OperationStatus.RUNNING:
            return
        
        operation.status = OperationStatus.PAUSED
        self.operation_paused.emit(operation_id)
        logger.info(f"Paused operation: {operation.name}")
    
    def resume_operation(self, operation_id: str):
        """Resume a paused operation."""
        if operation_id not in self.operations:
            return
        
        operation = self.operations[operation_id]
        if operation.status != OperationStatus.PAUSED:
            return
        
        operation.status = OperationStatus.RUNNING
        self.operation_resumed.emit(operation_id)
        logger.info(f"Resumed operation: {operation.name}")
    
    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """Get an operation by ID."""
        return self.operations.get(operation_id)
    
    def get_active_operations(self) -> List[Operation]:
        """Get all active operations."""
        return [op for op in self.operations.values() 
                if op.status in [OperationStatus.RUNNING, OperationStatus.PAUSED]]
    
    def get_operation_history(self, limit: int = 50) -> List[Operation]:
        """Get operation history."""
        return self.operation_history[-limit:]
    
    def _update_operation_estimation(self, operation: Operation):
        """Update operation time estimation."""
        if operation.status != OperationStatus.RUNNING or operation.progress <= 0:
            return
        
        duration = operation.get_duration()
        if duration:
            # Estimate total time based on current progress
            total_estimated_seconds = duration.total_seconds() / operation.progress
            remaining_seconds = total_estimated_seconds * (1.0 - operation.progress)
            operation.estimated_completion = datetime.now() + timedelta(seconds=remaining_seconds)
    
    def _update_estimations(self):
        """Update estimations for all running operations."""
        for operation in self.operations.values():
            if operation.status == OperationStatus.RUNNING:
                self._update_operation_estimation(operation)
    
    def _move_to_history(self, operation_id: str):
        """Move operation to history."""
        if operation_id in self.operations:
            operation = self.operations.pop(operation_id)
            self.operation_history.append(operation)
            
            # Limit history size
            if len(self.operation_history) > self.max_history_size:
                self.operation_history = self.operation_history[-self.max_history_size:]
    
    def get_operation_summary(self, operation_id: str) -> Dict[str, Any]:
        """Get operation summary for display."""
        operation = self.get_operation(operation_id)
        if not operation:
            # Check history
            for hist_op in self.operation_history:
                if hist_op.id == operation_id:
                    operation = hist_op
                    break
        
        if not operation:
            return {}
        
        duration = operation.get_duration()
        remaining = operation.get_estimated_remaining()
        
        return {
            "id": operation.id,
            "name": operation.name,
            "type": operation.operation_type.value,
            "status": operation.status.value,
            "progress": operation.progress,
            "current_step": operation.current_step,
            "total_steps": operation.total_steps,
            "duration": duration.total_seconds() if duration else None,
            "estimated_remaining": remaining.total_seconds() if remaining else None,
            "can_cancel": operation.can_cancel,
            "can_pause": operation.can_pause,
            "error_message": operation.error_message,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status.value,
                    "progress": step.progress,
                    "error": step.error_message
                }
                for step in operation.steps
            ]
        }


class ProgressTracker(QObject):
    """Simple progress tracker for individual operations."""
    
    progress_updated = Signal(float, str)  # progress, message
    
    def __init__(self, progress_manager: ProgressManager, operation_id: str):
        super().__init__()
        self.progress_manager = progress_manager
        self.operation_id = operation_id
        self.current_progress = 0.0
    
    def update(self, progress: float, message: str = ""):
        """Update progress."""
        self.current_progress = progress
        self.progress_manager.update_operation_progress(
            self.operation_id, progress, message
        )
        self.progress_updated.emit(progress, message)
    
    def set_step(self, step_index: int, step_progress: float = 0.0, message: str = ""):
        """Set current step."""
        self.progress_manager.update_operation_progress(
            self.operation_id, 
            self.current_progress, 
            message, 
            step_index, 
            step_progress
        )
    
    def complete_step(self, step_index: int, success: bool = True, error_message: str = ""):
        """Complete a step."""
        self.progress_manager.complete_operation_step(
            self.operation_id, step_index, success, error_message
        )
    
    def complete(self, success: bool = True, message: str = ""):
        """Complete the operation."""
        self.progress_manager.complete_operation(self.operation_id, success, message)
    
    def cancel(self):
        """Cancel the operation."""
        self.progress_manager.cancel_operation(self.operation_id)