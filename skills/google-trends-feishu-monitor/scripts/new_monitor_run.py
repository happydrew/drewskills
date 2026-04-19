#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_WORKBOOK_URL = "https://b8vf2u0bp3.feishu.cn/sheets/SG4xs1FjdhernxtTw9ucwBUAnGb"


def render_run_md(run_name: str, date: str, workbook_url: str, start_sheet: str, start_row: int) -> str:
    return f"""# Google Trends 运行记录

## 1. 任务元信息

- 任务名称: Google Trends 近期新词监控
- 执行日期: `{date}`
- 执行人: `Codex`
- 飞书主表: `{workbook_url}`
- SOP 文件: `docs/google-trends-keyword-monitoring-sop-2026-04-18.md`
- 任务说明文件: `docs/google-trends-monitoring-task-description-2026-04-18.md`
- 当前状态: `running`
- 当前批次: `{run_name}`
- 当前断点: `执行前健康检查`

## 2. 执行环境记录

- 代理软件:
- 当前代理组:
- 当前出口节点:
- 节点类型:
- 浏览器链路:
- Google 首页检查: `pending`
- Trends explore 检查: `pending`
- `relatedsearches` 检查: `pending`
- 备注:

## 3. 任务起点

- 起始工作表: `{start_sheet}`
- 起始行号: `{start_row}`

## 4. 失败与回补队列

| 类型 | 来源行 | 关键词 | 失败阶段 | 失败现象 | 已重试次数 | 下次重试时间 | 状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 5. 当日写入记录

| 日期 | 词根 | 暴涨词 | 分析链接 | 类型 | 写入状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
"""


def render_checkpoint(run_name: str, date: str, start_sheet: str, start_row: int) -> dict:
    return {
        "taskName": "google-trends-new-keyword-monitoring",
        "date": date,
        "status": "running",
        "network": {
            "proxyApp": "",
            "proxyGroup": "",
            "exitNode": "",
            "nodeType": "",
            "healthCheck": {
                "google": "pending",
                "trendsExplore": "pending",
                "relatedsearches": "pending",
            },
        },
        "currentBatch": run_name,
        "currentGroup": {
            "sourceType": "",
            "sheetId": start_sheet,
            "row": start_row,
            "rootGroup": "",
            "trendsUrl": "",
        },
        "currentKeyword": "",
        "completedGroups": [],
        "writtenKeywords": [],
        "deferredItems": [],
        "failedItems": [],
        "lastUpdatedAt": "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a new Google Trends monitoring run scaffold")
    parser.add_argument("--workspace", default=".", help="Workspace root that contains docs/")
    parser.add_argument("--date", required=True, help="Run date in YYYY-MM-DD format")
    parser.add_argument("--run-id", required=True, help="Run id such as 1 or 2")
    parser.add_argument("--start-sheet", default="oUaATj", help="Start sheet id")
    parser.add_argument("--start-row", type=int, default=2, help="Start row number")
    parser.add_argument("--workbook-url", default=DEFAULT_WORKBOOK_URL, help="Feishu workbook url")
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    runs_dir = workspace / "docs" / "google-trends-monitoring" / "runs"
    checkpoints_dir = workspace / "docs" / "google-trends-monitoring" / "checkpoints"
    runs_dir.mkdir(parents=True, exist_ok=True)
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    run_name = f"{args.date}-run-{args.run_id}"
    run_file = runs_dir / f"{run_name}.md"
    checkpoint_file = checkpoints_dir / f"{run_name}.json"

    run_file.write_text(
        render_run_md(run_name, args.date, args.workbook_url, args.start_sheet, args.start_row),
        encoding="utf-8",
    )
    checkpoint_file.write_text(
        json.dumps(render_checkpoint(run_name, args.date, args.start_sheet, args.start_row), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps({
        "runFile": str(run_file),
        "checkpointFile": str(checkpoint_file),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
