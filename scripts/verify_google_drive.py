#!/usr/bin/env python3
"""
验证 Google Drive 集成配置
验证服务账号凭证和文件夹访问权限
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def main():
    """验证 Google Drive 配置"""

    print("🔍 Google Drive 配置验证工具\n")
    print("=" * 60)

    # 1. 检查凭证文件
    print("\n1️⃣ 检查凭证文件...")
    credentials_path = project_root / "backend" / "credentials" / "google-drive-credentials.json"

    if not credentials_path.exists():
        print(f"❌ 凭证文件不存在: {credentials_path}")
        print("   请运行: gcloud iam service-accounts keys create ...")
        return False

    print(f"✅ 凭证文件存在: {credentials_path}")

    # 检查文件权限
    import stat
    file_stat = credentials_path.stat()
    file_mode = stat.filemode(file_stat.st_mode)
    print(f"   权限: {file_mode}")

    if file_stat.st_mode & 0o077:
        print("⚠️  警告: 文件权限过于宽松，建议设置为 600")
        print("   运行: chmod 600", credentials_path)

    # 2. 加载凭证
    print("\n2️⃣ 加载服务账号凭证...")
    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=['https://www.googleapis.com/auth/drive']
        )
        print(f"✅ 服务账号: {credentials.service_account_email}")
        print(f"   项目 ID: {credentials.project_id}")
    except Exception as e:
        print(f"❌ 加载凭证失败: {e}")
        return False

    # 3. 初始化 Drive 服务
    print("\n3️⃣ 初始化 Google Drive 服务...")
    try:
        service = build('drive', 'v3', credentials=credentials)
        print("✅ Google Drive 服务初始化成功")
    except Exception as e:
        print(f"❌ 初始化服务失败: {e}")
        return False

    # 4. 测试文件夹访问
    print("\n4️⃣ 测试文件夹访问...")
    folder_id = "1r4YwLr-58AvVl3e7TW5zqWn0X95-3EcG"
    print(f"   文件夹 ID: {folder_id}")

    try:
        # 获取文件夹元数据
        folder = service.files().get(
            fileId=folder_id,
            fields='id, name, mimeType, permissions'
        ).execute()

        print(f"✅ 文件夹访问成功")
        print(f"   名称: {folder.get('name')}")
        print(f"   类型: {folder.get('mimeType')}")

    except HttpError as e:
        if e.resp.status == 404:
            print(f"❌ 文件夹不存在或无权访问")
            print(f"   错误: {e}")
            print("\n💡 解决方案:")
            print(f"   1. 访问: https://drive.google.com/drive/folders/{folder_id}")
            print(f"   2. 点击 '共享' 按钮")
            print(f"   3. 添加服务账号: {credentials.service_account_email}")
            print(f"   4. 设置权限为 '编辑者 (Editor)'")
            return False
        else:
            print(f"❌ 访问文件夹时出错: {e}")
            return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

    # 5. 列出文件夹内容
    print("\n5️⃣ 列出文件夹内容...")
    try:
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            pageSize=10,
            fields="files(id, name, mimeType, createdTime)"
        ).execute()

        files = results.get('files', [])

        if not files:
            print("⚠️  文件夹为空")
        else:
            print(f"✅ 找到 {len(files)} 个文件:")
            for file in files:
                print(f"   - {file['name']} ({file['mimeType']})")

    except Exception as e:
        print(f"❌ 列出文件失败: {e}")
        return False

    # 6. 测试上传权限
    print("\n6️⃣ 测试上传权限...")
    try:
        # 创建一个测试文件元数据（不实际创建文件，只检查权限）
        file_metadata = {
            'name': '__test_permission__.txt',
            'parents': [folder_id]
        }

        from io import BytesIO
        from googleapiclient.http import MediaIoBaseUpload

        media = MediaIoBaseUpload(
            BytesIO(b'test content'),
            mimetype='text/plain',
            resumable=True
        )

        test_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name'
        ).execute()

        print(f"✅ 上传权限正常")
        print(f"   创建测试文件: {test_file['name']}")

        # 删除测试文件
        service.files().delete(fileId=test_file['id']).execute()
        print(f"   已清理测试文件")

    except HttpError as e:
        if e.resp.status == 403:
            print(f"❌ 没有上传权限")
            print(f"   错误: {e}")
            print("\n💡 解决方案:")
            print(f"   确保服务账号具有 '编辑者 (Editor)' 权限，而不是 '查看者 (Viewer)'")
            return False
        else:
            print(f"❌ 测试上传时出错: {e}")
            return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

    # 验证完成
    print("\n" + "=" * 60)
    print("✅ 所有验证通过！Google Drive 集成配置正确。")
    print("\n📋 配置摘要:")
    print(f"   服务账号: {credentials.service_account_email}")
    print(f"   项目 ID: {credentials.project_id}")
    print(f"   文件夹 ID: {folder_id}")
    print(f"   文件夹 URL: https://drive.google.com/drive/folders/{folder_id}")
    print("\n🚀 现在可以使用 Google Drive 功能了！")

    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  验证被中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
