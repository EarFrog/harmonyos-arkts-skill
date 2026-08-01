from __future__ import annotations

import re
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).parents[1]
LOCAL_LINK_PATTERN = re.compile(r"\]\(([^)]+)\)")


class SkillStructureTest(unittest.TestCase):
    def test_skill_entrypoint_stays_concise(self) -> None:
        lines = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").splitlines()

        self.assertLess(len(lines), 500)
        self.assertIn("name: harmonyos-arkts", lines)
        self.assertTrue(any("Native/NDK" in line for line in lines))
        self.assertTrue(any("Android 转鸿蒙" in line for line in lines))
        self.assertTrue(any("纯血鸿蒙" in line for line in lines))

    def test_required_native_resources_exist(self) -> None:
        required_paths = {
            "references/native-arkts-interop.md",
            "references/native-canvas-performance.md",
            "references/native-cmake-build.md",
            "references/native-engineering-lessons.md",
            "references/native-napi-process.md",
            "references/native-architecture-patterns.md",
            "references/native-debugging.md",
            "references/native-safety.md",
            "references/native-official-node-api-guide.md",
            "references/native-persistence-export-scheduling.md",
            "references/native-rendering-architecture.md",
            "scripts/audit_harmony_native.py",
        }

        missing = [
            relative_path
            for relative_path in sorted(required_paths)
            if not (SKILL_ROOT / relative_path).is_file()
        ]
        self.assertEqual([], missing)

    def test_references_are_one_level_deep(self) -> None:
        references_root = SKILL_ROOT / "references"
        nested_references = [
            str(path.relative_to(SKILL_ROOT))
            for path in references_root.rglob("*.md")
            if path.parent != references_root
        ]

        self.assertEqual([], nested_references)

    def test_every_reference_is_linked_directly_from_skill(self) -> None:
        references_root = SKILL_ROOT / "references"
        expected_references = {
            str(path.relative_to(SKILL_ROOT))
            for path in references_root.glob("*.md")
        }
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        linked_references = {
            target.split("#", maxsplit=1)[0]
            for target in LOCAL_LINK_PATTERN.findall(skill_text)
            if target.startswith("references/")
        }

        self.assertEqual(expected_references, linked_references)

    def test_bundled_script_uses_skill_root(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            'python3 "$SKILL_ROOT/scripts/audit_harmony_native.py"',
            skill_text,
        )

    def test_declares_official_developer_knowledge_mcp(self) -> None:
        metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        expected_fields = {
            'type: "mcp"',
            'value: "harmonyos_developer_knowledge"',
            'transport: "streamable_http"',
            'url: "https://connect-api.cloud.huawei.com/api/developerknowledge/mcp"',
        }
        missing_fields = [
            field for field in sorted(expected_fields) if field not in metadata
        ]

        self.assertIn("dependencies:\n  tools:", metadata)
        self.assertEqual([], missing_fields)

    def test_skill_explains_mcp_decline_fallback(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("## 官方开发者知识 MCP", skill_text)
        self.assertIn("不要在普通开发任务中重复询问", skill_text)
        self.assertIn("继续使用目标仓库", skill_text)

    def test_local_markdown_links_resolve(self) -> None:
        markdown_paths = [
            SKILL_ROOT / "README.md",
            SKILL_ROOT / "SKILL.md",
            *sorted((SKILL_ROOT / "references").rglob("*.md")),
        ]
        missing_links: list[str] = []

        for markdown_path in markdown_paths:
            text = markdown_path.read_text(encoding="utf-8-sig")
            for raw_target in LOCAL_LINK_PATTERN.findall(text):
                target = raw_target.strip().strip("<>")
                if (
                    not target
                    or target.startswith("#")
                    or re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE)
                ):
                    continue
                relative_target = target.split("#", maxsplit=1)[0]
                resolved_target = (markdown_path.parent / relative_target).resolve()
                if not resolved_target.exists():
                    missing_links.append(
                        f"{markdown_path.relative_to(SKILL_ROOT)} -> {target}"
                    )

        self.assertEqual([], missing_links)


if __name__ == "__main__":
    unittest.main()
