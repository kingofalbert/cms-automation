#!/usr/bin/env python3
"""
Pipeline 監控 API 服務器（支持新的分階段 Pipeline）

提供 RESTful API 讓前端可以查詢 Pipeline 狀態

啟動方式：
    python scripts/pipeline_monitor_api.py

API 端點：
    GET /api/pipeline/status - 獲取 Pipeline 狀態
    GET /api/pipeline/logs - 獲取最新日誌
    GET /api/pipeline/local-stats - 獲取本地抓取進度
    POST /api/pipeline/start - 啟動 Pipeline
    POST /api/pipeline/stop - 停止 Pipeline
"""

import os
import subprocess
import glob
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

app = Flask(__name__)
CORS(app)  # 允許跨域請求

# 配置
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_DIR, "logs")
DATA_DIR = os.path.join(PROJECT_DIR, "data", "scraped_articles")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def get_pipeline_pid() -> Dict[str, Any]:
    """獲取所有 Pipeline 相關進程"""
    pids = {
        "scrape": None,
        "import": None,
        "parse": None,
        "embed": None,
        "main": None,
    }

    process_patterns = [
        ("scrape", "scrape_all_to_local.py"),
        ("import", "import_to_database.py"),
        ("parse", "parse_all_articles.py"),
        ("embed", "embed_all_articles.py"),
        ("main", "run_complete_pipeline.sh"),
    ]

    for name, pattern in process_patterns:
        try:
            result = subprocess.run(
                ["pgrep", "-f", pattern],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pids[name] = int(result.stdout.strip().split()[0])
        except:
            pass

    return pids


def get_current_phase(pids: Dict) -> str:
    """根據運行的進程確定當前階段"""
    if pids.get("scrape"):
        return "scraping"
    elif pids.get("import"):
        return "importing"
    elif pids.get("parse"):
        return "parsing"
    elif pids.get("embed"):
        return "embedding"
    elif pids.get("main"):
        return "running"
    return "stopped"


def get_pipeline_runtime(pid: int) -> Optional[str]:
    """獲取進程運行時間"""
    if not pid:
        return None
    try:
        result = subprocess.run(
            ["ps", "-o", "etime=", "-p", str(pid)],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() if result.stdout.strip() else None
    except:
        return None


def get_latest_log_file() -> Optional[str]:
    """獲取最新的日誌文件（包括所有類型）"""
    log_patterns = [
        os.path.join(LOG_DIR, "complete_pipeline_*.log"),
        os.path.join(LOG_DIR, "scrape_local_*.log"),
        os.path.join(LOG_DIR, "import_*.log"),
        os.path.join(LOG_DIR, "parse_*.log"),
        os.path.join(LOG_DIR, "embed_*.log"),
        os.path.join(LOG_DIR, "pipeline_*.log"),
    ]

    all_logs = []
    for pattern in log_patterns:
        all_logs.extend(glob.glob(pattern))

    if all_logs:
        return max(all_logs, key=os.path.getmtime)
    return None


def get_log_tail(log_file: str, lines: int = 20) -> List[str]:
    """獲取日誌文件的最後幾行"""
    try:
        result = subprocess.run(
            ["tail", f"-{lines}", log_file],
            capture_output=True,
            text=True
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except:
        return []


def get_local_scrape_stats() -> Dict[str, Any]:
    """獲取本地抓取進度"""
    stats = {
        "total_local": 0,
        "categories": {},
        "progress_file": None,
    }

    # 檢查進度文件
    progress_file = os.path.join(DATA_DIR, "progress.json")
    if os.path.exists(progress_file):
        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                progress = json.load(f)
                stats["progress_file"] = progress
                stats["last_update"] = progress.get("last_update")
        except:
            pass

    # 統計各 JSONL 文件的行數
    jsonl_files = glob.glob(os.path.join(DATA_DIR, "articles_*.jsonl"))
    for jsonl_file in jsonl_files:
        try:
            # 使用 wc -l 快速計算行數
            result = subprocess.run(
                ["wc", "-l", jsonl_file],
                capture_output=True,
                text=True
            )
            line_count = int(result.stdout.strip().split()[0])

            category = os.path.basename(jsonl_file).replace("articles_", "").replace(".jsonl", "")
            stats["categories"][category] = line_count
            stats["total_local"] += line_count
        except:
            pass

    return stats


def get_database_stats() -> Dict[str, int]:
    """從 Supabase 獲取文章統計"""
    try:
        import httpx

        stats = {"scraped": 0, "parsed": 0, "ready": 0, "total": 0}

        with httpx.Client(timeout=10.0) as client:
            for status in ["scraped", "parsed", "ready"]:
                response = client.get(
                    f"{SUPABASE_URL}/rest/v1/health_articles",
                    headers={
                        "apikey": SUPABASE_KEY,
                        "Authorization": f"Bearer {SUPABASE_KEY}",
                        "Prefer": "count=exact"
                    },
                    params={
                        "select": "count",
                        "status": f"eq.{status}"
                    }
                )
                # 從 Content-Range header 獲取計數
                content_range = response.headers.get("content-range", "")
                if "/" in content_range:
                    count = int(content_range.split("/")[1])
                    stats[status] = count

        stats["total"] = stats["scraped"] + stats["parsed"] + stats["ready"]
        return stats
    except Exception as e:
        print(f"獲取數據庫統計失敗: {e}")
        return {"scraped": 0, "parsed": 0, "ready": 0, "total": 0, "error": str(e)}


@app.route("/api/pipeline/status", methods=["GET"])
def get_status():
    """獲取 Pipeline 狀態"""
    pids = get_pipeline_pid()
    current_phase = get_current_phase(pids)

    # 獲取主進程的運行時間
    main_pid = pids.get("main") or pids.get("scrape") or pids.get("import") or pids.get("parse") or pids.get("embed")
    runtime = get_pipeline_runtime(main_pid)

    log_file = get_latest_log_file()
    db_stats = get_database_stats()
    local_stats = get_local_scrape_stats()

    # 計算完成率（基於數據庫）
    total = db_stats.get("total", 0)
    ready = db_stats.get("ready", 0)
    completion_rate = round(ready / total * 100, 1) if total > 0 else 0

    # 判斷狀態
    is_running = any(pids.values())

    # 階段描述
    phase_descriptions = {
        "stopped": "已停止",
        "scraping": "階段 1: 抓取文章到本地",
        "importing": "階段 2: 導入數據庫",
        "parsing": "階段 3: AI 解析文章",
        "embedding": "階段 4: 向量化文章",
        "running": "運行中",
    }

    return jsonify({
        "status": "running" if is_running else "stopped",
        "phase": current_phase,
        "phase_description": phase_descriptions.get(current_phase, current_phase),
        "pid": main_pid,
        "pids": pids,
        "runtime": runtime,
        "log_file": os.path.basename(log_file) if log_file else None,
        "database": db_stats,
        "local": local_stats,
        "completion_rate": completion_rate,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/pipeline/logs", methods=["GET"])
def get_logs():
    """獲取最新日誌"""
    lines = request.args.get("lines", 50, type=int)
    log_file = get_latest_log_file()

    if not log_file:
        return jsonify({"logs": [], "log_file": None})

    log_lines = get_log_tail(log_file, lines)

    return jsonify({
        "logs": log_lines,
        "log_file": os.path.basename(log_file),
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/pipeline/local-stats", methods=["GET"])
def get_local_stats():
    """獲取本地抓取統計"""
    stats = get_local_scrape_stats()
    return jsonify(stats)


@app.route("/api/pipeline/start", methods=["POST"])
def start_pipeline():
    """啟動 Pipeline"""
    pids = get_pipeline_pid()
    if any(pids.values()):
        return jsonify({
            "success": False,
            "message": f"Pipeline 已在運行中"
        }), 400

    try:
        # 啟動新的完整 Pipeline
        script_path = os.path.join(PROJECT_DIR, "scripts", "run_complete_pipeline.sh")
        log_file = os.path.join(LOG_DIR, f"complete_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

        with open(log_file, "w") as f:
            subprocess.Popen(
                ["nohup", script_path],
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=PROJECT_DIR,
                start_new_session=True
            )

        # 等待一下讓進程啟動
        import time
        time.sleep(2)

        new_pids = get_pipeline_pid()
        return jsonify({
            "success": True,
            "message": "Pipeline 已啟動",
            "pids": new_pids
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"啟動失敗: {str(e)}"
        }), 500


@app.route("/api/pipeline/stop", methods=["POST"])
def stop_pipeline():
    """停止 Pipeline"""
    pids = get_pipeline_pid()
    if not any(pids.values()):
        return jsonify({
            "success": False,
            "message": "Pipeline 未運行"
        }), 400

    try:
        # 停止所有相關進程
        stopped = []
        for name, pid in pids.items():
            if pid:
                try:
                    subprocess.run(["kill", str(pid)], check=True)
                    stopped.append(name)
                except:
                    pass

        return jsonify({
            "success": True,
            "message": f"已停止進程: {', '.join(stopped)}"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"停止失敗: {str(e)}"
        }), 500


@app.route("/api/pipeline/history", methods=["GET"])
def get_history():
    """獲取歷史運行記錄"""
    log_patterns = [
        ("complete_pipeline_*.log", "完整 Pipeline"),
        ("scrape_local_*.log", "本地抓取"),
        ("import_*.log", "數據庫導入"),
        ("parse_*.log", "AI 解析"),
        ("embed_*.log", "向量化"),
    ]

    history = []
    for pattern, desc in log_patterns:
        full_pattern = os.path.join(LOG_DIR, pattern)
        log_files = sorted(glob.glob(full_pattern), key=os.path.getmtime, reverse=True)[:5]

        for log_file in log_files:
            basename = os.path.basename(log_file)
            file_size = os.path.getsize(log_file)
            mtime = datetime.fromtimestamp(os.path.getmtime(log_file))

            history.append({
                "filename": basename,
                "type": desc,
                "start_time": mtime.isoformat(),
                "size_kb": round(file_size / 1024, 1)
            })

    # 按時間排序
    history.sort(key=lambda x: x["start_time"], reverse=True)

    return jsonify({"history": history[:15]})


if __name__ == "__main__":
    print("=" * 60)
    print("Pipeline 監控 API 服務器 (v2 - 支持分階段 Pipeline)")
    print("=" * 60)
    print(f"監控目錄: {PROJECT_DIR}")
    print(f"日誌目錄: {LOG_DIR}")
    print(f"數據目錄: {DATA_DIR}")
    print("")
    print("API 端點:")
    print("  GET  /api/pipeline/status      - 獲取狀態")
    print("  GET  /api/pipeline/logs        - 獲取日誌")
    print("  GET  /api/pipeline/local-stats - 獲取本地抓取統計")
    print("  GET  /api/pipeline/history     - 獲取歷史")
    print("  POST /api/pipeline/start       - 啟動 Pipeline")
    print("  POST /api/pipeline/stop        - 停止 Pipeline")
    print("=" * 60)

    app.run(host="0.0.0.0", port=5050, debug=False)
