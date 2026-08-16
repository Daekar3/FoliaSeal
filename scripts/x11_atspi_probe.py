#!/usr/bin/env python3
"""Read-only AT-SPI inspection for one owned X11 audit process/window."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from collections import deque
from typing import Any


def _state_names(accessible: Any, pyatspi: Any) -> list[str]:
    try:
        state = accessible.getState()
    except Exception:
        return []
    names = {
        "visible": pyatspi.STATE_VISIBLE,
        "showing": pyatspi.STATE_SHOWING,
        "focused": pyatspi.STATE_FOCUSED,
        "enabled": pyatspi.STATE_ENABLED,
    }
    return [name for name, value in names.items() if state.contains(value)]


def _actions(accessible: Any) -> list[str]:
    try:
        action = accessible.queryAction()
        count = int(action.get_n_actions())
        return [
            str(action.get_action_name(index))
            for index in range(min(count, 32))
            if action.get_action_name(index)
        ]
    except Exception:
        return []


def _extents(accessible: Any, pyatspi: Any) -> dict[str, int] | None:
    try:
        rect = accessible.queryComponent().get_extents(pyatspi.DESKTOP_COORDS)
        return {
            "x": int(rect.x),
            "y": int(rect.y),
            "width": int(rect.width),
            "height": int(rect.height),
        }
    except Exception:
        return None


def _children(accessible: Any, pyatspi: Any, limit: int = 256) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    queue: deque[Any] = deque([accessible])
    while queue and len(result) < limit:
        current = queue.popleft()
        try:
            child_count = int(current.childCount)
        except Exception:
            continue
        for index in range(child_count):
            if len(result) >= limit:
                break
            try:
                child = current.getChildAtIndex(index)
                item = {
                    "name": str(child.name or ""),
                    "role": str(child.getRoleName()),
                    "states": _state_names(child, pyatspi),
                    "actions": _actions(child),
                    "extents": _extents(child, pyatspi),
                }
                result.append(item)
                queue.append(child)
            except Exception:
                continue
    return result


def _find_frame(application: Any, title: str, pyatspi: Any) -> Any | None:
    queue: deque[Any] = deque([application])
    seen: set[int] = set()
    while queue:
        current = queue.popleft()
        identity = id(current)
        if identity in seen:
            continue
        seen.add(identity)
        try:
            if str(current.name or "") == title and str(current.getRoleName()) == "frame":
                return current
            child_count = int(current.childCount)
        except Exception:
            continue
        for index in range(child_count):
            try:
                queue.append(current.getChildAtIndex(index))
            except Exception:
                continue
    return None


def inspect(pid: int, title: str, timeout_seconds: float) -> dict[str, Any]:
    try:
        bus = subprocess.run(
            ["busctl", "--user", "list"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "unavailable",
            "reason": f"accessibility bus: {type(exc).__name__}: {exc}",
        }
    if "org.a11y.atspi.Registry" not in bus.stdout:
        return {
            "status": "unavailable",
            "reason": "AT-SPI registry service is not present on the session bus",
            "process_id": pid,
            "title": title,
        }
    try:
        import pyatspi
    except Exception as exc:
        return {"status": "unavailable", "reason": f"import: {type(exc).__name__}: {exc}"}

    deadline = time.monotonic() + timeout_seconds
    try:
        desktop = pyatspi.Registry.getDesktop(0)
    except Exception as exc:
        return {"status": "unavailable", "reason": f"registry: {type(exc).__name__}: {exc}"}

    while time.monotonic() < deadline:
        try:
            for index in range(int(desktop.childCount)):
                application = desktop.getChildAtIndex(index)
                try:
                    if int(application.get_process_id()) != pid:
                        continue
                except Exception:
                    continue
                frame = _find_frame(application, title, pyatspi)
                if frame is None:
                    continue
                return {
                    "status": "available",
                    "process_id": pid,
                    "application_name": str(application.name or ""),
                    "frame": {
                        "name": str(frame.name or ""),
                        "role": str(frame.getRoleName()),
                        "states": _state_names(frame, pyatspi),
                        "actions": _actions(frame),
                        "extents": _extents(frame, pyatspi),
                    },
                    "children": _children(frame, pyatspi),
                }
        except Exception:
            pass
        time.sleep(0.05)
    return {
        "status": "unavailable",
        "reason": "owned AT-SPI application/frame was not discoverable before deadline",
        "process_id": pid,
        "title": title,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    args = parser.parse_args()
    print(json.dumps(inspect(args.pid, args.title, args.timeout_seconds), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
