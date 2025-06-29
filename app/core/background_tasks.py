import asyncio
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum
import structlog

logger = structlog.get_logger()

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackgroundTask:
    """Represents a background task."""
    
    def __init__(self, task_id: str, func: Callable, args: tuple = (), kwargs: dict = None):
        self.task_id = task_id
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.status = TaskStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[str] = None
        self.progress: float = 0.0
        self.task: Optional[asyncio.Task] = None

class BackgroundTaskManager:
    """Manages background tasks for the application."""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.tasks: Dict[str, BackgroundTask] = {}
        self.running_tasks: set = set()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start the background task manager."""
        if not self.running:
            self.running = True
            self.worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Background task manager started", max_concurrent_tasks=self.max_concurrent_tasks)
    
    async def stop(self):
        """Stop the background task manager."""
        if self.running:
            self.running = False
            
            # Cancel all running tasks
            for task_id in list(self.running_tasks):
                await self.cancel_task(task_id)
            
            # Cancel worker task
            if self.worker_task:
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Background task manager stopped")
    
    async def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Submit a new background task."""
        if task_id in self.tasks:
            raise ValueError(f"Task with ID {task_id} already exists")
        
        task = BackgroundTask(task_id, func, args, kwargs)
        self.tasks[task_id] = task
        
        await self.task_queue.put(task_id)
        logger.info("Task submitted", task_id=task_id, func_name=func.__name__)
        
        return task_id
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "progress": task.progress,
            "result": task.result,
            "error": task.error
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status == TaskStatus.RUNNING and task.task:
            task.task.cancel()
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.utcnow()
            self.running_tasks.discard(task_id)
            logger.info("Task cancelled", task_id=task_id)
            return True
        
        return False
    
    async def _worker_loop(self):
        """Main worker loop for processing background tasks."""
        while self.running:
            try:
                # Wait for a task to be available
                task_id = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Check if we can run more tasks
                if len(self.running_tasks) >= self.max_concurrent_tasks:
                    # Put the task back in the queue
                    await self.task_queue.put(task_id)
                    await asyncio.sleep(0.1)
                    continue
                
                # Get the task
                task = self.tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # Start the task
                self.running_tasks.add(task_id)
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.utcnow()
                
                # Create and run the task
                task.task = asyncio.create_task(self._execute_task(task))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error in worker loop", error=str(e))
    
    async def _execute_task(self, task: BackgroundTask):
        """Execute a background task."""
        try:
            logger.info("Starting task execution", task_id=task.task_id)
            
            # Execute the function
            if asyncio.iscoroutinefunction(task.func):
                result = await task.func(*task.args, **task.kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task.func, *task.args, **task.kwargs)
            
            # Task completed successfully
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.progress = 100.0
            
            logger.info("Task completed successfully", task_id=task.task_id)
            
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            logger.info("Task cancelled", task_id=task.task_id)
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            logger.error("Task failed", task_id=task.task_id, error=str(e))
        finally:
            task.completed_at = datetime.utcnow()
            self.running_tasks.discard(task.task_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get background task manager statistics."""
        status_counts = {}
        for task in self.tasks.values():
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(self.tasks),
            "running_tasks": len(self.running_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "status_counts": status_counts,
            "manager_running": self.running
        }
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """Clean up old completed/failed tasks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                task.completed_at and task.completed_at < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        if tasks_to_remove:
            logger.info("Cleaned up old tasks", count=len(tasks_to_remove))

# Global background task manager instance
background_task_manager = BackgroundTaskManager()

# Utility functions for common background tasks
async def send_email_async(to_email: str, subject: str, body: str):
    """Send email asynchronously."""
    # Simulate email sending
    await asyncio.sleep(2)
    logger.info("Email sent", to=to_email, subject=subject)
    return {"status": "sent", "to": to_email}

async def process_document_async(document_id: int, operation: str):
    """Process document asynchronously."""
    # Simulate document processing
    await asyncio.sleep(5)
    logger.info("Document processed", document_id=document_id, operation=operation)
    return {"status": "processed", "document_id": document_id, "operation": operation}

async def generate_report_async(report_type: str, filters: dict):
    """Generate report asynchronously."""
    # Simulate report generation
    await asyncio.sleep(10)
    logger.info("Report generated", report_type=report_type, filters=filters)
    return {"status": "generated", "report_type": report_type, "filters": filters}

# Decorator for background task execution
def background_task(task_id_prefix: str = ""):
    """Decorator to run a function as a background task."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            task_id = f"{task_id_prefix}:{func.__name__}:{int(time.time())}"
            return await background_task_manager.submit_task(task_id, func, args, kwargs)
        return wrapper
    return decorator 