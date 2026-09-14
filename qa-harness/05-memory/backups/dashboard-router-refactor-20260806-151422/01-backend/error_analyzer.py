"""
Smart Error Analyzer — classifies, groups, and estimates fix effort for test failures.

This module provides:
  1. Error categorization (what type of failure is it?)
  2. Error grouping (which failures share the same root cause?)
  3. Fix complexity estimation (how hard is this to fix?)
  4. Suggested fix actions (what should the tester do first?)

Categories:
  - SelectorChanged : Element/locator not found → UI changed, update selectors
  - Timeout         : Wait timeout exceeded → Env issue or need better waits
  - AssertionFailed : Expected vs actual mismatch → Logic or data changed
  - NetworkError    : Connection/fetch failures → Backend or infra issue
  - StepNotDefined  : Behave step not implemented → Incomplete test code
  - PageNavigation  : Page failed to load / wrong URL → App routing changed
  - Authentication  : Login/session/token errors → Credential or auth flow changed
  - DataError       : Data setup / database errors → Test data or API issue
  - Other           : Uncategorized
"""

import re
from collections import Counter, defaultdict
from typing import Optional


# ---------------------------------------------------------------------------
# Error category definitions with detection patterns
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        "id": "SelectorChanged",
        "label": "Selector / Element Not Found",
        "icon": "aim",
        "color": "#722ed1",
        "patterns": [
            r"locator.*resolved to 0 elements",
            r"element.*not found",
            r"no element.*match",
            r"waiting for locator",
            r"locator.*not visible",
            r"selector.*not found",
            r"could not find element",
            r"ElementNotFound",
            r"NoSuchElement",
            r"element is not attached",
            r"stale element",
        ],
        "complexity": "Medium",
        "est_time_min": 15,
        "est_time_max": 30,
        "suggestion": "The UI selector has likely changed. Inspect the page and update the locator in your step definition or page object.",
    },
    {
        "id": "Timeout",
        "label": "Timeout / Wait Exceeded",
        "icon": "clock-circle",
        "color": "#fa8c16",
        "patterns": [
            r"timeout.*exceeded",
            r"timed?\s*out",
            r"waiting for.*selector",
            r"TimeoutError",
            r"page\.wait_for",
            r"wait_for_selector",
            r"navigation timeout",
        ],
        "complexity": "Low",
        "est_time_min": 5,
        "est_time_max": 15,
        "suggestion": "Usually an environment or performance issue. Try increasing the wait timeout, or check if the target environment is healthy.",
    },
    {
        "id": "AssertionFailed",
        "label": "Assertion Failed",
        "icon": "close-circle",
        "color": "#f5222d",
        "patterns": [
            r"AssertionError",
            r"assert.*==",
            r"expected.*but got",
            r"does not match",
            r"not equal",
            r"should be.*but was",
            r"mismatch",
            r"assert.*in\b",
            r"assert.*True",
            r"assert.*False",
        ],
        "complexity": "High",
        "est_time_min": 30,
        "est_time_max": 60,
        "suggestion": "The application behavior or data has changed. Verify whether this is a product bug or an expected change that requires test update.",
    },
    {
        "id": "NetworkError",
        "label": "Network / Connection Error",
        "icon": "disconnect",
        "color": "#13c2c2",
        "patterns": [
            r"ERR_CONNECTION",
            r"net::ERR",
            r"fetch failed",
            r"ConnectionError",
            r"ConnectionRefused",
            r"ECONNREFUSED",
            r"socket hang up",
            r"request failed",
            r"status.*(4\d\d|5\d\d)",
        ],
        "complexity": "Low",
        "est_time_min": 5,
        "est_time_max": 10,
        "suggestion": "Likely an environment issue. Check if the target service is running and accessible. May resolve on retry.",
    },
    {
        "id": "StepNotDefined",
        "label": "Step Not Defined",
        "icon": "question-circle",
        "color": "#1890ff",
        "patterns": [
            r"not defined",
            r"undefined step",
            r"no step definition",
            r"step.*undefined",
            r"You can implement",
        ],
        "complexity": "Low",
        "est_time_min": 10,
        "est_time_max": 20,
        "suggestion": "A step definition is missing. Implement the step in your steps/ directory.",
    },
    {
        "id": "PageNavigation",
        "label": "Page Navigation Error",
        "icon": "global",
        "color": "#eb2f96",
        "patterns": [
            r"page\.goto",
            r"navigation.*failed",
            r"ERR_NAME_NOT_RESOLVED",
            r"ERR_ABORTED",
            r"page crashed",
            r"target.*closed",
            r"browser.*disconnected",
            r"context.*closed",
        ],
        "complexity": "Medium",
        "est_time_min": 15,
        "est_time_max": 30,
        "suggestion": "The page failed to load. Check if the URL is correct and the application is deployed in the target environment.",
    },
    {
        "id": "Authentication",
        "label": "Authentication / Session Error",
        "icon": "lock",
        "color": "#faad14",
        "patterns": [
            r"401",
            r"403",
            r"unauthorized",
            r"forbidden",
            r"login.*fail",
            r"token.*expired",
            r"session.*invalid",
            r"authentication.*failed",
        ],
        "complexity": "Medium",
        "est_time_min": 10,
        "est_time_max": 25,
        "suggestion": "Authentication failed. Check if test credentials are valid and the auth flow hasn't changed.",
    },
    {
        "id": "DataError",
        "label": "Data / Setup Error",
        "icon": "database",
        "color": "#52c41a",
        "patterns": [
            r"IntegrityError",
            r"duplicate key",
            r"not null constraint",
            r"data.*not found",
            r"record.*not found",
            r"setup.*failed",
            r"fixture.*error",
        ],
        "complexity": "Medium",
        "est_time_min": 15,
        "est_time_max": 30,
        "suggestion": "Test data setup failed. Check if prerequisite data exists and API responses match expectations.",
    },
]


def categorize_error(error_msg: str) -> dict:
    """Classify an error message into a category.

    Returns a dict with category info including id, label, complexity, etc.
    """
    if not error_msg:
        return _other_category()

    for cat in CATEGORIES:
        for pattern in cat["patterns"]:
            if re.search(pattern, error_msg, re.IGNORECASE | re.DOTALL):
                return {
                    "id": cat["id"],
                    "label": cat["label"],
                    "icon": cat["icon"],
                    "color": cat["color"],
                    "complexity": cat["complexity"],
                    "est_time_min": cat["est_time_min"],
                    "est_time_max": cat["est_time_max"],
                    "suggestion": cat["suggestion"],
                }

    return _other_category()


def _other_category():
    return {
        "id": "Other",
        "label": "Other / Uncategorized",
        "icon": "exclamation-circle",
        "color": "#8c8c8c",
        "complexity": "High",
        "est_time_min": 30,
        "est_time_max": 60,
        "suggestion": "Review the full error message and stack trace to determine the root cause.",
    }


def extract_error_fingerprint(error_msg: str) -> str:
    """Extract a short 'fingerprint' from an error message for grouping.

    The fingerprint strips variable parts (numbers, timestamps, UUIDs) so that
    errors with the same root cause produce the same fingerprint.
    """
    if not error_msg:
        return "empty"

    # Take the first meaningful line
    first_line = error_msg.strip().split("\n")[0].strip()

    # Remove variable parts
    fp = re.sub(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*", "<TS>", first_line)
    fp = re.sub(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", "<UUID>", fp)
    fp = re.sub(r"\b\d{5,}\b", "<ID>", fp)  # long numbers (IDs)
    fp = re.sub(r":\d+:\d+", ":<L>:<C>", fp)  # line:col in stack traces
    fp = re.sub(r"\s+", " ", fp).strip()

    return fp[:200]  # cap length


def analyze_run_errors(scenarios: list[dict]) -> dict:
    """Full error analysis for a set of scenario results.

    Args:
        scenarios: list of dicts with keys: id, feature, name, status, duration_s, error_msg, tags

    Returns:
        A comprehensive analysis dict.
    """
    failed = [s for s in scenarios if s.get("status") == "failed" and s.get("error_msg")]

    if not failed:
        return {
            "total_errors": 0,
            "categories": [],
            "groups": [],
            "blast_radius": [],
            "summary": {
                "total_failed": 0,
                "unique_root_causes": 0,
                "est_total_fix_min": 0,
                "est_total_fix_max": 0,
                "dominant_category": None,
            },
        }

    # --- Categorize each error ---
    categorized = []
    for s in failed:
        cat = categorize_error(s["error_msg"])
        fp = extract_error_fingerprint(s["error_msg"])
        categorized.append({
            **s,
            "category": cat,
            "fingerprint": fp,
        })

    # --- Group by category ---
    by_category = defaultdict(list)
    for item in categorized:
        by_category[item["category"]["id"]].append(item)

    categories = []
    total_min = 0
    total_max = 0

    for cat_id, items in by_category.items():
        cat_info = items[0]["category"]
        # When multiple tests fail with same root cause, fix time doesn't scale linearly
        unique_fps = len(set(i["fingerprint"] for i in items))
        fix_min = cat_info["est_time_min"] * unique_fps
        fix_max = cat_info["est_time_max"] * unique_fps
        total_min += fix_min
        total_max += fix_max

        categories.append({
            "id": cat_id,
            "label": cat_info["label"],
            "icon": cat_info["icon"],
            "color": cat_info["color"],
            "count": len(items),
            "complexity": cat_info["complexity"],
            "est_fix_time": f"{fix_min}-{fix_max} min",
            "suggestion": cat_info["suggestion"],
            "unique_patterns": unique_fps,
            "errors": [
                {
                    "scenario_id": i.get("id"),
                    "feature": i["feature"],
                    "scenario": i["name"],
                    "error_preview": _truncate(i["error_msg"], 200),
                    "fingerprint": i["fingerprint"],
                    "duration_s": i.get("duration_s", 0),
                }
                for i in items
            ],
        })

    categories.sort(key=lambda c: c["count"], reverse=True)

    # --- Group by fingerprint (root cause deduplication) ---
    by_fingerprint = defaultdict(list)
    for item in categorized:
        by_fingerprint[item["fingerprint"]].append(item)

    groups = []
    for fp, items in sorted(by_fingerprint.items(), key=lambda x: -len(x[1])):
        groups.append({
            "fingerprint": fp,
            "count": len(items),
            "category": items[0]["category"]["id"],
            "scenarios": [
                {"id": i.get("id"), "feature": i["feature"], "name": i["name"]}
                for i in items
            ],
        })

    # --- Blast radius: which features are affected? ---
    feature_errors = Counter(i["feature"] for i in categorized)
    blast_radius = [
        {"feature": f, "error_count": c}
        for f, c in feature_errors.most_common()
    ]

    dominant = categories[0] if categories else None

    return {
        "total_errors": len(failed),
        "categories": categories,
        "groups": groups,
        "blast_radius": blast_radius,
        "summary": {
            "total_failed": len(failed),
            "unique_root_causes": len(groups),
            "est_total_fix_min": total_min,
            "est_total_fix_max": total_max,
            "dominant_category": dominant["label"] if dominant else None,
            "dominant_count": dominant["count"] if dominant else 0,
        },
    }


def detect_flaky_tests(run_history: list[dict]) -> list[dict]:
    """Detect flaky tests by analyzing status flips across runs.

    Args:
        run_history: list of dicts, each containing 'run_id' and 'scenarios'
                     (list of {name, feature, status}).

    Returns:
        list of flaky test dicts sorted by flakiness rate (worst first).
    """
    # Track (feature, name) → list of statuses across runs
    test_history: dict[tuple, list[str]] = defaultdict(list)

    for run in run_history:
        for s in run.get("scenarios", []):
            key = (s["feature"], s["name"])
            test_history[key].append(s["status"])

    flaky_tests = []
    for (feature, name), statuses in test_history.items():
        if len(statuses) < 2:
            continue

        # Count status flips (pass→fail or fail→pass)
        flips = 0
        for i in range(1, len(statuses)):
            if statuses[i] != statuses[i - 1] and "skipped" not in (statuses[i], statuses[i - 1]):
                flips += 1

        if flips == 0:
            continue

        total_runs = len(statuses)
        pass_count = statuses.count("passed")
        fail_count = statuses.count("failed")
        flakiness_rate = round((flips / (total_runs - 1)) * 100, 1) if total_runs > 1 else 0

        flaky_tests.append({
            "feature": feature,
            "name": name,
            "total_runs": total_runs,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "flips": flips,
            "flakiness_rate": flakiness_rate,
            "last_status": statuses[-1] if statuses else "unknown",
            "history": statuses[-10:],  # last 10 statuses
        })

    flaky_tests.sort(key=lambda t: t["flakiness_rate"], reverse=True)
    return flaky_tests


def _truncate(s: str, max_len: int) -> str:
    if not s:
        return ""
    s = s.strip()
    if len(s) <= max_len:
        return s
    return s[:max_len] + "..."
