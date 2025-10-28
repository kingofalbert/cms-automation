"""
Computer Use Instruction Template Loader

This module provides functionality to load and manage Computer Use instruction templates
from YAML configuration files.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class InstructionTemplate:
    """Computer Use 指令模板管理器"""

    def __init__(self, templates: Dict[str, str]):
        """
        初始化指令模板

        Args:
            templates: 指令模板字典 {instruction_name: template_string}
        """
        self.templates = templates
        self._validate_required_templates()

    @classmethod
    def load_from_file(cls, file_path: str) -> 'InstructionTemplate':
        """
        从 YAML 文件加载指令模板

        Args:
            file_path: YAML 配置文件路径

        Returns:
            InstructionTemplate 实例

        Raises:
            FileNotFoundError: 文件不存在
            yaml.YAMLError: YAML 格式错误
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f'指令模板文件不存在: {file_path}')

        if not path.is_file():
            raise ValueError(f'路径不是文件: {file_path}')

        try:
            with open(path, 'r', encoding='utf-8') as f:
                templates = yaml.safe_load(f)

            if not isinstance(templates, dict):
                raise ValueError(f'指令模板文件格式错误：应该是字典格式')

            logger.info(f"成功加载 {len(templates)} 个指令模板 from {file_path}")
            return cls(templates)

        except yaml.YAMLError as e:
            logger.error(f"YAML 解析错误: {e}")
            raise

    def get(self, key: str, **kwargs) -> str:
        """
        获取并渲染指令模板

        Args:
            key: 模板键名
            **kwargs: 模板变量（用于替换 {{ variable }} 格式的占位符）

        Returns:
            渲染后的指令字符串

        Raises:
            KeyError: 模板不存在
            KeyError: 缺少必需的模板变量
        """
        template = self.templates.get(key)

        if template is None:
            available_keys = ", ".join(sorted(self.templates.keys()))
            raise KeyError(
                f'指令模板 "{key}" 不存在。\n'
                f'可用的模板: {available_keys}'
            )

        # 使用简单的字符串格式化替换变量
        # 支持 {{ variable }} 格式（带或不带空格）
        try:
            # 将 {{ var }} 转换为 {var} 格式，以便使用 str.format()
            # 使用正则表达式处理，去除变量名周围的空格
            import re
            formatted_template = re.sub(r'\{\{\s*(\w+)\s*\}\}', r'{\1}', template)
            return formatted_template.format(**kwargs)

        except KeyError as e:
            missing_var = str(e).strip("'")
            raise KeyError(
                f'指令模板 "{key}" 缺少必需的变量: {missing_var}\n'
                f'提供的变量: {", ".join(kwargs.keys())}'
            )

    def has(self, key: str) -> bool:
        """
        检查指令模板是否存在

        Args:
            key: 模板键名

        Returns:
            True 如果模板存在，否则 False
        """
        return key in self.templates

    def list_templates(self) -> list[str]:
        """
        列出所有可用的模板键名

        Returns:
            模板键名列表（已排序）
        """
        return sorted(self.templates.keys())

    def _validate_required_templates(self) -> None:
        """
        验证必需的模板是否存在

        Raises:
            ValueError: 缺少必需的模板
        """
        # 定义核心必需的模板
        required_templates = [
            'login_to_wordpress',
            'navigate_to_new_post',
            'fill_title',
            'fill_content',
            'open_media_library',
            'upload_file',
            'fill_image_metadata',
            'insert_image_to_content',
            'set_as_featured_image',
            'add_tag',
            'select_category',
            'click_save_draft',
            'click_publish',
        ]

        missing = [key for key in required_templates if key not in self.templates]

        if missing:
            raise ValueError(
                f'指令模板文件缺少必需的模板: {", ".join(missing)}\n'
                f'请确保 YAML 文件包含所有核心操作模板'
            )

        logger.debug(f"模板验证通过：所有 {len(required_templates)} 个必需模板都存在")

    def get_template_info(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取模板的详细信息

        Args:
            key: 模板键名

        Returns:
            模板信息字典，包含:
            - name: 模板名称
            - content: 模板内容
            - variables: 模板中使用的变量列表
            - length: 模板内容长度

            如果模板不存在返回 None
        """
        if not self.has(key):
            return None

        template_content = self.templates[key]

        # 提取模板中的变量（简单的正则匹配 {{ var }} 格式）
        import re
        variables = re.findall(r'\{\{\s*(\w+)\s*\}\}', template_content)

        return {
            'name': key,
            'content': template_content,
            'variables': list(set(variables)),  # 去重
            'length': len(template_content),
            'line_count': template_content.count('\n') + 1
        }

    def validate_template_variables(self, key: str, **kwargs) -> tuple[bool, list[str]]:
        """
        验证提供的变量是否满足模板需求

        Args:
            key: 模板键名
            **kwargs: 要验证的变量

        Returns:
            (is_valid, missing_variables)
            - is_valid: True 如果所有必需变量都提供了
            - missing_variables: 缺少的变量列表

        Raises:
            KeyError: 模板不存在
        """
        info = self.get_template_info(key)

        if info is None:
            raise KeyError(f'模板 "{key}" 不存在')

        required_vars = set(info['variables'])
        provided_vars = set(kwargs.keys())

        missing = list(required_vars - provided_vars)

        return (len(missing) == 0, missing)

    def __repr__(self) -> str:
        return f'<InstructionTemplate: {len(self.templates)} templates>'

    def __str__(self) -> str:
        templates_list = ", ".join(self.list_templates()[:5])
        more = f" ... ({len(self.templates) - 5} more)" if len(self.templates) > 5 else ""
        return f'InstructionTemplate({templates_list}{more})'


class ConfigurationError(Exception):
    """配置错误异常"""
    pass


def load_instruction_templates(config_path: Optional[str] = None) -> InstructionTemplate:
    """
    便捷函数：加载指令模板

    Args:
        config_path: 配置文件路径，如果为 None 则使用默认路径

    Returns:
        InstructionTemplate 实例

    Raises:
        ConfigurationError: 配置加载失败
    """
    if config_path is None:
        # 使用默认路径：相对于项目根目录
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'computer_use_instructions.yaml'

    try:
        return InstructionTemplate.load_from_file(str(config_path))
    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
        raise ConfigurationError(f'加载指令模板失败: {e}') from e


# 测试函数（仅用于开发验证）
def _test_template_loader():
    """测试模板加载器（内部使用）"""
    try:
        templates = load_instruction_templates()
        print(f"✅ 成功加载模板: {templates}")
        print(f"📋 可用模板列表:")

        for name in templates.list_templates():
            info = templates.get_template_info(name)
            vars_str = f"变量: {', '.join(info['variables'])}" if info['variables'] else "无变量"
            print(f"  - {name} ({info['line_count']} 行, {vars_str})")

        # 测试模板渲染
        print("\n🧪 测试模板渲染:")
        rendered = templates.get('fill_title', value='测试文章标题')
        print(f"  fill_title: {rendered[:100]}...")

    except Exception as e:
        print(f"❌ 测试失败: {e}")


if __name__ == '__main__':
    _test_template_loader()
