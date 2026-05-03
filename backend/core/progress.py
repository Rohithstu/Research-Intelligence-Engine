"""
Progress Tracker for Real-time Search Updates
"""

from typing import Dict, Any, Callable, Awaitable
import asyncio

class ProgressTracker:
    def __init__(self, on_update: Callable[[Dict[str, Any]], Awaitable[None]] = None):
        self.on_update = on_update
        self.current_state = "idle"

    async def update(self, state: str, message: str, detail: Any = None):
        self.current_state = state
        if self.on_update:
            await self.on_update({
                "state": state,
                "message": message,
                "detail": detail
            })

# Global tracker for simplicity in this prototype
# In a production app, this would be per-request
_tracker = ProgressTracker()

def get_tracker():
    return _tracker
