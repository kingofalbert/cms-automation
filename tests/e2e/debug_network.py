#!/usr/bin/env python3
"""
Debug script to capture network requests and responses from the frontend.
"""

import os
import time
import json
from playwright.sync_api import sync_playwright

# Configuration
FRONTEND_URL = "https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html"
AUTH_EMAIL = os.getenv("TEST_AUTH_EMAIL", "allen.chen@epochtimes.com")
AUTH_PASSWORD = os.getenv("TEST_AUTH_PASSWORD", "Editor123$")

def main():
    print("=" * 70)
    print("  Network Debug - CMS Frontend")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-TW",
        )
        page = context.new_page()

        # Capture all network requests and responses
        requests_log = []
        responses_log = []
        console_log = []

        def on_request(request):
            requests_log.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
            })
            if "/v1/" in request.url or "/api/" in request.url:
                print(f"\n  [REQUEST] {request.method} {request.url}")
                auth_header = request.headers.get("authorization", "NONE")
                print(f"    Auth: {auth_header[:50]}..." if len(auth_header) > 50 else f"    Auth: {auth_header}")

        def on_response(response):
            responses_log.append({
                "url": response.url,
                "status": response.status,
            })
            if "/v1/" in response.url or "/api/" in response.url:
                print(f"  [RESPONSE] {response.status} {response.url}")
                if response.status >= 400:
                    try:
                        body = response.text()
                        print(f"    Error: {body[:200]}")
                    except:
                        pass

        def on_console(msg):
            console_log.append({
                "type": msg.type,
                "text": msg.text,
            })
            if "error" in msg.type.lower() or "warn" in msg.type.lower():
                print(f"  [CONSOLE {msg.type.upper()}] {msg.text[:200]}")

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", on_console)

        # Step 1: Load login page
        print("\n--- Loading login page ---")
        login_url = f"{FRONTEND_URL}#/login"
        page.goto(login_url, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2)

        print(f"  Current URL: {page.url}")

        # Step 2: Login
        print("\n--- Performing login ---")
        try:
            email_input = page.locator('input[type="email"]')
            email_input.wait_for(state="visible", timeout=15000)
            email_input.fill(AUTH_EMAIL)

            password_input = page.locator('input[type="password"]')
            password_input.fill(AUTH_PASSWORD)

            submit_btn = page.locator('button[type="submit"]')
            submit_btn.click()

            # Wait for auth to complete
            time.sleep(5)
            page.wait_for_load_state("networkidle", timeout=15000)

            print(f"  Current URL after login: {page.url}")

        except Exception as e:
            print(f"  Login error: {e}")

        # Step 3: Navigate to worklist
        print("\n--- Navigating to worklist ---")
        worklist_url = f"{FRONTEND_URL}#/worklist"
        page.goto(worklist_url, timeout=30000)

        # Wait and capture API calls
        print("\n--- Waiting for API calls (15 seconds) ---")
        time.sleep(15)

        # Take screenshot
        screenshot_path = "/Users/albertking/ES/cms_automation/tests/e2e/screenshots/debug_network.png"
        page.screenshot(path=screenshot_path)
        print(f"\n  Screenshot saved: {screenshot_path}")

        # Summary
        print("\n--- Summary ---")
        print(f"  Total requests: {len(requests_log)}")
        print(f"  Total responses: {len(responses_log)}")
        print(f"  Console messages: {len(console_log)}")

        # API calls summary
        api_requests = [r for r in requests_log if "/v1/" in r["url"] or "/api/" in r["url"]]
        api_responses = [r for r in responses_log if "/v1/" in r["url"] or "/api/" in r["url"]]

        print(f"\n  API Requests: {len(api_requests)}")
        for req in api_requests:
            print(f"    - {req['method']} {req['url']}")

        print(f"\n  API Responses: {len(api_responses)}")
        for resp in api_responses:
            print(f"    - {resp['status']} {resp['url']}")

        # Console errors
        errors = [c for c in console_log if "error" in c["type"].lower()]
        if errors:
            print(f"\n  Console Errors: {len(errors)}")
            for err in errors[:5]:
                print(f"    - {err['text'][:100]}")

        browser.close()

if __name__ == "__main__":
    main()
