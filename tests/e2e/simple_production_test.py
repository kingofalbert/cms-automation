"""
CMS Automation 生产环境简化测试
使用 HTTP 请求测试后端 API 和前端可访问性
"""

import requests
import json
from datetime import datetime
from typing import Dict, List

# 配置
FRONTEND_URL = "https://storage.googleapis.com/cms-automation-frontend-476323/index.html"
BACKEND_URL = "https://cms-automation-backend-baau2zqeqq-ue.a.run.app"

class SimpleProductionTester:
    def __init__(self):
        self.test_results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}: {details}")

    def test_frontend_accessibility(self):
        """测试1: 前端可访问性"""
        print("\n🧪 测试1: 前端可访问性")
        try:
            response = self.session.get(FRONTEND_URL, timeout=30)
            passed = response.status_code == 200 and 'text/html' in response.headers.get('content-type', '')

            # 检查内容
            has_root = 'id="root"' in response.text
            has_scripts = '<script' in response.text
            has_css = '.css' in response.text or '<link' in response.text

            self.log_result(
                "前端HTML加载",
                passed and has_root and has_scripts,
                f"状态码: {response.status_code}, 有root div: {has_root}, 有脚本: {has_scripts}"
            )

            # 检查前端文件大小
            content_length = len(response.text)
            self.log_result(
                "前端内容完整性",
                content_length > 500,
                f"HTML大小: {content_length} 字节"
            )

        except Exception as e:
            self.log_result("前端可访问性", False, f"错误: {str(e)}")

    def test_backend_health(self):
        """测试2: 后端健康检查"""
        print("\n🧪 测试2: 后端健康检查")
        try:
            response = self.session.get(f"{BACKEND_URL}/health", timeout=10)
            data = response.json()

            passed = response.status_code == 200 and data.get("status") == "healthy"
            self.log_result(
                "后端健康状态",
                passed,
                f"状态码: {response.status_code}, 响应: {data}"
            )

        except Exception as e:
            self.log_result("后端健康检查", False, f"错误: {str(e)}")

    def test_backend_api_root(self):
        """测试3: 后端API根路径"""
        print("\n🧪 测试3: 后端API根路径")
        try:
            response = self.session.get(BACKEND_URL, timeout=10)
            data = response.json()

            has_docs = "docs" in data or "/docs" in str(data)
            passed = response.status_code == 200 and has_docs

            self.log_result(
                "API根路径响应",
                passed,
                f"状态码: {response.status_code}, 数据: {data}"
            )

        except Exception as e:
            self.log_result("后端API根路径", False, f"错误: {str(e)}")

    def test_api_docs_availability(self):
        """测试4: API文档可访问性"""
        print("\n🧪 测试4: API文档可访问性")
        try:
            response = self.session.get(f"{BACKEND_URL}/docs", timeout=10)
            passed = response.status_code == 200

            # 检查是否是 Swagger/OpenAPI文档
            has_swagger = 'swagger' in response.text.lower() or 'openapi' in response.text.lower()

            self.log_result(
                "API文档可访问",
                passed and has_swagger,
                f"状态码: {response.status_code}, 是Swagger文档: {has_swagger}"
            )

        except Exception as e:
            self.log_result("API文档可访问性", False, f"错误: {str(e)}")

    def test_cors_headers(self):
        """测试5: CORS配置"""
        print("\n🧪 测试5: CORS配置检查")
        try:
            response = self.session.options(f"{BACKEND_URL}/health", timeout=10)

            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            }

            has_cors = any(cors_headers.values())

            self.log_result(
                "CORS配置",
                has_cors,
                f"CORS headers: {cors_headers}"
            )

        except Exception as e:
            self.log_result("CORS配置", False, f"错误: {str(e)}")

    def test_response_times(self):
        """测试6: 响应时间"""
        print("\n🧪 测试6: API响应时间")

        endpoints = [
            ("/health", "健康检查"),
            ("/", "根路径"),
        ]

        for endpoint, name in endpoints:
            try:
                import time
                start = time.time()
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=10)
                duration = time.time() - start

                passed = response.status_code == 200 and duration < 5.0
                self.log_result(
                    f"响应时间: {name}",
                    passed,
                    f"耗时: {duration:.2f}秒, 状态: {response.status_code}"
                )

            except Exception as e:
                self.log_result(f"响应时间: {name}", False, f"错误: {str(e)}")

    def test_backend_error_handling(self):
        """测试7: 后端错误处理"""
        print("\n🧪 测试7: 后端错误处理")
        try:
            # 测试不存在的端点
            response = self.session.get(f"{BACKEND_URL}/nonexistent-endpoint-12345", timeout=10)

            # 应该返回404或其他合适的错误码
            passed = response.status_code in [404, 422, 405]

            self.log_result(
                "404错误处理",
                passed,
                f"状态码: {response.status_code}"
            )

        except Exception as e:
            self.log_result("后端错误处理", False, f"错误: {str(e)}")

    def test_security_headers(self):
        """测试8: 安全头检查"""
        print("\n🧪 测试8: 安全HTTP头")
        try:
            response = self.session.get(BACKEND_URL, timeout=10)

            security_headers = {
                'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                'X-Frame-Options': response.headers.get('X-Frame-Options'),
                'Strict-Transport-Security': response.headers.get('Strict-Transport-Security'),
            }

            has_security = any(security_headers.values())

            self.log_result(
                "安全HTTP头",
                has_security,
                f"安全头: {security_headers}"
            )

        except Exception as e:
            self.log_result("安全头检查", False, f"错误: {str(e)}")

    def test_frontend_assets(self):
        """测试9: 前端静态资源"""
        print("\n🧪 测试9: 前端静态资源")
        try:
            # 获取index.html并提取资源URL
            response = self.session.get(FRONTEND_URL, timeout=30)
            html = response.text

            # 检查CSS
            has_css = '.css' in html
            # 检查JS
            has_js = '.js' in html
            # 检查模块
            has_modules = 'type="module"' in html or 'crossorigin' in html

            self.log_result(
                "前端资源引用",
                has_css and has_js,
                f"CSS: {has_css}, JS: {has_js}, ES模块: {has_modules}"
            )

        except Exception as e:
            self.log_result("前端静态资源", False, f"错误: {str(e)}")

    def test_cache_headers(self):
        """测试10: 缓存策略"""
        print("\n🧪 测试10: 缓存策略")
        try:
            # 检查前端HTML缓存
            response = self.session.get(FRONTEND_URL, timeout=30)
            html_cache = response.headers.get('Cache-Control', '')

            # HTML应该no-cache
            html_no_cache = 'no-cache' in html_cache.lower() or 'no-store' in html_cache.lower()

            self.log_result(
                "HTML缓存策略",
                html_no_cache,
                f"Cache-Control: {html_cache}"
            )

        except Exception as e:
            self.log_result("缓存策略", False, f"错误: {str(e)}")

    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📊 测试报告摘要")
        print("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["passed"])
        failed_tests = total_tests - passed_tests

        print(f"\n总测试数: {total_tests}")
        print(f"✅ 通过: {passed_tests}")
        print(f"❌ 失败: {failed_tests}")
        print(f"成功率: {(passed_tests/total_tests*100):.1f}%")

        print("\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["passed"] else "❌"
            print(f"{status} {result['test']}")
            if result["details"]:
                print(f"   └─ {result['details']}")

        # 保存JSON报告
        report_file = f"/tmp/simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "success_rate": round(passed_tests/total_tests*100, 1)
                },
                "tests": self.test_results,
                "frontend_url": FRONTEND_URL,
                "backend_url": BACKEND_URL,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细报告已保存: {report_file}")

        return passed_tests, failed_tests

def main():
    """主测试函数"""
    print("🚀 CMS Automation 生产环境简化测试")
    print(f"前端URL: {FRONTEND_URL}")
    print(f"后端URL: {BACKEND_URL}")
    print("="*60)

    tester = SimpleProductionTester()

    try:
        # 运行所有测试
        tester.test_frontend_accessibility()
        tester.test_backend_health()
        tester.test_backend_api_root()
        tester.test_api_docs_availability()
        tester.test_cors_headers()
        tester.test_response_times()
        tester.test_backend_error_handling()
        tester.test_security_headers()
        tester.test_frontend_assets()
        tester.test_cache_headers()

        # 生成报告
        passed, failed = tester.generate_report()

    except Exception as e:
        print(f"\n❌ 测试执行错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n✅ 测试完成!")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())
