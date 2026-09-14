"""Named workload profiles for performance tests.

These placeholders keep future profile names stable while the active dashboard
still sends users, spawn_rate, duration, host, and mode directly.
"""

SMOKE_PROFILE = {
    "users": 1,
    "spawn_rate": 1,
    "duration": "20s",
}

BASELINE_PROFILE = {
    "users": 50,
    "spawn_rate": 5,
    "duration": "5m",
}

STRESS_PROFILE = {
    "users": 500,
    "spawn_rate": 10,
    "duration": "5m",
}
