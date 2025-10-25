# 🧭 Claude Computer Use CMS Automation Project (v2)

**Version:** 2.0  
**Author:** Albert King  
**Purpose:** Automate the CMS content-publishing workflow using **Anthropic Claude Computer Use API**.  
**Scope:** End-to-end automation – from content ingestion to scheduling and publishing via vision-based browser control.

---

## 🧩 1. Project Structure

```
cms_automation/
├── .env                         ← Environment variables
├── cms_automation.py            ← Main execution script
├── supabase_integration.py      ← Upload logs/screenshots to Supabase
├── scheduler.py                 ← Task scheduler and retry manager
├── error_handler.py             ← Error handling & rollback utilities
├── tasks/
│   └── post_20251025.json       ← Example task
├── logs/
│   └── cms_log_20251025.json    ← Execution logs
├── screenshots/
│   └── (Claude auto-generated images)
└── README.md                    ← This document
```

---

## ⚙️ 2. Environment Setup

### Prerequisites
- Python 3.10+
- Virtual Environment (Venv)
- Anthropic API Key (Computer Use Beta)
- Supabase Project & Service Key
- Secure Sandbox VM / Docker Environment

### Installation
```bash
python3 -m venv venv
source venv/bin/activate
pip install anthropic python-dotenv supabase
```

### `.env` Example
```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx
CMS_URL=https://cms.example.com
CMS_USERNAME=editor@domain.com
CMS_PASSWORD=your_password_here

SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📦 3. Task Definition (`tasks/post_20251025.json`)

```json
{
  "job_id": "POST_20251025_001",
  "cms_url": "https://cms.example.com",
  "title": "OEM Supply Chain Trends in North America",
  "body_html": "<p>In-depth analysis of OEM manufacturing and logistics shifts...</p>",
  "category": "Business",
  "tags": ["OEM", "Supply Chain"],
  "seo_title": "OEM Supply Chain Analysis",
  "seo_description": "A deep dive into OEM supply chain trends shaping 2025.",
  "schedule_et": "2025-10-25T19:30:00-04:00"
}
```

---

## 🧠 4. Main Script (`cms_automation.py`)

```python
import os, json, base64, time
from datetime import datetime
from dotenv import load_dotenv
import anthropic
from supabase_integration import upload_log_and_screenshots
from error_handler import retry_operation

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_cms_task(task_file):
    with open(task_file, "r") as f:
        task = json.load(f)

    system_prompt = f"""
You are an expert publishing assistant operating with Anthropic's Computer Use API.
Follow each step precisely:
1. Open Chrome and navigate to {task['cms_url']}.
2. Log in using environment variables (username & password).
3. Create a new article.
4. Paste the title: "{task['title']}".
5. Paste the HTML body content.
6. Set category "{task['category']}" and tags {task['tags']}.
7. Fill SEO title and description.
8. Schedule publication for {task['schedule_et']} (ET).
9. Save draft, verify success, and take screenshots.
Every action must be verified visually.
"""

    response = client.messages.create(
        model="claude-3.7-sonnet",
        max_output_tokens=2000,
        system=system_prompt,
        tools=[{"name": "computer_use"}],
        messages=[{"role": "user", "content": "Begin CMS automation now."}],
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("logs", exist_ok=True)
    os.makedirs("screenshots", exist_ok=True)

    log_path = f"logs/cms_log_{timestamp}.json"
    log_data = response.to_dict()

    # Save screenshots if included
    for content in response.content:
        if isinstance(content, dict) and content.get("type") == "image":
            img_data = base64.b64decode(content["data"])
            img_file = f"screenshots/{task['job_id']}_{timestamp}.png"
            with open(img_file, "wb") as f:
                f.write(img_data)

    with open(log_path, "w") as log_file:
        json.dump(log_data, log_file, indent=2)

    upload_log_and_screenshots(log_path, "screenshots/")
    print(f"✅ Task {task['job_id']} completed. Log: {log_path}")

if __name__ == "__main__":
    retry_operation(lambda: run_cms_task("tasks/post_20251025.json"), retries=3)
```

---

## 🌐 5. Supabase Integration (`supabase_integration.py`)

```python
import os, json, glob
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def upload_log_and_screenshots(log_path, screenshots_dir):
    print("Uploading to Supabase…")
    with open(log_path, "r") as f:
        log_json = json.load(f)
    supabase.table("cms_logs").insert(log_json).execute()

    for file in glob.glob(f"{screenshots_dir}/*.png"):
        with open(file, "rb") as f:
            supabase.storage.from_("cms_screens").upload(
                path=file.split("/")[-1],
                file=f,
                file_options={"content-type": "image/png"},
                upsert=True,
            )
    print("✅ Upload complete.")
```

---

## 🔁 6. Error Handler (`error_handler.py`)

```python
import time, traceback

def retry_operation(func, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            print(f"⚠️ Attempt {attempt} failed: {e}")
            traceback.print_exc()
            if attempt < retries:
                print(f"Retrying in {delay} seconds…")
                time.sleep(delay)
            else:
                print("❌ All attempts failed. Logged for manual review.")
```

---

## ⏰ 7. Scheduler (`scheduler.py`)

```python
import os, time
from datetime import datetime
from cms_automation import run_cms_task
from error_handler import retry_operation

def schedule_daily(hour=14, minute=0):
    print(f"Scheduler running. Tasks start daily at {hour}:{minute:02d}.")
    while True:
        now = datetime.now()
        if now.hour == hour and now.minute == minute:
            print(f"🚀 Running CMS task at {now}")
            retry_operation(lambda: run_cms_task("tasks/post_20251025.json"))
            time.sleep(60)  # Prevent re-trigger within same minute
        time.sleep(20)

if __name__ == "__main__":
    schedule_daily(14, 0)  # Example: 2 PM ET
```

---

## 🔐 8. Security Practices

| Category | Guideline |
|-----------|------------|
| **Environment** | Run inside VM / Docker container |
| **Credentials** | Never hard-code passwords; use .env |
| **Domain Whitelist** | Restrict Claude’s actions to CMS domain |
| **Human Checkpoints** | Confirm before publishing |
| **Audit Trail** | All actions logged + screenshots uploaded |
| **Rate Limits** | Limit one Computer Use session / minute |

---

## 📈 9. KPI Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Avg runtime / post | ≤ 2 min | Time from start to saved draft |
| Automation success rate | ≥ 85 % | No manual intervention |
| Metadata accuracy | ≥ 98 % | SEO + tag fields complete |
| Screenshot coverage | 100 % | Every major action logged |

---

## 🧰 10. Execution Commands

**Single Task**
```bash
python cms_automation.py
```

**Daily Scheduler**
```bash
python scheduler.py
```

**Log Inspection**
```bash
cat logs/cms_log_*.json
```

---

## 🧱 11. Next Steps

1. ✅ Test with 3–5 dummy posts in sandbox CMS  
2. 🧪 Validate Claude’s visual actions and scheduling accuracy  
3. 📤 Review logs / screenshots in Supabase dashboard  
4. 📧 Submit feedback to Anthropic (beta improvement)  
5. ⚙️ Deploy scheduler to server or cron container  

---

## 🧾 12. Changelog

| Version | Date | Updates |
|----------|------|----------|
| v1.0 | 2025-10-25 | Basic Computer Use prototype |
| v2.0 | 2025-10-25 | Added Supabase integration, retry logic, scheduler & full docs |

---

**End of Document — Claude Computer Use CMS Automation v2**
