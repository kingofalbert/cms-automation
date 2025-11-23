#!/usr/bin/env python3
"""
快速重置卡住的文件 (Item 13 和 6)
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from src.config.settings import get_settings


async def main():
    print("=" * 60)
    print("重置卡住的文件")
    print("=" * 60)
    print()

    settings = get_settings()
    engine = create_async_engine(str(settings.DATABASE_URL), echo=False)

    try:
        # 步骤 1: 检查当前状态
        print("📋 步骤 1: 检查当前状态...")
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT id, title, status, updated_at
                    FROM worklist_items
                    WHERE id IN (13, 6)
                    ORDER BY id
                """)
            )
            items = result.fetchall()

            if not items:
                print("❌ 未找到 ID 为 13 和 6 的文件")
                return

            print()
            print("当前状态:")
            print("-" * 60)
            for item in items:
                print(f"ID: {item[0]}")
                print(f"  标题: {item[1]}")
                print(f"  状态: {item[2]}")
                print(f"  更新时间: {item[3]}")
                print()

        # 步骤 2: 重置状态
        print("🔧 步骤 2: 重置为 pending 状态...")
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    UPDATE worklist_items
                    SET status = 'pending', updated_at = NOW()
                    WHERE id IN (13, 6)
                    RETURNING id, title, status
                """)
            )
            updated = result.fetchall()

            print("✅ 已重置以下文件:")
            for item in updated:
                print(f"  - ID {item[0]}: {item[1]} → {item[2]}")

        # 步骤 3: 验证
        print()
        print("📋 步骤 3: 验证重置结果...")
        async with engine.begin() as conn:
            result = await conn.execute(
                text("""
                    SELECT id, title, status, updated_at
                    FROM worklist_items
                    WHERE id IN (13, 6)
                    ORDER BY id
                """)
            )
            items = result.fetchall()

            print()
            print("重置后状态:")
            print("-" * 60)
            for item in items:
                print(f"ID: {item[0]}")
                print(f"  标题: {item[1]}")
                print(f"  状态: {item[2]}")
                print(f"  更新时间: {item[3]}")
                print()

        print("=" * 60)
        print("✅ 重置完成！")
        print()
        print("下一步:")
        print("1. 等待 1-2 分钟")
        print("2. 检查文件是否从 pending → parsing → parsing_review")
        print("3. 如需监控，运行: python monitor_items.py")
        print("=" * 60)

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        await engine.dispose()

    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))
