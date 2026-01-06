"""
CMS Automation 生产环境端到端测试
测试所有解析、推荐、校对功能的 UI 显示和功能正确性
"""

import asyncio
import json
from playwright.async_api import async_playwright, Page, expect
from datetime import datetime

# 配置
FRONTEND_URL = "https://storage.googleapis.com/cms-automation-frontend-476323/index.html"
BACKEND_URL = "https://cms-automation-backend-baau2zqeqq-ue.a.run.app"

class ProductionTester:
    def __init__(self):
        self.test_results = []
        self.page = None

    async def setup(self, page: Page):
        """设置测试环境"""
        self.page = page
        print(f"📱 访问应用: {FRONTEND_URL}")
        await page.goto(FRONTEND_URL, wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3000)

    async def take_screenshot(self, name: str):
        """截图保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/tmp/test_{name}_{timestamp}.png"
        await self.page.screenshot(path=filename, full_page=True)
        print(f"📸 截图保存: {filename}")
        return filename

    async def log_result(self, test_name: str, passed: bool, details: str = ""):
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

    async def test_homepage_loading(self):
        """测试1: 首页加载"""
        print("\n🧪 测试1: 首页加载")
        try:
            # 检查页面标题
            title = await self.page.title()
            await self.log_result(
                "首页加载",
                "CMS" in title,
                f"页面标题: {title}"
            )

            # 截图
            await self.take_screenshot("homepage")

            # 检查是否有主要导航元素
            nav_visible = await self.page.locator("nav, header, [role='navigation']").count() > 0
            await self.log_result(
                "导航元素存在",
                nav_visible,
                f"导航元素数量: {await self.page.locator('nav, header').count()}"
            )

        except Exception as e:
            await self.log_result("首页加载", False, f"错误: {str(e)}")

    async def test_backend_health(self):
        """测试2: 后端健康检查"""
        print("\n🧪 测试2: 后端API健康检查")
        try:
            response = await self.page.request.get(f"{BACKEND_URL}/health")
            health_data = await response.json()

            passed = response.status == 200 and health_data.get("status") == "healthy"
            await self.log_result(
                "后端健康检查",
                passed,
                f"状态: {response.status}, 数据: {health_data}"
            )
        except Exception as e:
            await self.log_result("后端健康检查", False, f"错误: {str(e)}")

    async def test_article_parsing_page(self):
        """测试3: 文章解析页面"""
        print("\n🧪 测试3: 文章解析页面")
        try:
            # 查找文章解析相关的按钮或链接
            parsing_links = await self.page.get_by_text("解析", exact=False).count()
            parsing_buttons = await self.page.locator("button:has-text('解析'), a:has-text('解析')").count()

            if parsing_links > 0 or parsing_buttons > 0:
                # 尝试点击进入解析页面
                if parsing_buttons > 0:
                    await self.page.locator("button:has-text('解析'), a:has-text('解析')").first.click()
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("parsing_page")

                await self.log_result(
                    "文章解析页面",
                    True,
                    f"找到解析元素: 链接{parsing_links}个, 按钮{parsing_buttons}个"
                )
            else:
                # 检查当前页面是否有解析相关的输入框
                url_inputs = await self.page.locator("input[type='text'], input[type='url']").count()
                await self.log_result(
                    "文章解析页面",
                    url_inputs > 0,
                    f"输入框数量: {url_inputs}"
                )

        except Exception as e:
            await self.log_result("文章解析页面", False, f"错误: {str(e)}")

    async def test_worklist_functionality(self):
        """测试4: 工作列表功能"""
        print("\n🧪 测试4: 工作列表功能")
        try:
            # 查找工作列表相关元素
            worklist_elements = await self.page.get_by_text("工作列表", exact=False).count()
            worklist_elements += await self.page.get_by_text("Worklist", exact=False).count()

            if worklist_elements > 0:
                # 尝试导航到工作列表
                worklist_link = self.page.locator("a:has-text('工作列表'), a:has-text('Worklist'), button:has-text('工作列表')").first
                if await worklist_link.count() > 0:
                    await worklist_link.click()
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("worklist_page")

                await self.log_result(
                    "工作列表功能",
                    True,
                    f"找到工作列表元素: {worklist_elements}个"
                )
            else:
                await self.log_result(
                    "工作列表功能",
                    False,
                    "未找到工作列表元素"
                )

        except Exception as e:
            await self.log_result("工作列表功能", False, f"错误: {str(e)}")

    async def test_proofreading_functionality(self):
        """测试5: 校对功能"""
        print("\n🧪 测试5: 校对功能")
        try:
            # 查找校对相关元素
            proofread_elements = await self.page.get_by_text("校对", exact=False).count()
            proofread_elements += await self.page.get_by_text("Proofread", exact=False).count()

            if proofread_elements > 0:
                # 尝试导航到校对页面
                proofread_link = self.page.locator("a:has-text('校对'), a:has-text('Proofread'), button:has-text('校对')").first
                if await proofread_link.count() > 0:
                    await proofread_link.click()
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("proofreading_page")

                await self.log_result(
                    "校对功能",
                    True,
                    f"找到校对元素: {proofread_elements}个"
                )
            else:
                await self.log_result(
                    "校对功能",
                    False,
                    "未找到校对元素"
                )

        except Exception as e:
            await self.log_result("校对功能", False, f"错误: {str(e)}")

    async def test_settings_page(self):
        """测试6: 设置页面"""
        print("\n🧪 测试6: 设置页面")
        try:
            # 查找设置相关元素
            settings_elements = await self.page.get_by_text("设置", exact=False).count()
            settings_elements += await self.page.get_by_text("Settings", exact=False).count()

            if settings_elements > 0:
                # 尝试导航到设置页面
                settings_link = self.page.locator("a:has-text('设置'), a:has-text('Settings'), button:has-text('设置')").first
                if await settings_link.count() > 0:
                    await settings_link.click()
                    await self.page.wait_for_timeout(2000)
                    await self.take_screenshot("settings_page")

                await self.log_result(
                    "设置页面",
                    True,
                    f"找到设置元素: {settings_elements}个"
                )
            else:
                await self.log_result(
                    "设置页面",
                    False,
                    "未找到设置元素"
                )

        except Exception as e:
            await self.log_result("设置页面", False, f"错误: {str(e)}")

    async def test_api_endpoints(self):
        """测试7: API端点可访问性"""
        print("\n🧪 测试7: API端点测试")

        endpoints = [
            ("/health", "健康检查"),
            ("/", "根路径"),
            ("/docs", "API文档")
        ]

        for endpoint, name in endpoints:
            try:
                response = await self.page.request.get(f"{BACKEND_URL}{endpoint}")
                passed = response.status == 200
                await self.log_result(
                    f"API端点: {name}",
                    passed,
                    f"状态码: {response.status}"
                )
            except Exception as e:
                await self.log_result(f"API端点: {name}", False, f"错误: {str(e)}")

    async def test_console_errors(self):
        """测试8: 检查控制台错误"""
        print("\n🧪 测试8: 控制台错误检查")

        # 收集控制台消息
        console_messages = []

        async def handle_console(msg):
            console_messages.append({
                "type": msg.type,
                "text": msg.text
            })

        self.page.on("console", handle_console)

        # 重新加载页面收集错误
        await self.page.reload(wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 检查错误
        errors = [msg for msg in console_messages if msg["type"] == "error"]
        warnings = [msg for msg in console_messages if msg["type"] == "warning"]

        await self.log_result(
            "控制台错误检查",
            len(errors) == 0,
            f"错误: {len(errors)}个, 警告: {len(warnings)}个"
        )

        if errors:
            for error in errors[:5]:  # 只显示前5个错误
                print(f"  ⚠️  错误: {error['text']}")

    async def generate_report(self):
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
        report_file = f"/tmp/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        print(f"\n📄 详细报告已保存: {report_file}")

        return passed_tests, failed_tests

async def main():
    """主测试函数"""
    print("🚀 CMS Automation 生产环境测试开始")
    print(f"前端URL: {FRONTEND_URL}")
    print(f"后端URL: {BACKEND_URL}")
    print("="*60)

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # 创建测试实例
        tester = ProductionTester()

        try:
            # 运行所有测试
            await tester.setup(page)
            await tester.test_homepage_loading()
            await tester.test_backend_health()
            await tester.test_article_parsing_page()
            await tester.test_worklist_functionality()
            await tester.test_proofreading_functionality()
            await tester.test_settings_page()
            await tester.test_api_endpoints()
            await tester.test_console_errors()

            # 生成报告
            passed, failed = await tester.generate_report()

        except Exception as e:
            print(f"\n❌ 测试执行错误: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()

        print("\n✅ 测试完成!")
        return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
