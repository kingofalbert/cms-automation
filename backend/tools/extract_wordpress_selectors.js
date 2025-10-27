/**
 * WordPress CSS选择器提取工具
 *
 * 使用方法：
 * 1. 登录你的WordPress后台
 * 2. 打开浏览器开发者工具 (F12)
 * 3. 切换到Console标签
 * 4. 复制粘贴这整个脚本并回车
 * 5. 按照提示操作，脚本会自动记录所有CSS选择器
 * 6. 完成后，复制输出的JSON配置
 */

(function() {
    console.log('🚀 WordPress选择器提取工具已启动');
    console.log('📋 请按照提示操作，我会记录所有元素的CSS选择器\n');

    const selectors = {
        metadata: {
            wordpress_version: null,
            editor_type: null,
            seo_plugin: null,
            theme: null,
            extracted_at: new Date().toISOString(),
        },
        login: {},
        dashboard: {},
        editor: {},
        media: {},
        seo: {},
        publish: {},
    };

    // 检测WordPress版本
    function detectWordPressVersion() {
        const generator = document.querySelector('meta[name="generator"]');
        if (generator) {
            selectors.metadata.wordpress_version = generator.content;
        }
    }

    // 检测编辑器类型
    function detectEditorType() {
        if (document.querySelector('.block-editor')) {
            selectors.metadata.editor_type = 'Gutenberg';
        } else if (document.querySelector('#wp-content-editor-container')) {
            selectors.metadata.editor_type = 'Classic Editor';
        } else if (document.querySelector('.elementor-editor-active')) {
            selectors.metadata.editor_type = 'Elementor';
        }
    }

    // 检测SEO插件
    function detectSEOPlugin() {
        if (document.querySelector('#wpseo-metabox-root')) {
            selectors.metadata.seo_plugin = 'Yoast SEO';
        } else if (document.querySelector('.rank-math-editor')) {
            selectors.metadata.seo_plugin = 'Rank Math';
        } else if (document.querySelector('#aioseo-post-settings')) {
            selectors.metadata.seo_plugin = 'All in One SEO';
        }
    }

    // 获取元素的最优CSS选择器
    function getBestSelector(element) {
        if (!element) return null;

        // 优先级：id > name > class > xpath
        if (element.id) {
            return `#${element.id}`;
        }

        if (element.name) {
            return `[name="${element.name}"]`;
        }

        if (element.className && typeof element.className === 'string') {
            const classes = element.className.trim().split(/\s+/).filter(c => c);
            if (classes.length > 0) {
                return `.${classes.join('.')}`;
            }
        }

        // 使用Chrome DevTools的copy selector功能
        if (window.getSelection && window.getSelection().toString() === '') {
            // 生成CSS路径
            const path = [];
            let current = element;
            while (current && current.nodeType === Node.ELEMENT_NODE) {
                let selector = current.nodeName.toLowerCase();
                if (current.id) {
                    selector += `#${current.id}`;
                    path.unshift(selector);
                    break;
                } else {
                    let sibling = current;
                    let nth = 1;
                    while (sibling.previousElementSibling) {
                        sibling = sibling.previousElementSibling;
                        if (sibling.nodeName.toLowerCase() === selector) nth++;
                    }
                    if (nth > 1) selector += `:nth-of-type(${nth})`;
                }
                path.unshift(selector);
                current = current.parentElement;
            }
            return path.join(' > ');
        }

        return null;
    }

    // 高亮元素
    function highlightElement(element, label) {
        if (!element) return;

        element.style.outline = '3px solid red';
        element.style.outlineOffset = '2px';

        const labelDiv = document.createElement('div');
        labelDiv.textContent = label;
        labelDiv.style.cssText = `
            position: absolute;
            background: red;
            color: white;
            padding: 2px 5px;
            font-size: 12px;
            font-weight: bold;
            z-index: 99999;
            pointer-events: none;
        `;

        const rect = element.getBoundingClientRect();
        labelDiv.style.top = (window.scrollY + rect.top - 25) + 'px';
        labelDiv.style.left = (window.scrollX + rect.left) + 'px';

        document.body.appendChild(labelDiv);

        setTimeout(() => {
            element.style.outline = '';
            labelDiv.remove();
        }, 3000);
    }

    // 步骤1：登录页面元素
    function step1_extractLoginSelectors() {
        console.log('\n📍 步骤1：提取登录页面元素');
        console.log('请访问登录页面 (如果还没有退出登录)');
        console.log('然后运行：step1_complete()\n');

        window.step1_complete = function() {
            const usernameField = document.querySelector('#user_login, input[name="log"]');
            const passwordField = document.querySelector('#user_pass, input[name="pwd"]');
            const submitButton = document.querySelector('#wp-submit, input[type="submit"]');

            if (usernameField) {
                selectors.login.username_field = getBestSelector(usernameField);
                highlightElement(usernameField, 'Username');
                console.log('✅ 用户名字段:', selectors.login.username_field);
            }

            if (passwordField) {
                selectors.login.password_field = getBestSelector(passwordField);
                highlightElement(passwordField, 'Password');
                console.log('✅ 密码字段:', selectors.login.password_field);
            }

            if (submitButton) {
                selectors.login.submit_button = getBestSelector(submitButton);
                highlightElement(submitButton, 'Submit');
                console.log('✅ 登录按钮:', selectors.login.submit_button);
            }

            console.log('\n继续下一步：step2_extractDashboardSelectors()');
        };
    }

    // 步骤2：仪表盘元素
    function step2_extractDashboardSelectors() {
        console.log('\n📍 步骤2：提取仪表盘元素');
        console.log('请确保在WordPress仪表盘页面');
        console.log('然后运行：step2_complete()\n');

        window.step2_complete = function() {
            const postsMenu = document.querySelector('#menu-posts');
            const newPostLink = document.querySelector('#menu-posts a[href*="post-new"]');

            if (postsMenu) {
                selectors.dashboard.posts_menu = getBestSelector(postsMenu);
                highlightElement(postsMenu, 'Posts Menu');
                console.log('✅ 文章菜单:', selectors.dashboard.posts_menu);
            }

            if (newPostLink) {
                selectors.dashboard.new_post_link = getBestSelector(newPostLink);
                highlightElement(newPostLink, 'New Post');
                console.log('✅ 新建文章链接:', selectors.dashboard.new_post_link);
            }

            console.log('\n继续下一步：step3_extractEditorSelectors()');
            console.log('请先点击"新建文章"，等编辑器加载完成后运行step3_complete()');
        };
    }

    // 步骤3：编辑器元素
    function step3_extractEditorSelectors() {
        console.log('\n📍 步骤3：提取编辑器元素');
        console.log('请确保在文章编辑页面，编辑器已完全加载');
        console.log('然后运行：step3_complete()\n');

        window.step3_complete = function() {
            detectEditorType();
            console.log(`📝 检测到编辑器类型: ${selectors.metadata.editor_type}`);

            // Gutenberg编辑器
            if (selectors.metadata.editor_type === 'Gutenberg') {
                const titleField = document.querySelector('.editor-post-title__input, .wp-block-post-title');
                const contentArea = document.querySelector('.block-editor-default-block-appender__content, .block-editor-writing-flow');
                const addBlockButton = document.querySelector('.block-editor-inserter__toggle, .edit-post-header-toolbar__inserter-toggle');
                const publishButton = document.querySelector('.editor-post-publish-button, .editor-post-publish-panel__toggle');

                if (titleField) {
                    selectors.editor.title_field = getBestSelector(titleField);
                    highlightElement(titleField, 'Title');
                    console.log('✅ 标题字段:', selectors.editor.title_field);
                }

                if (contentArea) {
                    selectors.editor.content_area = getBestSelector(contentArea);
                    highlightElement(contentArea, 'Content');
                    console.log('✅ 内容区域:', selectors.editor.content_area);
                }

                if (addBlockButton) {
                    selectors.editor.add_block_button = getBestSelector(addBlockButton);
                    highlightElement(addBlockButton, 'Add Block');
                    console.log('✅ 添加块按钮:', selectors.editor.add_block_button);
                }

                if (publishButton) {
                    selectors.publish.publish_button = getBestSelector(publishButton);
                    highlightElement(publishButton, 'Publish');
                    console.log('✅ 发布按钮:', selectors.publish.publish_button);
                }
            }

            // Classic Editor
            else if (selectors.metadata.editor_type === 'Classic Editor') {
                const titleField = document.querySelector('#title');
                const contentArea = document.querySelector('#content');
                const publishButton = document.querySelector('#publish');

                if (titleField) {
                    selectors.editor.title_field = getBestSelector(titleField);
                    console.log('✅ 标题字段:', selectors.editor.title_field);
                }

                if (contentArea) {
                    selectors.editor.content_area = getBestSelector(contentArea);
                    console.log('✅ 内容区域:', selectors.editor.content_area);
                }

                if (publishButton) {
                    selectors.publish.publish_button = getBestSelector(publishButton);
                    console.log('✅ 发布按钮:', selectors.publish.publish_button);
                }
            }

            console.log('\n继续下一步：step4_extractMediaSelectors()');
            console.log('请点击"添加媒体"或"添加块"→"图片"，然后运行step4_complete()');
        };
    }

    // 步骤4：媒体上传元素
    function step4_extractMediaSelectors() {
        console.log('\n📍 步骤4：提取媒体上传元素');
        console.log('请打开媒体上传对话框');
        console.log('然后运行：step4_complete()\n');

        window.step4_complete = function() {
            const uploadButton = document.querySelector('.media-button-select, .components-button.is-primary');
            const mediaFrame = document.querySelector('.media-frame, .media-modal');

            if (uploadButton) {
                selectors.media.upload_button = getBestSelector(uploadButton);
                highlightElement(uploadButton, 'Upload');
                console.log('✅ 上传按钮:', selectors.media.upload_button);
            }

            if (mediaFrame) {
                selectors.media.media_frame = getBestSelector(mediaFrame);
                console.log('✅ 媒体框架:', selectors.media.media_frame);
            }

            console.log('\n继续下一步：step5_extractSEOSelectors()');
            console.log('请向下滚动找到SEO插件面板，然后运行step5_complete()');
        };
    }

    // 步骤5：SEO插件元素
    function step5_extractSEOSelectors() {
        console.log('\n📍 步骤5：提取SEO插件元素');
        console.log('请确保SEO插件面板可见');
        console.log('然后运行：step5_complete()\n');

        window.step5_complete = function() {
            detectSEOPlugin();
            console.log(`🔍 检测到SEO插件: ${selectors.metadata.seo_plugin}`);

            // Yoast SEO
            if (selectors.metadata.seo_plugin === 'Yoast SEO') {
                const focusKeyword = document.querySelector('#yoast-google-preview-focus-keyword, input[name="yoast_wpseo_focuskw"]');
                const metaDescription = document.querySelector('#yoast-google-preview-description, textarea[name="yoast_wpseo_metadesc"]');
                const seoPanel = document.querySelector('#wpseo-metabox-root, .yoast-seo');

                if (focusKeyword) {
                    selectors.seo.focus_keyword_field = getBestSelector(focusKeyword);
                    highlightElement(focusKeyword, 'Focus Keyword');
                    console.log('✅ Focus Keyword字段:', selectors.seo.focus_keyword_field);
                }

                if (metaDescription) {
                    selectors.seo.meta_description_field = getBestSelector(metaDescription);
                    highlightElement(metaDescription, 'Meta Description');
                    console.log('✅ Meta Description字段:', selectors.seo.meta_description_field);
                }

                if (seoPanel) {
                    selectors.seo.panel = getBestSelector(seoPanel);
                    console.log('✅ SEO面板:', selectors.seo.panel);
                }
            }

            // Rank Math
            else if (selectors.metadata.seo_plugin === 'Rank Math') {
                const focusKeyword = document.querySelector('.rank-math-focus-keyword input');
                const metaDescription = document.querySelector('.rank-math-meta-description textarea');

                if (focusKeyword) {
                    selectors.seo.focus_keyword_field = getBestSelector(focusKeyword);
                    console.log('✅ Focus Keyword字段:', selectors.seo.focus_keyword_field);
                }

                if (metaDescription) {
                    selectors.seo.meta_description_field = getBestSelector(metaDescription);
                    console.log('✅ Meta Description字段:', selectors.seo.meta_description_field);
                }
            }

            console.log('\n🎉 所有选择器提取完成！');
            console.log('运行 showResults() 查看完整配置');
        };
    }

    // 显示最终结果
    window.showResults = function() {
        console.log('\n' + '='.repeat(60));
        console.log('📊 WordPress选择器配置 (完整JSON)');
        console.log('='.repeat(60) + '\n');

        const jsonOutput = JSON.stringify(selectors, null, 2);
        console.log(jsonOutput);

        console.log('\n' + '='.repeat(60));
        console.log('✅ 请复制上面的JSON配置');
        console.log('📧 发送给开发人员用于配置Playwright脚本');
        console.log('='.repeat(60));

        // 自动复制到剪贴板
        if (navigator.clipboard) {
            navigator.clipboard.writeText(jsonOutput).then(() => {
                console.log('\n✨ 已自动复制到剪贴板！');
            });
        }

        return selectors;
    };

    // 开始提取流程
    console.log('🎯 开始提取流程：');
    console.log('\n选项1：自动检测当前页面');
    console.log('  运行：autoDetect()');
    console.log('\n选项2：手动分步提取（推荐）');
    console.log('  第1步：step1_extractLoginSelectors()');
    console.log('  第2步：step2_extractDashboardSelectors()');
    console.log('  第3步：step3_extractEditorSelectors()');
    console.log('  第4步：step4_extractMediaSelectors()');
    console.log('  第5步：step5_extractSEOSelectors()');
    console.log('  完成后：showResults()');

    // 自动检测
    window.autoDetect = function() {
        console.log('🔍 自动检测当前页面...\n');

        detectWordPressVersion();
        detectEditorType();
        detectSEOPlugin();

        // 检测当前页面类型
        const currentUrl = window.location.href;

        if (currentUrl.includes('wp-login.php')) {
            console.log('📍 检测到：登录页面');
            step1_extractLoginSelectors();
            setTimeout(() => window.step1_complete(), 1000);
        } else if (currentUrl.includes('wp-admin') && !currentUrl.includes('post')) {
            console.log('📍 检测到：仪表盘');
            step2_extractDashboardSelectors();
            setTimeout(() => window.step2_complete(), 1000);
        } else if (currentUrl.includes('post-new.php') || currentUrl.includes('post.php')) {
            console.log('📍 检测到：编辑器页面');
            step3_extractEditorSelectors();
            setTimeout(() => window.step3_complete(), 1000);
        }

        setTimeout(() => {
            console.log('\n⚠️ 自动检测只能提取当前页面的元素');
            console.log('建议使用手动分步提取获取完整配置');
        }, 2000);
    };

    // 暴露全局函数
    window.step1_extractLoginSelectors = step1_extractLoginSelectors;
    window.step2_extractDashboardSelectors = step2_extractDashboardSelectors;
    window.step3_extractEditorSelectors = step3_extractEditorSelectors;
    window.step4_extractMediaSelectors = step4_extractMediaSelectors;
    window.step5_extractSEOSelectors = step5_extractSEOSelectors;

    console.log('\n✨ 工具加载完成！选择一个选项开始吧！\n');
})();
