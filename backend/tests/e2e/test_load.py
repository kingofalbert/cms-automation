#!/usr/bin/env python3
"""Load Testing for CMS Automation - 10+ Concurrent Requests"""

import asyncio
import time
from datetime import datetime
from statistics import mean, median, stdev

import httpx


class LoadTester:
    """Load testing suite for production readiness validation"""

    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = []
        self.metrics = {
            "topic_creation_times": [],
            "processing_times": [],
            "total_times": [],
            "success_count": 0,
            "failure_count": 0,
        }

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
            "topic_description": f"Load test article #{topic_num} - Performance validation at {datetime.now().isoformat()}",
            "target_word_count": 800,  # Shorter for faster testing
            "style_tone": "professional"
        }

        start_time = time.time()
        try:
            response = await client.post(
                f"{self.base_url}/v1/topics",
                json=test_data,
                timeout=10.0
            )

            elapsed = time.time() - start_time
            self.metrics["topic_creation_times"].append(elapsed)

            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"   ⚠️  Topic {topic_num} creation failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"   ⚠️  Topic {topic_num} exception: {str(e)}")
            return None

    async def test_load_topic_creation(self, num_requests: int = 10):
        """Test 1: Load test topic creation"""
        print("\n" + "="*80)
        print(f"LOAD TEST 1: Concurrent Topic Creation ({num_requests} requests)")
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

            # Calculate statistics
            creation_times = self.metrics["topic_creation_times"]
            avg_time = mean(creation_times) if creation_times else 0
            median_time = median(creation_times) if creation_times else 0

            print("\nResults:")
            print(f"  Total requests: {num_requests}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {num_requests - successful}")
            print(f"  Total time: {elapsed:.2f}s")
            print(f"  Avg creation time: {avg_time:.3f}s")
            print(f"  Median creation time: {median_time:.3f}s")
            print(f"  Throughput: {successful/elapsed:.2f} topics/sec")

            if successful >= num_requests * 0.9:  # 90% success threshold
                self.log_result(
                    "Load test: Topic creation",
                    "PASS",
                    f"{successful}/{num_requests} topics created in {elapsed:.2f}s"
                )
                return [t for t in topics if t is not None]
            else:
                self.log_result(
                    "Load test: Topic creation",
                    "FAIL",
                    f"Only {successful}/{num_requests} topics created successfully"
                )
                return [t for t in topics if t is not None]

    async def monitor_processing(self, topic_ids: list[int], timeout: int = 600):
        """Test 2: Monitor concurrent processing under load"""
        print("\n" + "="*80)
        print(f"LOAD TEST 2: Monitor Processing Under Load ({len(topic_ids)} topics)")
        print("="*80)

        start_time = time.time()
        completed_topics = {}
        failed_topics = set()

        async with httpx.AsyncClient() as client:
            print(f"Monitoring {len(topic_ids)} topics")
            print(f"Timeout: {timeout}s ({timeout/60:.1f} minutes)")
            print()

            while time.time() - start_time < timeout:
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
                                elapsed = time.time() - start_time
                                completed_topics[topic_id] = elapsed
                                self.metrics["processing_times"].append(elapsed)
                                print(f"  [{elapsed:6.1f}s] Topic {topic_id}: COMPLETED ✅")
                            elif status == "failed":
                                failed_topics.add(topic_id)
                                print(f"  Topic {topic_id}: FAILED ❌")

                    except Exception as e:
                        print(f"  Topic {topic_id} check error: {str(e)}")

                # Check if all done
                if len(completed_topics) + len(failed_topics) == len(topic_ids):
                    break

                await asyncio.sleep(3)  # Check every 3 seconds

        total_elapsed = time.time() - start_time

        # Calculate processing statistics
        if self.metrics["processing_times"]:
            avg_processing = mean(self.metrics["processing_times"])
            median_processing = median(self.metrics["processing_times"])
            min_processing = min(self.metrics["processing_times"])
            max_processing = max(self.metrics["processing_times"])

            if len(self.metrics["processing_times"]) > 1:
                stddev_processing = stdev(self.metrics["processing_times"])
            else:
                stddev_processing = 0
        else:
            avg_processing = median_processing = min_processing = max_processing = stddev_processing = 0

        print()
        print("Processing Results:")
        print(f"  Completed: {len(completed_topics)}/{len(topic_ids)}")
        print(f"  Failed: {len(failed_topics)}/{len(topic_ids)}")
        print(f"  Still processing: {len(topic_ids) - len(completed_topics) - len(failed_topics)}")
        print(f"  Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} minutes)")

        if self.metrics["processing_times"]:
            print("\nProcessing Time Statistics:")
            print(f"  Average: {avg_processing:.2f}s")
            print(f"  Median: {median_processing:.2f}s")
            print(f"  Min: {min_processing:.2f}s")
            print(f"  Max: {max_processing:.2f}s")
            print(f"  Std Dev: {stddev_processing:.2f}s")
            print("\nSLA Compliance (< 300s):")
            sla_compliant = sum(1 for t in self.metrics["processing_times"] if t < 300)
            print(f"  Compliant: {sla_compliant}/{len(self.metrics['processing_times'])} ({sla_compliant/len(self.metrics['processing_times'])*100:.1f}%)")

        success_rate = len(completed_topics) / len(topic_ids)

        if success_rate >= 0.9:  # 90% success threshold
            self.log_result(
                "Load test: Processing under load",
                "PASS",
                f"{len(completed_topics)}/{len(topic_ids)} completed in {total_elapsed:.1f}s"
            )
        else:
            self.log_result(
                "Load test: Processing under load",
                "FAIL",
                f"Only {len(completed_topics)}/{len(topic_ids)} completed"
            )

        self.metrics["success_count"] = len(completed_topics)
        self.metrics["failure_count"] = len(failed_topics)

        return set(completed_topics.keys())

    async def verify_articles_created(self, completed_topic_ids: set[int]):
        """Test 3: Verify all articles were created"""
        print("\n" + "="*80)
        print(f"LOAD TEST 3: Verify Article Creation ({len(completed_topic_ids)} topics)")
        print("="*80)

        async with httpx.AsyncClient() as client:
            articles_created = 0
            word_counts = []
            costs = []

            for topic_id in completed_topic_ids:
                try:
                    topic_response = await client.get(
                        f"{self.base_url}/v1/topics/{topic_id}",
                        timeout=5.0
                    )

                    if topic_response.status_code == 200:
                        topic = topic_response.json()
                        article_id = topic.get("article_id")

                        if article_id:
                            article_response = await client.get(
                                f"{self.base_url}/v1/articles/{article_id}",
                                timeout=5.0
                            )

                            if article_response.status_code == 200:
                                article = article_response.json()
                                word_counts.append(article.get("word_count", 0))
                                costs.append(article.get("generation_cost", 0))
                                print(f"  Article {article_id}: {article['word_count']} words, ${article.get('generation_cost', 0):.4f}")
                                articles_created += 1

                except Exception as e:
                    print(f"  Topic {topic_id} verification error: {str(e)}")

            print()
            print(f"Articles verified: {articles_created}/{len(completed_topic_ids)}")

            if word_counts:
                print("\nContent Statistics:")
                print(f"  Avg word count: {mean(word_counts):.0f}")
                print(f"  Total words generated: {sum(word_counts)}")

            if costs:
                print("\nCost Statistics:")
                print(f"  Avg cost per article: ${mean(costs):.4f}")
                print(f"  Total cost: ${sum(costs):.4f}")

            if articles_created == len(completed_topic_ids):
                self.log_result(
                    "Load test: Article verification",
                    "PASS",
                    f"All {articles_created} articles created successfully"
                )
            else:
                self.log_result(
                    "Load test: Article verification",
                    "PARTIAL",
                    f"{articles_created}/{len(completed_topic_ids)} articles verified"
                )

    def print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*80)
        print("LOAD TEST SUMMARY")
        print("="*80)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        partial = sum(1 for r in self.results if r["status"] == "PARTIAL")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)

        print("\nTest Results:")
        print(f"  Total Tests: {total}")
        print(f"  ✅ Passed: {passed}")
        print(f"  ⚠️  Partial: {partial}")
        print(f"  ❌ Failed: {failed}")

        if total > 0:
            success_rate = (passed / total) * 100
            print(f"  Success Rate: {success_rate:.1f}%")

        print("\nSystem Performance:")
        print(f"  Articles generated: {self.metrics['success_count']}")
        print(f"  Failed generations: {self.metrics['failure_count']}")

        if self.metrics["processing_times"]:
            avg_time = mean(self.metrics["processing_times"])
            sla_target = 300  # 5 minutes
            improvement = ((sla_target - avg_time) / sla_target) * 100
            print(f"  Avg processing time: {avg_time:.2f}s")
            print(f"  SLA target: {sla_target}s")
            print(f"  Performance improvement: {improvement:.1f}% faster than SLA")

    async def run_load_test(self, num_concurrent: int = 10):
        """Run complete load test suite"""
        print("="*80)
        print("CMS AUTOMATION - LOAD TESTING")
        print("="*80)
        print(f"Base URL: {self.base_url}")
        print(f"Concurrent Requests: {num_concurrent}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test 1: Create topics concurrently
        topics = await self.test_load_topic_creation(num_concurrent)

        if not topics:
            print("\n❌ No topics created, cannot continue testing")
            return

        # Extract topic IDs
        topic_ids = [t["id"] for t in topics]

        # Test 2: Monitor concurrent processing
        completed = await self.monitor_processing(topic_ids, timeout=600)

        if completed:
            # Test 3: Verify articles created
            await self.verify_articles_created(completed)

        self.print_summary()


async def main():
    """Main test runner"""
    tester = LoadTester()

    # Run with 10 concurrent requests (production load test)
    await tester.run_load_test(num_concurrent=10)


if __name__ == "__main__":
    asyncio.run(main())
