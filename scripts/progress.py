import queue
import threading

_listeners = {}
_lock = threading.Lock()


def _get_queue(job_id):
    with _lock:
        if job_id not in _listeners:
            _listeners[job_id] = queue.Queue()
        return _listeners[job_id]


def emit(job_id, step, status="in_progress"):
    """Emit a progress event for a job. status: in_progress | completed | error"""
    q = _get_queue(job_id)
    q.put({"step": step, "status": status})


def listen(job_id):
    """Yield progress events for a job. Blocks until next event."""
    q = _get_queue(job_id)
    while True:
        event = q.get()
        yield event
        if event["status"] in ("completed", "error"):
            break
    # Cleanup
    with _lock:
        _listeners.pop(job_id, None)
