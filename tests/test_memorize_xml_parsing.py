"""Tests for XML parsing in MemorizeMixin.

Covers _find_xml_boundaries() and _parse_memory_type_response_xml() edge cases.
"""

from __future__ import annotations

import pytest

from memu.app.memorize import MemorizeMixin


class StubMemoMixin(MemorizeMixin):
    """Minimal stub to test XML parsing methods."""

    pass


@pytest.fixture
def parser() -> StubMemoMixin:
    return StubMemoMixin()


# ---------------------------------------------------------------------------
# _find_xml_boundaries
# ---------------------------------------------------------------------------


class TestFindXmlBoundaries:
    def test_known_root_tag_item(self, parser: StubMemoMixin) -> None:
        raw = "<item><memory><content>A</content></memory></item>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        start, end, closing = result
        assert start == 0
        assert closing == "</item>"

    def test_known_root_tag_profile(self, parser: StubMemoMixin) -> None:
        raw = "<profile><memory><content>B</content></memory></profile>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</profile>"

    def test_case_insensitive_root_tag(self, parser: StubMemoMixin) -> None:
        raw = "<Item><memory><content>C</content></memory></Item>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        start, end, closing = result
        assert start == 0
        # The actual closing tag should preserve original casing
        assert closing == "</Item>"

    def test_upper_case_root_tag(self, parser: StubMemoMixin) -> None:
        raw = "<ITEM><memory><content>D</content></memory></ITEM>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</ITEM>"

    def test_new_root_tag_memories(self, parser: StubMemoMixin) -> None:
        raw = "<memories><memory><content>E</content></memory></memories>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</memories>"

    def test_new_root_tag_response(self, parser: StubMemoMixin) -> None:
        raw = "<response><memory><content>F</content></memory></response>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</response>"

    def test_new_root_tag_items(self, parser: StubMemoMixin) -> None:
        raw = "<items><memory><content>G</content></memory></items>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</items>"

    def test_root_tag_with_attributes(self, parser: StubMemoMixin) -> None:
        raw = '<item type="profile"><memory><content>H</content></memory></item>'
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        start, end, closing = result
        assert start == 0
        assert closing == "</item>"

    def test_fallback_unknown_wrapper_with_memory(self, parser: StubMemoMixin) -> None:
        raw = "<custom_wrapper><memory><content>I</content></memory></custom_wrapper>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</custom_wrapper>"

    def test_thinking_tags_skipped_in_fallback(self, parser: StubMemoMixin) -> None:
        raw = "<thinking>Let me analyze</thinking><custom_wrapper><memory><content>J</content></memory></custom_wrapper>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</custom_wrapper>"

    def test_chinese_thinking_tags_skipped(self, parser: StubMemoMixin) -> None:
        raw = "<\u601d\u8003>\u8ba9\u6211\u5206\u6790</\u601d\u8003><data><memory><content>K</content></memory></data>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[2] == "</data>"

    def test_no_xml_at_all(self, parser: StubMemoMixin) -> None:
        raw = "This is plain text with no XML"
        assert parser._find_xml_boundaries(raw) is None

    def test_empty_string(self, parser: StubMemoMixin) -> None:
        assert parser._find_xml_boundaries("") is None

    def test_memory_tag_only_no_wrapper(self, parser: StubMemoMixin) -> None:
        """<memory> alone should NOT be found as a root (it's in skip_tags)."""
        raw = "<memory><content>L</content></memory>"
        assert parser._find_xml_boundaries(raw) is None

    def test_leading_text_before_known_tag(self, parser: StubMemoMixin) -> None:
        raw = "Here are the results:\n<item><memory><content>M</content></memory></item>"
        result = parser._find_xml_boundaries(raw)
        assert result is not None
        assert result[0] > 0  # starts after the leading text


# ---------------------------------------------------------------------------
# _parse_memory_type_response_xml
# ---------------------------------------------------------------------------


class TestParseMemoryTypeResponseXml:
    def _make_memory_xml(
        self,
        content: str,
        categories: list[str],
        root_tag: str = "item",
        root_attrs: str = "",
    ) -> str:
        cats_xml = "".join(f"<category>{c}</category>" for c in categories)
        open_tag = f"<{root_tag}{(' ' + root_attrs) if root_attrs else ''}>"
        close_tag = f"</{root_tag}>"
        return f"{open_tag}<memory><content>{content}</content><categories>{cats_xml}</categories></memory>{close_tag}"

    def test_standard_item(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("likes coffee", ["preferences"])
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "likes coffee"
        assert result[0]["categories"] == ["preferences"]

    def test_profile_root_tag(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("name is Alice", ["identity"], root_tag="profile")
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "name is Alice"

    def test_unknown_root_tag_memories(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("test fact", ["general"], root_tag="memories")
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1

    def test_root_tag_with_attributes(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("attr test", ["test"], root_tag="item", root_attrs='type="profile"')
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "attr test"

    def test_bare_memory_no_wrapper(self, parser: StubMemoMixin) -> None:
        xml = "<memory><content>bare fact</content><categories><category>misc</category></categories></memory>"
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "bare fact"

    def test_markdown_code_fences(self, parser: StubMemoMixin) -> None:
        xml = "```xml\n<item><memory><content>fenced</content><categories><category>test</category></categories></memory></item>\n```"
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "fenced"

    def test_plain_text_no_xml(self, parser: StubMemoMixin) -> None:
        result = parser._parse_memory_type_response_xml("Here are the memory items: blah blah")
        assert result == []

    def test_empty_string(self, parser: StubMemoMixin) -> None:
        assert parser._parse_memory_type_response_xml("") == []

    def test_whitespace_only(self, parser: StubMemoMixin) -> None:
        assert parser._parse_memory_type_response_xml("   \n  ") == []

    def test_json_response_wrong_format(self, parser: StubMemoMixin) -> None:
        result = parser._parse_memory_type_response_xml('{"memories_items": [{"content": "x"}]}')
        assert result == []

    def test_case_insensitive_root_tags(self, parser: StubMemoMixin) -> None:
        xml = "<Item><memory><content>cased</content><categories><category>test</category></categories></memory></Item>"
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "cased"

    def test_multiple_memory_elements(self, parser: StubMemoMixin) -> None:
        xml = (
            "<item>"
            "<memory><content>first</content><categories><category>a</category></categories></memory>"
            "<memory><content>second</content><categories><category>b</category></categories></memory>"
            "</item>"
        )
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 2
        assert result[0]["content"] == "first"
        assert result[1]["content"] == "second"

    def test_memory_without_content(self, parser: StubMemoMixin) -> None:
        xml = "<item><memory><categories><category>X</category></categories></memory></item>"
        result = parser._parse_memory_type_response_xml(xml)
        assert result == []

    def test_memory_without_categories(self, parser: StubMemoMixin) -> None:
        xml = "<item><memory><content>orphan</content></memory></item>"
        result = parser._parse_memory_type_response_xml(xml)
        assert result == []

    def test_chinese_content(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("\u7528\u6237\u559c\u6b22\u559d\u5496\u5561", ["\u504f\u597d"])
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "\u7528\u6237\u559c\u6b22\u559d\u5496\u5561"
        assert result[0]["categories"] == ["\u504f\u597d"]

    def test_thinking_tags_before_xml(self, parser: StubMemoMixin) -> None:
        xml = (
            "<thinking>Let me analyze this conversation...</thinking>"
            "<item><memory><content>analyzed</content><categories><category>test</category></categories></memory></item>"
        )
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert result[0]["content"] == "analyzed"

    def test_ampersand_in_content(self, parser: StubMemoMixin) -> None:
        xml = "<item><memory><content>A & B</content><categories><category>X</category></categories></memory></item>"
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1
        assert "A" in result[0]["content"]
        assert "B" in result[0]["content"]

    def test_multiple_bare_memories_no_wrapper(self, parser: StubMemoMixin) -> None:
        xml = (
            "<memory><content>bare1</content><categories><category>a</category></categories></memory>"
            "<memory><content>bare2</content><categories><category>b</category></categories></memory>"
        )
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 2

    def test_result_root_tag(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("result wrapped", ["general"], root_tag="result")
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1

    def test_output_root_tag(self, parser: StubMemoMixin) -> None:
        xml = self._make_memory_xml("output wrapped", ["general"], root_tag="output")
        result = parser._parse_memory_type_response_xml(xml)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# JSON fallback (when LLM returns JSON instead of XML)
# ---------------------------------------------------------------------------


class TestJsonFallback:
    """Tests for _try_parse_json_memory_response and its integration."""

    def test_json_item_memory_structure(self, parser: StubMemoMixin) -> None:
        """LLM returns {"item": {"memory": [...]}} — the actual observed format."""
        raw = '{"item": {"memory": [{"content": "用户喜欢咖啡", "categories": ["偏好"]}]}}'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 1
        assert result[0]["content"] == "用户喜欢咖啡"
        assert result[0]["categories"] == ["偏好"]

    def test_json_memories_items_legacy(self, parser: StubMemoMixin) -> None:
        """Legacy format: {"memories_items": [...]}"""
        raw = '{"memories_items": [{"content": "fact A", "categories": ["general"]}]}'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 1
        assert result[0]["content"] == "fact A"

    def test_json_direct_memory_array(self, parser: StubMemoMixin) -> None:
        """Format: {"memory": [...]}"""
        raw = '{"memory": [{"content": "fact B", "categories": ["info"]}]}'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 1

    def test_json_flat_list(self, parser: StubMemoMixin) -> None:
        """Format: [{"content": ..., "categories": ...}, ...]"""
        raw = '[{"content": "fact C", "categories": ["misc"]}]'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 1
        assert result[0]["content"] == "fact C"

    def test_json_multiple_items(self, parser: StubMemoMixin) -> None:
        raw = '{"item": {"memory": [{"content": "A", "categories": ["x"]}, {"content": "B", "categories": ["y"]}]}}'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 2
        assert result[0]["content"] == "A"
        assert result[1]["content"] == "B"

    def test_json_missing_content_skipped(self, parser: StubMemoMixin) -> None:
        raw = '{"memory": [{"categories": ["x"]}]}'
        result = parser._parse_memory_type_response_xml(raw)
        assert result == []

    def test_json_missing_categories_skipped(self, parser: StubMemoMixin) -> None:
        raw = '{"memory": [{"content": "orphan"}]}'
        result = parser._parse_memory_type_response_xml(raw)
        assert result == []

    def test_json_empty_content_skipped(self, parser: StubMemoMixin) -> None:
        raw = '{"memory": [{"content": "", "categories": ["x"]}]}'
        result = parser._parse_memory_type_response_xml(raw)
        assert result == []

    def test_json_wrapped_in_markdown(self, parser: StubMemoMixin) -> None:
        raw = '```json\n{"item": {"memory": [{"content": "wrapped", "categories": ["test"]}]}}\n```'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 1
        assert result[0]["content"] == "wrapped"

    def test_json_with_leading_text(self, parser: StubMemoMixin) -> None:
        """LLM returns explanation text before JSON."""
        raw = 'Here are the extracted memories:\n{"item": {"memory": [{"content": "extracted", "categories": ["info"]}]}}'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 1

    def test_json_chinese_encoding(self, parser: StubMemoMixin) -> None:
        """Chinese content in JSON — the exact scenario from logs."""
        raw = '{"item": {"memory": [{"content": "用户说了你好", "categories": ["知识"]}, {"content": "用户说了再见", "categories": ["事件"]}]}}'
        result = parser._parse_memory_type_response_xml(raw)
        assert len(result) == 2
        assert result[0]["content"] == "用户说了你好"
        assert result[1]["categories"] == ["事件"]

    def test_not_json_not_xml_still_warns(self, parser: StubMemoMixin) -> None:
        """Pure text should still return [] (and warn)."""
        result = parser._parse_memory_type_response_xml("This is just plain text, not JSON or XML.")
        assert result == []

    def test_json_fallback_direct_method(self, parser: StubMemoMixin) -> None:
        """Test _try_parse_json_memory_response directly."""
        raw = '{"item": {"memory": [{"content": "direct test", "categories": ["cat"]}]}}'
        result = parser._try_parse_json_memory_response(raw)
        assert len(result) == 1
        assert result[0]["content"] == "direct test"

    def test_json_fallback_invalid_json(self, parser: StubMemoMixin) -> None:
        result = parser._try_parse_json_memory_response("not json at all")
        assert result == []

    def test_json_fallback_arbitrary_root_key(self, parser: StubMemoMixin) -> None:
        """Any root key wrapping a memory list should work."""
        raw = '{"data": {"memory": [{"content": "arbitrary key", "categories": ["x"]}]}}'
        result = parser._try_parse_json_memory_response(raw)
        assert len(result) == 1
