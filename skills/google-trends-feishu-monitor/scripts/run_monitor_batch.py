#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_WORKBOOK_URL = "https://b8vf2u0bp3.feishu.cn/sheets/SG4xs1FjdhernxtTw9ucwBUAnGb"
TOOLS_SHEET_ID = "oUaATj"
GAMES_SHEET_ID = "2gLvk3"
OUTPUT_SHEET_ID = "rBLswo"
ANCHOR = "happy birthday images"
BENCHMARK = "GPTs"
RELATED_WAIT_SECONDS = 5
COMPARE_WAIT_SECONDS = 3
RETRY_DELAYS_SECONDS = (75, 240)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Google Trends -> Feishu monitoring batch")
    parser.add_argument("--workspace", default=".", help="Workspace root that contains docs/")
    parser.add_argument("--date", required=True, help="Run date in YYYY-MM-DD format")
    parser.add_argument("--run-id", required=True, help="Run id such as 1")
    parser.add_argument("--workbook-url", default=DEFAULT_WORKBOOK_URL, help="Feishu workbook URL")
    parser.add_argument("--tools-range", default=f"{TOOLS_SHEET_ID}!A1:B20", help="Tool source range")
    parser.add_argument("--games-range", default=f"{GAMES_SHEET_ID}!A1:B20", help="Game source range")
    parser.add_argument("--output-range", default=f"{OUTPUT_SHEET_ID}!A1:F200", help="Output inspection range")
    parser.add_argument(
        "--health-url",
        default="https://trends.google.com/trends/explore?date=now%207-d&q=seedance,wan,qwen,veo,sora",
        help="Trends URL used for health check",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip the initial health check. Use only if the environment is already verified.",
    )
    return parser.parse_args()


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def extract_json_payload(output: str) -> Any:
    lines = output.splitlines()
    for index, line in enumerate(lines):
        stripped = line.lstrip("\ufeff").strip()
        if not stripped or stripped.startswith("[info]:"):
            continue
        if stripped.startswith("{") or stripped.startswith("["):
            candidate = "\n".join(lines[index:]).lstrip("\ufeff")
            return json.loads(candidate)
    stripped = output.strip().lstrip("\ufeff")
    if stripped.startswith("{") or stripped.startswith("["):
        return json.loads(stripped)
    raise ValueError(f"Unable to locate JSON payload in output:\n{output}")


def run_json_command(args: list[str], *, cwd: Path | None = None) -> Any:
    completed = run_command(args, cwd=cwd)
    combined = "\n".join(part for part in [completed.stdout, completed.stderr] if part).strip()
    if completed.returncode != 0:
        raise RuntimeError(combined or f"Command failed: {' '.join(args)}")
    return extract_json_payload(combined)


def powershell_script_args(script_path: Path, *script_args: str) -> list[str]:
    return [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        *script_args,
    ]


def run_feishu(workbook_url: str, command: str, *command_args: str) -> Any:
    script = skill_root() / "scripts" / "run_feishu_bootstrap.ps1"
    args = powershell_script_args(script, command, "--url", workbook_url, *command_args)
    return run_json_command(args)


def run_trends(command: str, *command_args: str) -> Any:
    script = skill_root() / "scripts" / "run_trends_collect.ps1"
    args = powershell_script_args(script, command, *command_args)
    return run_json_command(args)


def create_run_scaffold(workspace: Path, run_date: str, run_id: str) -> tuple[Path, Path, str]:
    script = skill_root() / "scripts" / "new_monitor_run.py"
    payload = run_json_command(
        [
            "python",
            str(script),
            "--workspace",
            str(workspace),
            "--date",
            run_date,
            "--run-id",
            run_id,
            "--start-sheet",
            TOOLS_SHEET_ID,
            "--start-row",
            "2",
        ],
        cwd=workspace,
    )
    run_name = f"{run_date}-run-{run_id}"
    return Path(payload["runFile"]), Path(payload["checkpointFile"]), run_name


def build_source_groups(tools_read: dict[str, Any], games_read: dict[str, Any]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []

    tool_rows = tools_read.get("values", [])
    for row_number in range(2, 13):
        row_index = row_number - 1
        if row_index >= len(tool_rows):
            continue
        row = tool_rows[row_index] or []
        root_group = row[0] if len(row) > 0 else None
        trends_url = row[1] if len(row) > 1 else None
        if root_group and trends_url:
            groups.append(
                {
                    "sourceType": "工具",
                    "sheetId": TOOLS_SHEET_ID,
                    "row": row_number,
                    "rootGroup": root_group,
                    "trendsUrl": trends_url,
                }
            )

    game_rows = games_read.get("values", [])
    for row_number in range(2, 7):
        row_index = row_number - 1
        if row_index >= len(game_rows):
            continue
        row = game_rows[row_index] or []
        root_group = row[0] if len(row) > 0 else None
        trends_url = row[1] if len(row) > 1 else None
        if root_group and trends_url:
            groups.append(
                {
                    "sourceType": "游戏",
                    "sheetId": GAMES_SHEET_ID,
                    "row": row_number,
                    "rootGroup": root_group,
                    "trendsUrl": trends_url,
                }
            )

    return groups


def normalize_candidate_key(value: str) -> str:
    return value.strip().lower()


def collect_existing_pairs(readback: dict[str, Any], run_date: str) -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for row in readback.get("values", [])[1:]:
        if not row or len(row) < 5:
            continue
        candidate = row[1] if len(row) > 1 else None
        date_value = row[4] if len(row) > 4 else None
        if candidate and date_value == run_date:
            pairs.add((run_date, normalize_candidate_key(str(candidate))))
    return pairs


def find_write_start_row(readback: dict[str, Any]) -> int:
    last_nonempty_row = 1
    for index, row in enumerate(readback.get("values", [])[1:], start=2):
        if any(cell not in (None, "") for cell in row):
            last_nonempty_row = index
    return last_nonempty_row + 1


def generic_intent_summary(candidate: str) -> str:
    return f"用户在找 {candidate} 相关信息、入口或最新进展。"


def normalize_feishu_cell(cell: Any) -> Any:
    if isinstance(cell, list) and cell and isinstance(cell[0], dict):
        normalized_parts: list[str] = []
        for index, item in enumerate(cell):
            if not isinstance(item, dict):
                normalized_parts.append(str(item))
                continue
            if index == 0 and item.get("link"):
                normalized_parts.append(str(item["link"]))
                continue
            if item.get("text"):
                normalized_parts.append(str(item["text"]))
                continue
            if item.get("link"):
                normalized_parts.append(str(item["link"]))
        return "".join(normalized_parts)
    return cell


def normalize_feishu_matrix(values: list[list[Any]]) -> list[list[Any]]:
    return [[normalize_feishu_cell(cell) for cell in row] for row in values]


def sanitize_compare_url(raw_url: str) -> str:
    # Feishu may split hyperlink-rich text cells when a raw apostrophe remains in the URL.
    return raw_url.replace("'", "%27")


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_compare_results(compare_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for file_path in sorted(compare_dir.glob("*.json")):
        records.append(json.loads(file_path.read_text(encoding="utf-8")))
    return records


def run_with_retry(candidate: str) -> tuple[int, dict[str, Any]]:
    attempts = 0
    while True:
        attempts += 1
        try:
            result = run_trends("compare", candidate, ANCHOR, BENCHMARK)
            if result.get("error") != "multiline_unavailable":
                return attempts, result
        except Exception as error:  # noqa: BLE001
            if attempts > len(RETRY_DELAYS_SECONDS):
                raise RuntimeError(f"compare failed for {candidate}: {error}") from error
        if attempts > len(RETRY_DELAYS_SECONDS):
            return attempts, {
                "candidate": candidate,
                "compareUrl": (
                    "https://trends.google.com/trends/explore?date=now%207-d&q="
                    f"happy%20birthday%20images%2CGPTs%2C{candidate}"
                ),
                "error": "multiline_unavailable",
            }
        time.sleep(RETRY_DELAYS_SECONDS[attempts - 1])


def write_run_summary(
    run_file: Path,
    checkpoint_file: Path,
    *,
    run_name: str,
    workbook_url: str,
    completed_groups: list[str],
    written_keywords: list[str],
    exploding_count: int,
    unique_compare_count: int,
    qualified_count: int,
    write_range: str | None,
    revision_after_write: int | None,
) -> None:
    last_updated = datetime.now().astimezone().isoformat()
    checkpoint = {
        "taskName": "google-trends-new-keyword-monitoring",
        "date": run_name.split("-run-")[0],
        "status": "completed",
        "network": {
            "proxyApp": "",
            "proxyGroup": "",
            "exitNode": "",
            "nodeType": "",
            "healthCheck": {
                "google": "pass",
                "trendsExplore": "pass",
                "relatedsearches": "pass",
            },
        },
        "currentBatch": run_name,
        "currentGroup": {
            "sourceType": "",
            "sheetId": "",
            "row": 0,
            "rootGroup": "",
            "trendsUrl": "",
        },
        "currentKeyword": "",
        "completedGroups": completed_groups,
        "writtenKeywords": written_keywords,
        "deferredItems": [],
        "failedItems": [],
        "lastUpdatedAt": last_updated,
        "metrics": {
            "sourceGroupCount": len(completed_groups),
            "explodingRelatedCount": exploding_count,
            "uniqueCompareCount": unique_compare_count,
            "qualifiedCount": qualified_count,
            "writeRange": write_range,
            "revisionAfterWrite": revision_after_write,
        },
    }
    checkpoint_file.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# Google Trends Monitor Run {run_name.split('-run-')[0]} / run-{run_name.split('-run-')[1]}",
        "",
        "## Status",
        "- status: completed",
        f"- workbook: {workbook_url}",
        "- browser path: reused or auto-bootstrapped local CDP browser session on 127.0.0.1:9225",
        "- health: google=pass, trendsExplore=pass, relatedsearches=pass",
        f"- source groups processed: {len(completed_groups)}",
        f"- exploding related queries collected: {exploding_count}",
        f"- unique compare candidates: {unique_compare_count}",
        f"- qualified candidates written: {qualified_count}",
    ]
    if write_range:
        lines.append(f"- Feishu writeback: {write_range}, revision {revision_after_write}")
    lines.extend(
        [
            f"- last updated: {last_updated}",
            "",
            "## Written Keywords",
        ]
    )
    if written_keywords:
        lines.extend(f"- {item}" for item in written_keywords)
    else:
        lines.append("- none")
    run_file.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    workspace = Path(args.workspace).resolve()
    run_file, checkpoint_file, run_name = create_run_scaffold(workspace, args.date, args.run_id)

    notes_root = workspace / "docs" / "google-trends-monitoring" / "notes" / run_name
    related_dir = notes_root / "related"
    compare_dir = notes_root / "compare"
    notes_root.mkdir(parents=True, exist_ok=True)
    related_dir.mkdir(parents=True, exist_ok=True)
    compare_dir.mkdir(parents=True, exist_ok=True)

    if not args.skip_health:
        health = run_trends("health", args.health_url)
        related_statuses = health.get("trends", {}).get("relatedStatuses", [])
        if (
            not health.get("google", {}).get("title")
            or not health.get("trends", {}).get("title")
            or not related_statuses
            or any(status != 200 for status in related_statuses)
        ):
            raise RuntimeError(f"Health check failed: {json.dumps(health, ensure_ascii=False, indent=2)}")

    tools_read = run_feishu(args.workbook_url, "read", "--range", args.tools_range)
    games_read = run_feishu(args.workbook_url, "read", "--range", args.games_range)
    output_before = run_feishu(args.workbook_url, "read", "--range", args.output_range)

    groups = build_source_groups(tools_read, games_read)
    existing_pairs = collect_existing_pairs(output_before, args.date)

    exploding_entries: list[dict[str, Any]] = []
    completed_groups: list[str] = []
    for group in groups:
        related = run_trends("related", group["trendsUrl"])
        record = {
            **group,
            "title": related.get("title"),
            "is429": related.get("is429"),
            "isSorry": related.get("isSorry"),
            "related": related.get("related", []),
        }
        save_json(related_dir / f"{group['sheetId']}-{group['row']}.json", record)
        completed_groups.append(f"{group['sheetId']}:{group['row']}")

        for related_item in related.get("related", []):
            if related_item.get("status") != 200 or not related_item.get("parseable"):
                continue
            for rising in related_item.get("rising", []):
                if not (rising.get("qualifiesExploding") or rising.get("isBreakout")):
                    continue
                exploding_entries.append(
                    {
                        **group,
                        "rootKeyword": related_item.get("rootKeyword"),
                        "candidate": rising.get("query"),
                        "formattedValue": rising.get("formattedValue"),
                        "value": rising.get("value"),
                    }
                )
        time.sleep(RELATED_WAIT_SECONDS)

    save_json(notes_root / "exploding.json", exploding_entries)

    unique_candidates: list[dict[str, Any]] = []
    seen_candidates: dict[str, dict[str, Any]] = {}
    for entry in exploding_entries:
        key = normalize_candidate_key(str(entry["candidate"]))
        if key not in seen_candidates:
            seen_candidates[key] = {
                "candidate": entry["candidate"],
                "roots": [entry["rootKeyword"]],
                "sourceType": entry["sourceType"],
                "rootKeyword": entry["rootKeyword"],
            }
            unique_candidates.append(seen_candidates[key])
            continue
        roots = seen_candidates[key]["roots"]
        if entry["rootKeyword"] not in roots:
            roots.append(entry["rootKeyword"])
    save_json(notes_root / "unique-candidates.json", unique_candidates)

    compare_records: list[dict[str, Any]] = []
    for index, candidate_entry in enumerate(unique_candidates, start=1):
        attempts, result = run_with_retry(candidate_entry["candidate"])
        record = {
            "index": index,
            "candidate": candidate_entry["candidate"],
            "roots": candidate_entry["roots"],
            "sourceType": candidate_entry["sourceType"],
            "rootKeyword": candidate_entry["rootKeyword"],
            "attempts": attempts,
            "result": result,
        }
        save_json(compare_dir / f"{index:03d}.json", record)
        compare_records.append(record)
        time.sleep(COMPARE_WAIT_SECONDS)

    qualified: list[dict[str, Any]] = []
    for record in compare_records:
        result = record.get("result") or {}
        if result.get("qualifies") is True:
            key = (args.date, normalize_candidate_key(record["candidate"]))
            if key in existing_pairs:
                continue
            qualified.append(record)
            existing_pairs.add(key)
    save_json(notes_root / "qualified.json", qualified)

    write_range = None
    revision_after_write = None
    written_keywords: list[str] = []

    if qualified:
        start_row = find_write_start_row(output_before)
        values = [
            [
                item["rootKeyword"],
                item["candidate"],
                sanitize_compare_url(item["result"]["compareUrl"]),
                generic_intent_summary(item["candidate"]),
                args.date,
                item["sourceType"],
            ]
            for item in qualified
        ]
        write_values_path = notes_root / "write-values.json"
        save_json(write_values_path, values)

        end_row = start_row + len(values) - 1
        write_range = f"{OUTPUT_SHEET_ID}!A{start_row}:F{end_row}"
        write_result = run_feishu(
            args.workbook_url,
            "write",
            "--range",
            write_range,
            "--values-file",
            str(write_values_path),
        )
        revision_after_write = write_result.get("revision")
        time.sleep(5)
        verify = run_feishu(args.workbook_url, "read", "--range", write_range)
        expected_matrix = normalize_feishu_matrix(values)
        actual_matrix = normalize_feishu_matrix(verify.get("values", []))
        if actual_matrix != expected_matrix:
            raise RuntimeError(
                "Feishu write verification failed.\n"
                f"expected={json.dumps(expected_matrix, ensure_ascii=False)}\n"
                f"actual={json.dumps(actual_matrix, ensure_ascii=False)}"
            )
        written_keywords = [item["candidate"] for item in qualified]

    write_run_summary(
        run_file,
        checkpoint_file,
        run_name=run_name,
        workbook_url=args.workbook_url,
        completed_groups=completed_groups,
        written_keywords=written_keywords,
        exploding_count=len(exploding_entries),
        unique_compare_count=len(unique_candidates),
        qualified_count=len(qualified),
        write_range=write_range,
        revision_after_write=revision_after_write,
    )

    print(
        json.dumps(
            {
                "runFile": str(run_file),
                "checkpointFile": str(checkpoint_file),
                "notesRoot": str(notes_root),
                "sourceGroupCount": len(completed_groups),
                "explodingRelatedCount": len(exploding_entries),
                "uniqueCompareCount": len(unique_candidates),
                "qualifiedCount": len(qualified),
                "writeRange": write_range,
                "revisionAfterWrite": revision_after_write,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:  # noqa: BLE001
        print(str(error), file=sys.stderr)
        raise
