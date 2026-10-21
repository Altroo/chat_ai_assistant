"""Verify captured systemd execution identity across status-rendering changes.

Callers must obtain both records from trusted host queries. A verified result
does not establish model accuracy or authorize another process.
"""
from datetime import datetime, timedelta, timezone
import re

UNIT_FIELDS = frozenset((
    "MainPID", "SubState", "Result", "ExecMainStatus", "InvocationID", "ExecStart",
    "CPUQuotaPerSecUSec", "MemoryMax", "MemorySwapMax", "KillMode", "User",
    "RuntimeMaxUSec",
))
EXECUTION_FIELDS = frozenset((
    "InvocationID", "ExecMainPID", "ExecMainCode", "ExecMainStatus", "NRestarts",
    "ExecMainStartTimestamp", "ExecMainExitTimestamp",
    "ExecMainStartTimestampMonotonic", "ExecMainExitTimestampMonotonic",
))
COMMAND = re.compile(
    r"\{ path=(?P<path>[^\s;]+) ; argv\[\]=(?P<argv>[^;]+) ; "
    r"ignore_errors=(?P<ignore>no) ; start_time=\[(?P<start>[^\]]+)\] ; "
    r"stop_time=\[(?P<stop>[^\]]+)\] ; pid=(?P<pid>[0-9]+) ; "
    r"code=(?P<code>exited|\(null\)) ; status=(?P<status>0|0/0) \}"
)
ZONES = {"UTC": 0, "CET": 1, "CEST": 2}
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def fields(value, required):
    if (not isinstance(value, dict) or set(value) != required
            or any(not isinstance(v, str) for v in value.values())):
        raise ValueError("Missing, unexpected or invalid execution fields")


def timestamp(value):
    match = re.fullmatch(
        r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (UTC|CET|CEST)",
        value,
    )
    if match is None:
        raise ValueError("Unrecognized execution timestamp")
    day, text, zone = match.groups()
    parsed = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
    if WEEKDAYS[parsed.weekday()] != day:
        raise ValueError("Inconsistent timestamp weekday")
    return parsed.replace(tzinfo=timezone(timedelta(hours=ZONES[zone]))).astimezone(timezone.utc)


def command(value):
    match = COMMAND.fullmatch(value)
    if match is None:
        raise ValueError("Malformed or multiple configured commands")
    result = match.groupdict()
    if not result["path"].startswith("/") or not (
            result["argv"] == result["path"] or result["argv"].startswith(result["path"] + " ")):
        raise ValueError("Configured executable and argv disagree")
    return result


def positive(value):
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise ValueError("Invalid execution identity number")
    return int(value)


def verify_terminal_execution(recorded, current, execution):
    """Require stable configuration and the actual original successful execution."""
    fields(recorded, UNIT_FIELDS)
    fields(current, UNIT_FIELDS)
    fields(execution, EXECUTION_FIELDS)
    if any(current[k] != v for k, v in recorded.items() if k != "ExecStart"):
        raise ValueError("Terminal unit identity, configuration or result changed")
    if any(recorded[k] != v for k, v in {
            "MainPID": "0", "SubState": "exited", "Result": "success",
            "ExecMainStatus": "0"}.items()):
        raise ValueError("Original unit did not complete successfully")
    if not re.fullmatch(r"[0-9a-f]{32}", recorded["InvocationID"]):
        raise ValueError("Invalid invocation identity")
    original, now = command(recorded["ExecStart"]), command(current["ExecStart"])
    if any(now[k] != original[k] for k in ("path", "argv", "ignore")):
        raise ValueError("Configured command changed")
    pid = positive(original["pid"])
    if original["code"] != "exited" or original["status"] != "0":
        raise ValueError("Original command execution was not captured successfully")
    start, end = timestamp(original["start"]), timestamp(original["stop"])
    if end <= start:
        raise ValueError("Invalid original execution interval")
    if any(execution[k] != v for k, v in {
            "InvocationID": recorded["InvocationID"], "ExecMainPID": str(pid),
            "ExecMainCode": "1", "ExecMainStatus": "0", "NRestarts": "0"}.items()):
        raise ValueError("Actual main execution identity or result changed")
    if (timestamp(execution["ExecMainStartTimestamp"]) != start
            or timestamp(execution["ExecMainExitTimestamp"]) != end):
        raise ValueError("Actual execution timestamps differ from the captured run")
    mono_start = positive(execution["ExecMainStartTimestampMonotonic"])
    mono_end = positive(execution["ExecMainExitTimestampMonotonic"])
    if mono_end <= mono_start or abs(
            (mono_end - mono_start) / 1_000_000 - (end - start).total_seconds()) > 2:
        raise ValueError("Inconsistent monotonic execution interval")
    cleared = {k: now[k] for k in ("start", "stop", "pid", "code", "status")} == {
        "start": "n/a", "stop": "n/a", "pid": "0", "code": "(null)", "status": "0/0"}
    if not cleared and (
            positive(now["pid"]) != pid or now["code"] != "exited" or now["status"] != "0"
            or timestamp(now["start"]) != start or timestamp(now["stop"]) != end):
        raise ValueError("Current execution presentation contradicts the original run")
    return {
        "verified": True, "invocation_id": recorded["InvocationID"],
        "original_controller_pid": pid, "execution_start_utc": start.isoformat(),
        "execution_exit_utc": end.isoformat(), "restarts": 0,
        "execstart_presentation_cleared": cleared,
    }
