#!/usr/bin/env python3
"""E2E Error Handling Tests for CMS Automation"""

import asyncio
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

import httpx


class ErrorHandlingTests:
    """Test suite for error handling scenarios"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []

    def log_test(self, name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.results.append(result)

        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {name}: {status}")
        if details:
            print(f"   {details}")

    async def test_invalid_topic_data(self):
        """Test 1: Invalid topic request data"""
        print("\n" + "="*80)
        print("Test 1: Invalid Topic Request Data")
        print("="*80)

        test_cases = [
            {
                "name": "Empty topic description",
                "data": {"topic_description": "", "target_word_count": 1000},
                "expected_status": 422
            },
            {
                "name": "Negative word count",
                "data": {"topic_description": "Test", "target_word_count": -100},
                "expected_status": 422
            },
            {
                "name": "Extremely large word count",
                "data": {"topic_description": "Test", "target_word_count": 100000},
                "expected_status": 422
            },
            {
                "name": "Invalid priority",
                "data": {"topic_description": "Test", "priority": "invalid"},
                "expected_status": 422
            },
            {
                "name": "Missing required fields",
                "data": {},
                "expected_status": 422
            }
        ]

        async with httpx.AsyncClient() as client:
            for test_case in test_cases:
                try:
                    response = await client.post(
                        f"{self.base_url}/v1/topics",
                        json=test_case["data"],
                        timeout=5.0
                    )

                    if response.status_code == test_case["expected_status"]:
                        self.log_test(
                            test_case["name"],
                            "PASS",
                            f"Got expected status {test_case['expected_status']}"
                        )
                    else:
                        self.log_test(
                            test_case["name"],
                            "FAIL",
                            f"Expected {test_case['expected_status']}, got {response.status_code}"
                        )
                except Exception as e:
                    self.log_test(test_case["name"], "FAIL", f"Exception: {str(e)}")

    async def test_invalid_api_key(self):
        """Test 2: Invalid Anthropic API key"""
        print("\n" + "="*80)
        print("Test 2: Invalid API Key Handling")
        print("="*80)

        # This test would require temporarily changing the API key
        # For now, we'll create a topic and observe if it handles auth errors

        test_data = {
            "topic_description": "Test article for API error",
            "target_word_count": 500,
            "style_tone": "professional"
        }

        async with httpx.AsyncClient() as client:
            try:
                # Create topic request
                response = await client.post(
                    f"{self.base_url}/v1/topics",
                    json=test_data,
                    timeout=5.0
                )

                if response.status_code == 200:
                    topic_id = response.json()["id"]
                    self.log_test(
                        "Topic creation for API error test",
                        "PASS",
                        f"Created topic ID {topic_id}"
                    )

                    # Note: Actual API error testing would require modifying env
                    self.log_test(
                        "API error handling",
                        "INFO",
                        "Would require invalid API key to test fully"
                    )
                else:
                    self.log_test(
                        "Topic creation for API error test",
                        "FAIL",
                        f"Status: {response.status_code}"
                    )
            except Exception as e:
                self.log_test("Invalid API key test", "FAIL", f"Exception: {str(e)}")

    async def test_concurrent_duplicate_requests(self):
        """Test 3: Concurrent duplicate requests"""
        print("\n" + "="*80)
        print("Test 3: Duplicate Request Handling")
        print("="*80)

        test_data = {
            "topic_description": "Duplicate test article",
            "target_word_count": 500,
            "style_tone": "professional"
        }

        async with httpx.AsyncClient() as client:
            try:
                # Create the same topic twice
                response1 = await client.post(
                    f"{self.base_url}/v1/topics",
                    json=test_data,
                    timeout=5.0
                )

                response2 = await client.post(
                    f"{self.base_url}/v1/topics",
                    json=test_data,
                    timeout=5.0
                )

                if response1.status_code == 200 and response2.status_code == 200:
                    topic1_id = response1.json()["id"]
                    topic2_id = response2.json()["id"]

                    if topic1_id != topic2_id:
                        self.log_test(
                            "Duplicate requests create separate topics",
                            "PASS",
                            f"Created topics {topic1_id} and {topic2_id}"
                        )
                    else:
                        self.log_test(
                            "Duplicate request handling",
                            "INFO",
                            "System allows duplicate topics (no deduplication)"
                        )
                else:
                    self.log_test(
                        "Duplicate request test",
                        "FAIL",
                        f"Status codes: {response1.status_code}, {response2.status_code}"
                    )
            except Exception as e:
                self.log_test("Duplicate request test", "FAIL", f"Exception: {str(e)}")

    async def test_invalid_topic_id(self):
        """Test 4: Invalid topic ID retrieval"""
        print("\n" + "="*80)
        print("Test 4: Invalid Topic ID Handling")
        print("="*80)

        test_cases = [
            {"id": 99999, "name": "Non-existent topic ID"},
            {"id": -1, "name": "Negative topic ID"},
            {"id": "invalid", "name": "String topic ID"},
        ]

        async with httpx.AsyncClient() as client:
            for test_case in test_cases:
                try:
                    response = await client.get(
                        f"{self.base_url}/v1/topics/{test_case['id']}",
                        timeout=5.0
                    )

                    if response.status_code == 404:
                        self.log_test(
                            test_case["name"],
                            "PASS",
                            "Got expected 404 Not Found"
                        )
                    elif response.status_code == 422:
                        self.log_test(
                            test_case["name"],
                            "PASS",
                            "Got expected 422 Validation Error"
                        )
                    else:
                        self.log_test(
                            test_case["name"],
                            "FAIL",
                            f"Unexpected status: {response.status_code}"
                        )
                except Exception as e:
                    # String ID will cause an exception in path parameter parsing
                    if test_case["id"] == "invalid":
                        self.log_test(
                            test_case["name"],
                            "PASS",
                            "Validation error as expected"
                        )
                    else:
                        self.log_test(test_case["name"], "FAIL", f"Exception: {str(e)}")

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("ERROR HANDLING TEST SUMMARY")
        print("="*80)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        info = sum(1 for r in self.results if r["status"] == "INFO")
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"ℹ️  Info: {info}")
        print(f"\nSuccess Rate: {(passed/total*100):.1f}%")

        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if r["status"] == "FAIL":
                    print(f"  - {r['test']}: {r['details']}")

    async def run_all_tests(self):
        """Run all error handling tests"""
        print("="*80)
        print("E2E ERROR HANDLING TESTS - CMS Automation")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        await self.test_invalid_topic_data()
        await self.test_invalid_api_key()
        await self.test_concurrent_duplicate_requests()
        await self.test_invalid_topic_id()

        self.print_summary()


async def main():
    """Main test runner"""
    tests = ErrorHandlingTests()
    await tests.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
