"""P2 tests: Google Doc HTML parser alignment.

Tests that the parser correctly handles actual Google Doc export HTML format:
- HTML entities (&#9552; for ═)
- Content wrapped in <span class="..."> inside <p class="..."> and <h2 class="...">
- Multi-line Meta+AEO fields
- Multi-paragraph proofreading format (原文/建議/說明 on separate lines)
- Image alt text with 圖片連結：prefix on separate lines
"""

import pytest

from src.services.parser.article_parser import (
    _normalize_gdoc_html,
    _extract_metadata_sections,
    _clean_metadata_sections_from_body,
    _parse_proofreading_section,
    _parse_meta_aeo_section,
    _parse_image_alt_text_section,
)


class TestNormalizeGdocHtml:
    """Tests for _normalize_gdoc_html helper."""

    def test_decode_html_entities(self):
        html = '<p>&#9552;&#9552;&#9552;&#9552;&#9552;</p>'
        result = _normalize_gdoc_html(html)
        assert '═════' in result

    def test_decode_fullwidth_colon_entity(self):
        html = '<p>AEO&#65306;C</p>'
        result = _normalize_gdoc_html(html)
        assert 'AEO：C' in result

    def test_decode_nbsp(self):
        html = '<p>Hello&nbsp;World</p>'
        result = _normalize_gdoc_html(html)
        assert 'Hello' in result
        assert 'World' in result

    def test_unwrap_span_tags(self):
        html = '<p class="c3"><span class="c0">Hello World</span></p>'
        result = _normalize_gdoc_html(html)
        assert '<span' not in result
        assert 'Hello World' in result

    def test_strip_class_id_from_p_and_h2(self):
        html = '<p class="c3" id="h.123">Content</p><h2 class="c5">Title</h2>'
        result = _normalize_gdoc_html(html)
        assert '<p>Content</p>' in result
        assert '<h2>Title</h2>' in result

    def test_full_gdoc_normalization(self):
        """Test the complete normalization pipeline with realistic Google Doc HTML."""
        html = '<p class="c3"><span class="c0">&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;</span></p>'
        result = _normalize_gdoc_html(html)
        assert result == '<p>════════</p>'

    def test_preserves_non_span_content(self):
        html = '<p>Plain text</p>'
        result = _normalize_gdoc_html(html)
        assert '<p>Plain text</p>' in result

    def test_handles_empty_input(self):
        assert _normalize_gdoc_html('') == ''
        assert _normalize_gdoc_html(None) is None

    def test_nested_spans(self):
        html = '<p class="c1"><span class="c2"><span class="c3">Deep</span> text</span></p>'
        result = _normalize_gdoc_html(html)
        assert '<span' not in result
        assert 'Deep text' in result


class TestExtractMetadataSectionsGdoc:
    """Tests for _extract_metadata_sections with Google Doc HTML."""

    def _build_gdoc_html(self) -> str:
        """Build realistic Google Doc HTML with all metadata sections."""
        return """
        <p class="c3"><span class="c0">Article body content here.</span></p>
        <p class="c3"><span class="c0">&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;</span></p>
        <h2 class="c5"><span class="c1">&#26657;&#23565;&#32080;&#26524;</span></h2>
        <p class="c3"><span class="c0">1. &#12304;&#27161;&#40670;&#33287;&#20840;&#21322;&#24418;&#12305;</span></p>
        <p class="c3"><span class="c0">&#21407;&#25991;&#65306;&#31449;&#19978;&#39636;&#37325;&#35336;&#65292;&#25976;&#23383;&#30906;&#23526;&#19979;&#38477;&#20102;</span></p>
        <p class="c3"><span class="c0">&#24314;&#35696;&#65306;&#31449;&#19978;&#39636;&#37325;&#35336;&#65292;&#25976;&#23383;&#30906;&#23526;&#19979;&#38477;&#20102;</span></p>
        <p class="c3"><span class="c0">&#35498;&#26126;&#65306;&#36949;&#21453;&#27161;&#40670;&#33287;&#20840;&#21322;&#24418;&#35215;&#21063;</span></p>
        <p class="c3"><span class="c0">2. &#12304;&#27161;&#40670;&#33287;&#20840;&#21322;&#24418;&#12305;</span></p>
        <p class="c3"><span class="c0">&#21407;&#25991;&#65306;&#28271;&#27713;&#31245;&#24494;&#25910;&#20094;&#21363;&#21487;,&#19981;&#38656;&#35201;&#21246;&#33451;&#12290;</span></p>
        <p class="c3"><span class="c0">&#24314;&#35696;&#65306;&#28271;&#27713;&#31245;&#24494;&#25910;&#20094;&#21363;&#21487;&#65292;&#19981;&#38656;&#35201;&#21246;&#33451;&#12290;</span></p>
        <p class="c3"><span class="c0">&#35498;&#26126;&#65306;&#36949;&#21453;&#27161;&#40670;&#33287;&#20840;&#21322;&#24418;&#35215;&#21063;</span></p>
        <p class="c3"><span class="c0">&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;</span></p>
        <h2 class="c5"><span class="c1">Meta + AEO</span></h2>
        <p class="c3"><span class="c0">SEO&#27161;&#38988;</span></p>
        <p class="c3"><span class="c0">&#36039;&#35338;&#22411;&#65306;</span></p>
        <p class="c3"><span class="c0">&#33419;&#38957;&#29140;&#39895;&#39770;&#65306;&#20013;&#37291;&#39178;&#29983;&#35264;&#40670;&#19979;&#30340;&#20581;&#24247;&#28187;&#37325;&#39135;&#35676;</span></p>
        <p class="c3"><span class="c0">&#25080;&#24565;&#22411;&#65306;</span></p>
        <p class="c3"><span class="c0">&#19981;&#25384;&#39187;&#20063;&#33021;&#30246;&#65311;&#33419;&#38957;&#39895;&#39770;&#30340;&#20013;&#37291;&#39178;&#29983;&#31192;&#23494;</span></p>
        <p class="c3"><span class="c0">Meta&#25551;&#36848;</span></p>
        <p class="c3"><span class="c0">&#31680;&#39135;&#28187;&#32933;&#24120;&#35731;&#20154;&#30130;&#24970;</span></p>
        <p class="c3"><span class="c0">Focus Keyword</span></p>
        <p class="c3"><span class="c0">&#33419;&#38957;&#29140;&#39895;&#39770;</span></p>
        <p class="c3"><span class="c0">Tags</span></p>
        <p class="c3"><span class="c0">&#33419;&#38957;&#29140;&#39895;&#39770;, &#20013;&#37291;&#39178;&#29983;, &#28187;&#37325;&#39135;&#35676;, &#29151;&#39178;&#22343;&#34913;, &#20581;&#24247;&#39154;&#39135;</span></p>
        <p class="c3"><span class="c0">AEO&#39006;&#22411;&#65306;C</span></p>
        <p class="c3"><span class="c0">AEO&#39318;&#27573;</span></p>
        <p class="c3"><span class="c0">&#28187;&#32933;&#36942;&#31243;&#20013;&#24456;&#22810;&#20154;&#25361;&#25136;</span></p>
        <p class="c3"><span class="c0">&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;</span></p>
        <h2 class="c5"><span class="c1">&#22294;&#29255; Alt Text</span></h2>
        <p class="c3"><span class="c0">1. &#19968;&#30871;&#29140;&#29038;&#30340;&#39895;&#39770;&#33287;&#33419;&#38957;</span></p>
        <p class="c3"><span class="c0">&#22294;&#29255;&#36899;&#32080;&#65306;https://drive.google.com/file/d/1FGtest/view</span></p>
        <p class="c3"><span class="c0">2. &#26408;&#30436;&#19978;&#25850;&#25918;&#33879;&#20999;&#29255;&#39895;&#39770;</span></p>
        <p class="c3"><span class="c0">&#22294;&#29255;&#36899;&#32080;&#65306;https://drive.google.com/file/d/1Ratest/view</span></p>
        """

    def test_divider_detection_with_entities(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        # Should find proofreading suggestions
        assert len(result["proofreading_suggestions"]) >= 2

    def test_proofreading_extraction(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        suggestions = result["proofreading_suggestions"]
        assert len(suggestions) >= 2
        assert suggestions[0]["position"] == 1
        assert suggestions[0]["source"] == "doc_proofreading"
        assert suggestions[0]["original"]
        assert suggestions[0]["suggestion"]
        assert suggestions[0]["reason"]

    def test_seo_title_variants(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        variants = result["seo_title_variants"]
        assert len(variants) == 2
        types = {v["type"] for v in variants}
        assert "資訊型" in types
        assert "懸念型" in types
        for v in variants:
            assert v["title"]

    def test_meta_description(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        assert result["meta_description"] is not None
        assert len(result["meta_description"]) > 0

    def test_focus_keyword(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        assert result["focus_keyword"] is not None

    def test_tags(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        assert len(result["tags"]) == 5

    def test_aeo_type(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        assert result["aeo_type"] == "C"

    def test_aeo_paragraph(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        assert result["aeo_paragraph"] is not None
        assert len(result["aeo_paragraph"]) > 0

    def test_image_alt_texts(self):
        html = self._build_gdoc_html()
        result = _extract_metadata_sections(html)
        alts = result["image_alt_texts"]
        assert len(alts) == 2
        assert alts[0]["position"] == 1
        assert alts[0]["alt_text"]
        assert alts[0]["drive_link"] == "https://drive.google.com/file/d/1FGtest/view"
        assert alts[1]["position"] == 2
        assert alts[1]["drive_link"] == "https://drive.google.com/file/d/1Ratest/view"


class TestCleanMetadataSectionsGdoc:
    """Tests for _clean_metadata_sections_from_body with Google Doc HTML."""

    def test_truncates_at_gdoc_divider(self):
        html = (
            '<p class="c3"><span class="c0">Article body.</span></p>'
            '<p class="c3"><span class="c0">&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;&#9552;</span></p>'
            '<h2 class="c5"><span class="c1">&#26657;&#23565;&#32080;&#26524;</span></h2>'
            '<p class="c3"><span class="c0">Proofreading data here</span></p>'
        )
        cleaned = _clean_metadata_sections_from_body(html)
        assert 'Article body' in cleaned
        assert '校對結果' not in cleaned
        assert 'Proofreading data' not in cleaned

    def test_removes_editor_credit(self):
        html = '<p>Article body.</p><p>責任編輯：張三</p>'
        cleaned = _clean_metadata_sections_from_body(html)
        assert 'Article body' in cleaned
        assert '責任編輯' not in cleaned

    def test_no_metadata_returns_unchanged(self):
        html = '<p>Just a simple article body.</p>'
        cleaned = _clean_metadata_sections_from_body(html)
        assert 'Just a simple article body' in cleaned


class TestParseProofreadingSectionGdoc:
    """Tests for _parse_proofreading_section with Google Doc multi-paragraph format."""

    def test_pattern0_multi_paragraph(self):
        """Test multi-paragraph proofreading format (Pattern 0)."""
        html = """
        <p>1. 【標點與全半形】</p>
        <p>原文：站上體重計，數字確實下降了</p>
        <p>建議：站上體重計，數字確實下降了</p>
        <p>說明：違反標點與全半形規則</p>
        <p>2. 【標點與全半形】</p>
        <p>原文：湯汁稍微收乾即可,不需要勾芡。</p>
        <p>建議：湯汁稍微收乾即可，不需要勾芡。</p>
        <p>說明：違反標點與全半形規則</p>
        """
        result = _parse_proofreading_section(html)
        assert len(result) == 2
        assert result[0]["position"] == 1
        assert result[0]["original"].startswith("站上體重計")
        assert result[0]["suggestion"].startswith("站上體重計")
        assert "標點" in result[0]["reason"] or "規則" in result[0]["reason"]
        assert result[1]["position"] == 2
        assert "," in result[1]["original"]  # Half-width comma in original
        assert "，" in result[1]["suggestion"]  # Full-width comma in suggestion

    def test_pattern0_five_items(self):
        """Test extracting 5 proofreading items."""
        items = []
        for i in range(1, 6):
            items.append(f"""
            <p>{i}. 【錯誤類型{i}】</p>
            <p>原文：原文內容{i}</p>
            <p>建議：建議內容{i}</p>
            <p>說明：說明原因{i}</p>
            """)
        html = "\n".join(items)
        result = _parse_proofreading_section(html)
        assert len(result) == 5
        for i, item in enumerate(result):
            assert item["position"] == i + 1

    def test_legacy_pattern1_still_works(self):
        """Test that legacy Pattern 1 still works."""
        html = '<p>1. 原文：「錯誤文字」→ 建議：「正確文字」（修正原因）</p>'
        result = _parse_proofreading_section(html)
        assert len(result) == 1
        assert result[0]["original"] == "錯誤文字"
        assert result[0]["suggestion"] == "正確文字"
        assert result[0]["reason"] == "修正原因"


class TestParseMetaAeoSectionGdoc:
    """Tests for _parse_meta_aeo_section with Google Doc multi-line format."""

    def test_google_doc_multi_line_format(self):
        """Test the actual Google Doc format with labels on separate lines."""
        html = """
        <p>SEO標題</p>
        <p>資訊型：</p>
        <p>芋頭燉鱿魚：中醫養生觀點下的健康減重食譜</p>
        <p>懸念型：</p>
        <p>不挨餓也能瘦？芋頭鱿魚的中醫養生秘密</p>
        <p>Meta描述</p>
        <p>節食減肥常讓人疲憊</p>
        <p>Focus Keyword</p>
        <p>芋頭燉鱿魚</p>
        <p>Tags</p>
        <p>芋頭燉鱿魚, 中醫養生, 減重食譜, 營養均衡, 健康飲食</p>
        <p>AEO類型：C</p>
        <p>AEO首段</p>
        <p>減肥過程中很多人挑戰</p>
        """
        result = _parse_meta_aeo_section(html)

        # SEO title variants
        assert len(result["seo_title_variants"]) == 2
        types = {v["type"] for v in result["seo_title_variants"]}
        assert "資訊型" in types
        assert "懸念型" in types
        info_title = next(v for v in result["seo_title_variants"] if v["type"] == "資訊型")
        assert "芋頭燉鱿魚" in info_title["title"]

        # Meta description
        assert result["meta_description"] == "節食減肥常讓人疲憊"

        # Focus keyword
        assert result["focus_keyword"] == "芋頭燉鱿魚"

        # Tags
        assert len(result["tags"]) == 5
        assert "芋頭燉鱿魚" in result["tags"]
        assert "中醫養生" in result["tags"]

        # AEO
        assert result["aeo_type"] == "C"
        assert result["aeo_paragraph"] is not None
        assert "減肥" in result["aeo_paragraph"]

    def test_legacy_inline_format_still_works(self):
        """Test that legacy single-line format still works."""
        html = """
        <p>SEO標題（資訊型）：老花眼必看指南</p>
        <p>SEO標題（懸念型）：為什麼能讓老花眼不再模糊？</p>
        <p>Meta 描述：探討中醫如何改善老花眼</p>
        <p>Focus Keyword：老花眼 中醫</p>
        <p>Tags：老花眼, 中醫, 針灸</p>
        <p>AEO 類型：定義解說型</p>
        <p>AEO 首段：老花眼是一種常見的視力問題</p>
        """
        result = _parse_meta_aeo_section(html)

        assert len(result["seo_title_variants"]) == 2
        assert result["meta_description"] == "探討中醫如何改善老花眼"
        assert result["focus_keyword"] == "老花眼 中醫"
        assert len(result["tags"]) == 3
        assert result["aeo_type"] == "定義解說型"
        assert result["aeo_paragraph"] is not None

    def test_subtype_with_value_on_same_line(self):
        """Test subtype label with value on same line."""
        html = """
        <p>SEO標題</p>
        <p>資訊型：芋頭燉鱿魚食譜</p>
        <p>懸念型：不挨餓也能瘦？</p>
        """
        result = _parse_meta_aeo_section(html)
        assert len(result["seo_title_variants"]) == 2

    def test_aeo_type_inline(self):
        """Test AEO type with value on the same line (AEO類型：C)."""
        html = "<p>AEO類型：C</p>"
        result = _parse_meta_aeo_section(html)
        assert result["aeo_type"] == "C"


class TestParseImageAltTextSectionGdoc:
    """Tests for _parse_image_alt_text_section with Google Doc format."""

    def test_drive_link_on_separate_line(self):
        """Test 圖片連結：URL format on separate lines."""
        html = """
        <p>1. 一碗燉煮的魷魚與芋頭</p>
        <p>圖片連結：https://drive.google.com/file/d/1FGtest/view</p>
        <p>2. 木盤上擺放著切片魷魚</p>
        <p>圖片連結：https://drive.google.com/file/d/1Ratest/view</p>
        """
        result = _parse_image_alt_text_section(html)
        assert len(result) == 2
        assert result[0]["position"] == 1
        assert "魷魚" in result[0]["alt_text"] or "鱿魚" in result[0]["alt_text"] or "燉煮" in result[0]["alt_text"]
        assert result[0]["drive_link"] == "https://drive.google.com/file/d/1FGtest/view"
        assert result[1]["position"] == 2
        assert result[1]["drive_link"] == "https://drive.google.com/file/d/1Ratest/view"

    def test_inline_url_still_works(self):
        """Test legacy inline URL format still works."""
        html = '<p>1. 老花眼穴位示意圖 (https://drive.google.com/file/d/test/view)</p>'
        result = _parse_image_alt_text_section(html)
        assert len(result) == 1
        assert result[0]["drive_link"] == "https://drive.google.com/file/d/test/view"

    def test_a_tag_link_extraction(self):
        """Test link extraction from <a> tags."""
        html = '<p>1. 穴位圖 <a href="https://drive.google.com/file/d/abc/view">連結</a></p>'
        result = _parse_image_alt_text_section(html)
        assert len(result) >= 1
        assert result[0]["drive_link"] == "https://drive.google.com/file/d/abc/view"
