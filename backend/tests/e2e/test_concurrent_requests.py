#!/usr/bin/env python3
"""E2E Concurrent Requests Tests for CMS Automation"""

import asyncio
import time
from datetime import datetime

import httpx


class ConcurrentRequestTests:
    """Test suite for concurrent request handling"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []

    def log_result(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
        print(f"{emoji} {test_name}: {status}")
        if details:
            print(f"   {details}")

    async def create_topic(self, client: httpx.AsyncClient, topic_num: int) -> dict | None:
        """Create a single topic request"""
        test_data = {
            "topic_description": f"Concurrent test article #{topic_num} - {datetime.now().isoformat()}",
            "target_word_count": 500,
            "style_tone": "professional"
        }
        
        try:
            response = await client.post(
                f"{self.base_url}/v1/topics",
                json=test_data,
                timeout=10.0
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"   ⚠️  Topic {topic_num} creation failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ⚠️  Topic {topic_num} exception: {str(e)}")
            return None

    async def test_concurrent_topic_creation(self, num_requests: int = 5):
        """Test 1: Concurrent topic creation"""
        print("\n" + "="*80)
        print(f"Test 1: Concurrent Topic Creation ({num_requests} requests)")
        print("="*80)
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            # Create all topics concurrently
            tasks = [
                self.create_topic(client, i+1)
                for i in range(num_requests)
            ]
            
            print(f"Creating {num_requests} topics concurrently...")
            topics = await asyncio.gather(*tasks)
            
            elapsed = time.time() - start_time
            successful = sum(1 for t in topics if t is not None)
            
            print(f"\nResults:")
            print(f"  Total requests: {num_requests}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {num_requests - successful}")
            print(f"  Time elapsed: {elapsed:.2f}s")
            print(f"  Avg time per request: {elapsed/num_requests:.2f}s")
            
            if successful == num_requests:
                self.log_result(
                    "Concurrent topic creation",
                    "PASS",
                    f"All {num_requests} topics created in {elapsed:.2f}s"
                )
                return [t for t in topics if t is not None]
            elif successful > 0:
                self.log_result(
                    "Concurrent topic creation",
                    "PARTIAL",
                    f"{successful}/{num_requests} topics created"
                )
                return [t for t in topics if t is not None]
            else:
                self.log_result(
                    "Concurrent topic creation",
                    "FAIL",
                    "No topics created successfully"
                )
                return []

    async def monitor_topic_processing(self, topic_ids: list[int], timeout: int = 120):
        """Test 2: Monitor concurrent processing"""
        print("\n" + "="*80)
        print(f"Test 2: Monitor Concurrent Processing ({len(topic_ids)} topics)")
        print("="*80)
        
        start_time = time.time()
        completed_topics = set()
        failed_topics = set()
        
        async with httpx.AsyncClient() as client:
            print(f"Monitoring topics: {topic_ids}")
            print(f"Timeout: {timeout}s")
            print()
            
            while time.time() - start_time < timeout:
                # Check status of all topics
                for topic_id in topic_ids:
                    if topic_id in completed_topics or topic_id in failed_topics:
                        continue
                    
                    try:
                        response = await client.get(
                            f"{self.base_url}/v1/topics/{topic_id}",
                            timeout=5.0
                        )
                        
                        if response.status_code == 200:
                            topic = response.json()
                            status = topic["status"]
                            
                            if status == "completed":
                                completed_topics.add(topic_id)
                                elapsed = time.time() - start_time
                                print(f"  [{elapsed:5.1f}s] Topic {topic_id}: COMPLETED ✅")
                            elif status == "failed":
                                failed_topics.add(topic_id)
                                print(f"  Topic {topic_id}: FAILED ❌")
                    
                    except Exception as e:
                        print(f"  Topic {topic_id} check error: {str(e)}")
                
                # Check if all done
                if len(completed_topics) + len(failed_topics) == len(topic_ids):
                    break
                
                await asyncio.sleep(2)
        
        elapsed = time.time() - start_time
        
        print()
        print("Processing Results:")
        print(f"  Completed: {len(completed_topics)}/{len(topic_ids)}")
        print(f"  Failed: {len(failed_topics)}/{len(topic_ids)}")
        print(f"  Still processing: {len(topic_ids) - len(completed_topics) - len(failed_topics)}")
        print(f"  Total time: {elapsed:.1f}s")
        
        if len(completed_topics) == len(topic_ids):
            self.log_result(
                "Concurrent processing",
                "PASS",
                f"All {len(topic_ids)} topics completed in {elapsed:.1f}s"
            )
        elif len(completed_topics) > 0:
            self.log_result(
                "Concurrent processing",
                "PARTIAL",
                f"{len(completed_topics)}/{len(topic_ids)} completed"
            )
        else:
            self.log_result(
                "Concurrent processing",
                "FAIL",
                "No topics completed"
            )
        
        return completed_topics

    async def verify_articles_created(self, completed_topic_ids: set[int]):
        """Test 3: Verify articles were created for completed topics"""
        print("\n" + "="*80)
        print(f"Test 3: Verify Article Creation ({len(completed_topic_ids)} topics)")
        print("="*80)
        
        async with httpx.AsyncClient() as client:
            articles_created = 0
            
            for topic_id in completed_topic_ids:
                try:
                    # Get topic to find article_id
                    topic_response = await client.get(
                        f"{self.base_url}/v1/topics/{topic_id}",
                        timeout=5.0
                    )
                    
                    if topic_response.status_code == 200:
                        topic = topic_response.json()
                        article_id = topic.get("article_id")
                        
                        if article_id:
                            # Verify article exists
                            article_response = await client.get(
                                f"{self.base_url}/v1/articles/{article_id}",
                                timeout=5.0
                            )
                            
                            if article_response.status_code == 200:
                                article = article_response.json()
                                print(f"  Topic {topic_id} → Article {article_id}: {article['title'][:50]}...")
                                articles_created += 1
                            else:
                                print(f"  Topic {topic_id} → Article {article_id}: NOT FOUND ❌")
                        else:
                            print(f"  Topic {topic_id}: No article_id ⚠️")
                
                except Exception as e:
                    print(f"  Topic {topic_id} verification error: {str(e)}")
            
            print()
            print(f"Articles created: {articles_created}/{len(completed_topic_ids)}")
            
            if articles_created == len(completed_topic_ids):
                self.log_result(
                    "Article creation verification",
                    "PASS",
                    f"All {articles_created} articles created successfully"
                )
            elif articles_created > 0:
                self.log_result(
                    "Article creation verification",
                    "PARTIAL",
                    f"{articles_created}/{len(completed_topic_ids)} articles created"
                )
            else:
                self.log_result(
                    "Article creation verification",
                    "FAIL",
                    "No articles found"
                )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("CONCURRENT REQUEST TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        partial = sum(1 for r in self.results if r["status"] == "PARTIAL")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"⚠️  Partial: {partial}")
        print(f"❌ Failed: {failed}")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")

    async def run_all_tests(self, num_concurrent: int = 3):
        """Run all concurrent request tests"""
        print("="*80)
        print("E2E CONCURRENT REQUEST TESTS - CMS Automation")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print(f"Concurrent Requests: {num_concurrent}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test 1: Create topics concurrently
        topics = await self.test_concurrent_topic_creation(num_concurrent)
        
        if not topics:
            print("\n❌ No topics created, cannot continue testing")
            return
        
        # Extract topic IDs
        topic_ids = [t["id"] for t in topics]
        
        # Test 2: Monitor concurrent processing
        completed = await self.monitor_topic_processing(topic_ids, timeout=180)
        
        if completed:
            # Test 3: Verify articles created
            await self.verify_articles_created(completed)
        
        self.print_summary()


async def main():
    """Main test runner"""
    tests = ConcurrentRequestTests()
    
    # Test with 3 concurrent requests (conservative for API limits)
    await tests.run_all_tests(num_concurrent=3)


if __name__ == "__main__":
    asyncio.run(main())
