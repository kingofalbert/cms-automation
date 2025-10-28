"""
Unit Tests for Computer Use Configuration Loader

测试 Computer Use 指令模板加载器的功能
"""

import pytest
from pathlib import Path
from src.config.computer_use_loader import (
    InstructionTemplate,
    load_instruction_templates,
    ConfigurationError
)


class TestInstructionTemplate:
    """测试 InstructionTemplate 类"""

    @pytest.fixture
    def template_dict(self):
        """测试用的模板字典"""
        return {
            'login_to_wordpress': '登录到 {{ username }} 的账号，密码是 {{ password }}',
            'navigate_to_new_post': '导航到新增文章页面',
            'fill_title': '填写标题: {{ value }}',
            'fill_content': '填写内容: {{ content }}',
            'open_media_library': '打开媒体库',
            'upload_file': '上传文件: {{ file_path }}',
            'fill_image_metadata': '填写图片元数据',
            'insert_image_to_content': '插入图片到文章',
            'set_as_featured_image': '设置为特色图片',
            'add_tag': '添加标签: {{ tag }}',
            'select_category': '选择分类: {{ category }}',
            'click_save_draft': '保存草稿',
            'click_publish': '发布文章',
        }

    @pytest.fixture
    def instruction_template(self, template_dict):
        """InstructionTemplate 实例"""
        return InstructionTemplate(template_dict)

    def test_initialization(self, template_dict):
        """测试初始化"""
        template = InstructionTemplate(template_dict)
        assert template.templates == template_dict
        assert len(template.templates) == len(template_dict)

    def test_get_template_without_variables(self, instruction_template):
        """测试获取无变量的模板"""
        result = instruction_template.get('navigate_to_new_post')
        assert result == '导航到新增文章页面'

    def test_get_template_with_variables(self, instruction_template):
        """测试获取有变量的模板"""
        result = instruction_template.get('fill_title', value='测试标题')
        assert result == '填写标题: 测试标题'

    def test_get_template_with_multiple_variables(self, instruction_template):
        """测试获取多个变量的模板"""
        result = instruction_template.get(
            'login_to_wordpress',
            username='admin',
            password='password123'
        )
        assert result == '登录到 admin 的账号，密码是 password123'

    def test_get_template_missing_key(self, instruction_template):
        """测试获取不存在的模板"""
        with pytest.raises(KeyError) as exc_info:
            instruction_template.get('nonexistent_template')
        assert 'nonexistent_template' in str(exc_info.value)
        assert '可用的模板' in str(exc_info.value)

    def test_get_template_missing_variable(self, instruction_template):
        """测试缺少必需变量"""
        with pytest.raises(KeyError) as exc_info:
            instruction_template.get('fill_title')  # 缺少 value 参数
        assert '缺少必需的变量' in str(exc_info.value)

    def test_has_template(self, instruction_template):
        """测试检查模板是否存在"""
        assert instruction_template.has('fill_title') is True
        assert instruction_template.has('nonexistent') is False

    def test_list_templates(self, instruction_template):
        """测试列出所有模板"""
        templates = instruction_template.list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert 'fill_title' in templates
        assert templates == sorted(templates)  # 应该已排序

    def test_get_template_info(self, instruction_template):
        """测试获取模板信息"""
        info = instruction_template.get_template_info('fill_title')
        assert info is not None
        assert info['name'] == 'fill_title'
        assert 'value' in info['variables']
        assert info['length'] > 0
        assert info['line_count'] >= 1

    def test_get_template_info_nonexistent(self, instruction_template):
        """测试获取不存在模板的信息"""
        info = instruction_template.get_template_info('nonexistent')
        assert info is None

    def test_validate_template_variables(self, instruction_template):
        """测试验证模板变量"""
        # 提供所有必需变量
        is_valid, missing = instruction_template.validate_template_variables(
            'fill_title',
            value='test'
        )
        assert is_valid is True
        assert len(missing) == 0

        # 缺少变量
        is_valid, missing = instruction_template.validate_template_variables(
            'fill_title'
        )
        assert is_valid is False
        assert 'value' in missing

    def test_validate_required_templates_success(self, template_dict):
        """测试验证必需模板 - 成功"""
        # 所有必需模板都存在
        template = InstructionTemplate(template_dict)
        assert template.templates == template_dict

    def test_validate_required_templates_failure(self):
        """测试验证必需模板 - 失败"""
        # 缺少必需模板
        incomplete_dict = {
            'fill_title': 'test',
            'fill_content': 'test',
        }

        with pytest.raises(ValueError) as exc_info:
            InstructionTemplate(incomplete_dict)
        assert '缺少必需的模板' in str(exc_info.value)

    def test_repr_and_str(self, instruction_template):
        """测试字符串表示"""
        repr_str = repr(instruction_template)
        str_str = str(instruction_template)

        assert 'InstructionTemplate' in repr_str
        assert str(len(instruction_template.templates)) in repr_str

        assert 'InstructionTemplate' in str_str


class TestLoadFromFile:
    """测试从文件加载模板"""

    def test_load_instruction_templates_default_path(self):
        """测试使用默认路径加载模板"""
        # 假设默认路径的文件存在
        try:
            template = load_instruction_templates()
            assert template is not None
            assert len(template.templates) > 0
            assert template.has('login_to_wordpress')
            assert template.has('navigate_to_new_post')
        except ConfigurationError:
            pytest.skip("默认配置文件不存在")

    def test_load_instruction_templates_custom_path(self):
        """测试使用自定义路径加载模板"""
        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'computer_use_instructions.yaml'

        if not config_path.exists():
            pytest.skip("配置文件不存在")

        template = load_instruction_templates(str(config_path))
        assert template is not None
        assert len(template.templates) > 0

    def test_load_from_nonexistent_file(self):
        """测试加载不存在的文件"""
        with pytest.raises(ConfigurationError):
            load_instruction_templates('/nonexistent/path/config.yaml')

    def test_load_from_file_with_actual_config(self):
        """测试加载实际的配置文件"""
        # 找到实际的配置文件
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'computer_use_instructions.yaml'

        if not config_path.exists():
            pytest.skip("配置文件不存在")

        template = InstructionTemplate.load_from_file(str(config_path))

        # 验证加载的模板包含所有必需的指令
        required_instructions = [
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

        for instruction in required_instructions:
            assert template.has(instruction), f"缺少必需指令: {instruction}"

    def test_template_rendering_with_actual_config(self):
        """测试使用实际配置进行模板渲染"""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'computer_use_instructions.yaml'

        if not config_path.exists():
            pytest.skip("配置文件不存在")

        template = InstructionTemplate.load_from_file(str(config_path))

        # 测试登录指令
        login_instruction = template.get(
            'login_to_wordpress',
            username='test_user',
            password='test_password'
        )
        assert 'test_user' in login_instruction
        assert 'test_password' in login_instruction

        # 测试填写标题指令
        title_instruction = template.get(
            'fill_title',
            value='测试文章标题'
        )
        assert '测试文章标题' in title_instruction

    def test_template_variables_extraction(self):
        """测试从实际配置中提取变量"""
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / 'config' / 'computer_use_instructions.yaml'

        if not config_path.exists():
            pytest.skip("配置文件不存在")

        template = InstructionTemplate.load_from_file(str(config_path))

        # 检查 login_to_wordpress 的变量
        info = template.get_template_info('login_to_wordpress')
        assert 'username' in info['variables']
        assert 'password' in info['variables']

        # 检查 fill_title 的变量
        info = template.get_template_info('fill_title')
        assert 'value' in info['variables']

        # 检查 fill_content 的变量
        info = template.get_template_info('fill_content')
        assert 'content' in info['variables']


class TestEdgeCases:
    """测试边界情况"""

    def test_template_with_whitespace_in_variables(self):
        """测试变量名周围有空格的情况"""
        templates = {
            'test': '填写 {{  value  }} 的内容',  # 变量名周围有空格
            'login_to_wordpress': 'test',
            'navigate_to_new_post': 'test',
            'fill_title': 'test',
            'fill_content': 'test',
            'open_media_library': 'test',
            'upload_file': 'test',
            'fill_image_metadata': 'test',
            'insert_image_to_content': 'test',
            'set_as_featured_image': 'test',
            'add_tag': 'test',
            'select_category': 'test',
            'click_save_draft': 'test',
            'click_publish': 'test',
        }
        template = InstructionTemplate(templates)

        # 应该能正确解析并替换
        result = template.get('test', value='测试')
        assert result == '填写 测试 的内容'

    def test_template_with_chinese_content(self):
        """测试包含中文的模板"""
        templates = {
            'test_chinese': '這是繁體中文模板：{{ title }}',
            'login_to_wordpress': 'test',
            'navigate_to_new_post': 'test',
            'fill_title': 'test',
            'fill_content': 'test',
            'open_media_library': 'test',
            'upload_file': 'test',
            'fill_image_metadata': 'test',
            'insert_image_to_content': 'test',
            'set_as_featured_image': 'test',
            'add_tag': 'test',
            'select_category': 'test',
            'click_save_draft': 'test',
            'click_publish': 'test',
        }
        template = InstructionTemplate(templates)

        result = template.get('test_chinese', title='測試標題')
        assert result == '這是繁體中文模板：測試標題'
        assert '繁體中文' in result

    def test_template_with_multiline_content(self):
        """测试多行模板"""
        templates = {
            'multiline': '''第一行
第二行：{{ value }}
第三行''',
            'login_to_wordpress': 'test',
            'navigate_to_new_post': 'test',
            'fill_title': 'test',
            'fill_content': 'test',
            'open_media_library': 'test',
            'upload_file': 'test',
            'fill_image_metadata': 'test',
            'insert_image_to_content': 'test',
            'set_as_featured_image': 'test',
            'add_tag': 'test',
            'select_category': 'test',
            'click_save_draft': 'test',
            'click_publish': 'test',
        }
        template = InstructionTemplate(templates)

        result = template.get('multiline', value='测试')
        assert '第一行' in result
        assert '第二行：测试' in result
        assert '第三行' in result
        assert result.count('\n') == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
