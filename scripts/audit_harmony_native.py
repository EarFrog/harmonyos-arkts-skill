#!/usr/bin/env python3
"""Read-only inventory and consistency checks for HarmonyOS Native modules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".cxx",
    ".git",
    ".gradle",
    ".hvigor",
    ".idea",
    "build",
    "node_modules",
    "oh_modules",
    "third_party",
}
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx"}


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class NativeModule:
    module_root: str
    cmake: str
    project_name: str | None = None
    shared_targets: list[str] = field(default_factory=list)
    registered_modules: list[str] = field(default_factory=list)
    native_exports: list[str] = field(default_factory=list)
    arkts_imports: list[str] = field(default_factory=list)
    arkts_declarations: list[str] = field(default_factory=list)
    source_files: list[str] = field(default_factory=list)
    linked_libraries: list[str] = field(default_factory=list)
    native_features: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def walk_files(root: Path, suffixes: set[str] | None = None) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if suffixes is None or path.suffix.lower() in suffixes:
            yield path


def extract_calls(text: str, function_name: str) -> list[str]:
    """Return balanced parenthesized calls without parsing all of CMake/C++."""
    result: list[str] = []
    pattern = re.compile(rf"\b{re.escape(function_name)}\s*\(", re.IGNORECASE)
    for match in pattern.finditer(text):
        start = match.end()
        depth = 1
        quote: str | None = None
        escaped = False
        index = start
        while index < len(text) and depth:
            char = text[index]
            if escaped:
                escaped = False
            elif char == "\\" and quote:
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in {"'", '"'}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            index += 1
        if depth == 0:
            result.append(text[start : index - 1])
    return result


def clean_cmake_token(token: str) -> str:
    return token.strip().strip("\"'")


def cmake_tokens(call: str) -> list[str]:
    without_comments = re.sub(r"#[^\n]*", " ", call)
    return [clean_cmake_token(token) for token in re.findall(r'"[^"]*"|\'[^\']*\'|[^\s]+', without_comments)]


def resolve_target_name(name: str, project_name: str | None) -> str:
    if name == "${PROJECT_NAME}" and project_name:
        return project_name
    return name


def relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def collect_arkts_contract(module_root: Path) -> tuple[set[str], set[str]]:
    imports: set[str] = set()
    declarations: set[str] = set()
    source_suffixes = {".ets", ".ts", ".d.ts"}

    for path in walk_files(module_root, source_suffixes):
        text = read_text(path)
        imports.update(
            re.findall(r"\bfrom\s*['\"](lib[A-Za-z0-9_.+-]+\.so)['\"]", text)
        )
        if path.name.endswith(".d.ts"):
            declarations.update(
                re.findall(
                    r"\b(?:export\s+)?function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
                    text,
                )
            )
            declarations.update(
                re.findall(
                    r"\b(?:export\s+)?(?:declare\s+)?const\s+"
                    r"([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*\(",
                    text,
                )
            )

        for interface_match in re.finditer(
            r"\binterface\s+[A-Za-z_$][A-Za-z0-9_$]*native[A-Za-z0-9_$]*\s*\{",
            text,
            re.IGNORECASE,
        ):
            body_start = interface_match.end()
            depth = 1
            cursor = body_start
            while cursor < len(text) and depth:
                if text[cursor] == "{":
                    depth += 1
                elif text[cursor] == "}":
                    depth -= 1
                cursor += 1
            body = text[body_start : cursor - 1] if depth == 0 else ""
            declarations.update(
                re.findall(
                    r"(?m)^\s*(?:readonly\s+)?([A-Za-z_$][A-Za-z0-9_$]*)\s*\(",
                    body,
                )
            )

    return imports, declarations


def collect_native_contract(
    module_root: Path,
) -> tuple[set[str], set[str], str, list[Path]]:
    registrations: set[str] = set()
    exports: set[str] = set()
    combined: list[str] = []
    source_paths = list(walk_files(module_root, SOURCE_SUFFIXES | {".h", ".hpp"}))

    for path in source_paths:
        text = read_text(path)
        combined.append(text)
        registrations.update(
            re.findall(r"\bNAPI_MODULE\s*\(\s*([A-Za-z0-9_.+-]+)", text)
        )
        registrations.update(
            re.findall(r"\.nm_modname\s*=\s*['\"]([^'\"]+)['\"]", text)
        )
        exports.update(
            re.findall(
                r"\{\s*['\"]([A-Za-z_$][A-Za-z0-9_$]*)['\"]\s*,\s*"
                r"(?:nullptr|NULL)\s*,\s*[A-Za-z_$:][A-Za-z0-9_$:]*",
                text,
                re.MULTILINE,
            )
        )

    return registrations, exports, "\n".join(combined), source_paths


def detect_native_features(native_text: str) -> list[str]:
    checks = [
        ("Node-API", r"\bnapi_(?:env|value|status|create_|get_|set_|define_)"),
        ("N-API async work", r"\bnapi_(?:create|queue|cancel|delete)_async_work\b"),
        ("ArrayBuffer/TypedArray", r"\bnapi_(?:create|get)_arraybuffer_info\b|\bnapi_create_arraybuffer\b"),
        ("XComponent", r"\bOH_NativeXComponent\b"),
        ("NativeWindow", r"\bOH_NativeWindow\b|\bOHNativeWindow\b"),
        ("Native Drawing", r"\bOH_Drawing_"),
        ("EGL", r"\begl(?:Initialize|Create|MakeCurrent|SwapBuffers|Destroy)"),
        ("OpenGL ES", r"\bgl(?:Draw|Buffer|Tex|Shader|Program|Framebuffer)[A-Za-z0-9_]*\b"),
    ]
    return [label for label, pattern in checks if re.search(pattern, native_text)]


def parse_cmake(
    cmake_path: Path, project_root: Path
) -> tuple[str | None, list[str], list[str], list[str], list[Finding]]:
    text = read_text(cmake_path)
    findings: list[Finding] = []
    project_match = re.search(
        r"\bproject\s*\(\s*([A-Za-z0-9_.+-]+)", text, re.IGNORECASE
    )
    project_name = project_match.group(1) if project_match else None
    targets: list[str] = []
    sources: list[str] = []

    for call in extract_calls(text, "add_library"):
        tokens = cmake_tokens(call)
        if len(tokens) < 2 or "IMPORTED" in {token.upper() for token in tokens}:
            continue
        kind_index = next(
            (
                index
                for index, token in enumerate(tokens[1:], start=1)
                if token.upper() in {"SHARED", "STATIC", "MODULE", "OBJECT", "INTERFACE"}
            ),
            None,
        )
        if kind_index is None or tokens[kind_index].upper() != "SHARED":
            continue
        target = resolve_target_name(tokens[0], project_name)
        targets.append(target)
        for token in tokens[kind_index + 1 :]:
            clean = token.rstrip(")")
            if Path(clean).suffix.lower() not in SOURCE_SUFFIXES:
                continue
            sources.append(clean)
            if "${" in clean or "$<" in clean:
                continue
            source_path = (cmake_path.parent / clean).resolve()
            if not source_path.exists():
                findings.append(
                    Finding(
                        "error",
                        f"CMake target {target} 引用了不存在的源文件：{relative(source_path, project_root)}",
                    )
                )

    linked: set[str] = set()
    for call in extract_calls(text, "target_link_libraries"):
        tokens = cmake_tokens(call)
        if not tokens:
            continue
        for token in tokens[1:]:
            clean = token.rstrip(")")
            if clean.upper() in {"PRIVATE", "PUBLIC", "INTERFACE"}:
                continue
            if clean.startswith("$"):
                continue
            linked.add(clean)

    if not targets:
        findings.append(Finding("error", "没有识别到 SHARED Native target。"))
    if not project_name:
        findings.append(Finding("note", "没有识别到 project(...)；target 仍可能使用显式名称。"))

    return project_name, sorted(set(targets)), sorted(set(sources)), sorted(linked), findings


def inspect_build_profile(module_root: Path, project_root: Path) -> list[Finding]:
    path = module_root / "build-profile.json5"
    if not path.exists():
        return [Finding("warning", "模块目录没有 build-profile.json5，需确认 Native CMake 从何处接入。")]

    text = read_text(path)
    findings: list[Finding] = []
    if "externalNativeOptions" not in text:
        findings.append(Finding("warning", "build-profile.json5 未发现 externalNativeOptions。"))
    if not re.search(
        r"['\"]?path['\"]?\s*:\s*['\"][^'\"]*CMakeLists\.txt['\"]", text
    ):
        findings.append(Finding("warning", "build-profile.json5 未识别到 CMakeLists.txt 路径。"))
    if "abiFilters" not in text:
        findings.append(
            Finding(
                "note",
                f"{relative(path, project_root)} 未显式发现 abiFilters；核对应用产物需要的 ABI。",
            )
        )
    return findings


def audit_module(cmake_path: Path, project_root: Path) -> NativeModule:
    cpp_dir = cmake_path.parent
    module_root = cpp_dir.parents[2] if len(cpp_dir.parents) >= 3 else cpp_dir
    project_name, targets, cmake_sources, linked, findings = parse_cmake(
        cmake_path, project_root
    )
    registrations, exports, native_text, native_source_paths = collect_native_contract(
        module_root
    )
    imports, declarations = collect_arkts_contract(module_root)

    module = NativeModule(
        module_root=relative(module_root, project_root),
        cmake=relative(cmake_path, project_root),
        project_name=project_name,
        shared_targets=targets,
        registered_modules=sorted(registrations),
        native_exports=sorted(exports),
        arkts_imports=sorted(imports),
        arkts_declarations=sorted(declarations),
        source_files=sorted(
            {
                relative(path, project_root)
                for path in native_source_paths
                if path.suffix.lower() in SOURCE_SUFFIXES
            }
        ),
        linked_libraries=linked,
        native_features=detect_native_features(native_text),
        findings=findings + inspect_build_profile(module_root, project_root),
    )

    expected_libraries = {f"lib{target}.so" for target in targets if "${" not in target}
    if imports and expected_libraries and not imports.intersection(expected_libraries):
        module.findings.append(
            Finding(
                "warning",
                "ArkTS 导入与 CMake SHARED target 不一致："
                f"imports={sorted(imports)}，expected={sorted(expected_libraries)}；"
                "若项目使用 loader alias、跨模块消费者或额外预编译库，请沿构建产物确认。",
            )
        )
    if registrations and targets and not registrations.intersection(targets):
        module.findings.append(
            Finding(
                "warning",
                "Native 注册模块名与 CMake target 不一致："
                f"registered={sorted(registrations)}，targets={targets}；"
                "若项目使用显式别名或特殊加载规则，请沿真实加载链确认。",
            )
        )
    if not registrations:
        module.findings.append(
            Finding("warning", "未识别到 NAPI_MODULE 或 napi_module.nm_modname 注册。")
        )
    if not imports:
        module.findings.append(
            Finding("note", "模块内部未识别到 lib*.so ArkTS import；消费者可能位于其他模块。")
        )

    has_macro_registration = bool(re.search(r"\bNAPI_MODULE\s*\(", native_text))
    has_explicit_registration = bool(
        re.search(r"\bnapi_module_register\s*\(", native_text)
    )
    if has_macro_registration and has_explicit_registration:
        module.findings.append(
            Finding(
                "warning",
                "同时发现 NAPI_MODULE 与显式 napi_module_register；核对是否发生重复注册。",
            )
        )

    if exports and declarations:
        missing_declarations = exports - declarations
        declaration_only = declarations - exports
        if missing_declarations:
            module.findings.append(
                Finding(
                    "warning",
                    f"Native 导出缺少 ArkTS 声明：{sorted(missing_declarations)}",
                )
            )
        if declaration_only:
            module.findings.append(
                Finding(
                    "warning",
                    f"ArkTS 声明未在静态导出表中找到：{sorted(declaration_only)}；"
                    "若使用动态导出或门面组合，请人工确认。",
                )
            )
    elif exports and not declarations:
        module.findings.append(
            Finding("warning", "发现 Native 导出，但未识别到 .d.ts 或 Native ArkTS 接口声明。")
        )

    if "EGL_BUFFER_PRESERVED" in native_text:
        module.findings.append(
            Finding(
                "review",
                "发现 EGL_BUFFER_PRESERVED；需检查调用结果、设备支持，并为持久画布准备自有 FBO/纹理方案。",
            )
        )
    if "glReadPixels" in native_text:
        module.findings.append(
            Finding(
                "review",
                "发现 glReadPixels；确认不阻塞输入/UI 路径，并检查尺寸溢出、行方向和 buffer 复用。",
            )
        )
    if re.search(r"\bnapi_(?:create|get)_arraybuffer", native_text):
        module.findings.append(
            Finding(
                "review",
                "发现 ArrayBuffer 数据通道；确认 stride/端序/上限/所有权，并用 calls-per-point 验证是否真正批处理。",
            )
        )

    return module


def discover_cmake_files(
    project_root: Path, module_filters: list[str] | None = None
) -> list[Path]:
    normalized_filters = {
        item.strip().strip("/")
        for item in (module_filters or [])
        if item.strip().strip("/")
    }
    result = []
    for path in project_root.rglob("CMakeLists.txt"):
        relative_parts = path.relative_to(project_root).parts
        if any(part in SKIP_DIRS for part in relative_parts):
            continue
        if normalized_filters:
            module_path = "/".join(relative_parts[:-4])
            top_level_module = relative_parts[0] if relative_parts else ""
            if (
                top_level_module not in normalized_filters
                and module_path not in normalized_filters
            ):
                continue
        if path.parent.name == "cpp" and path.parent.parent.name == "main":
            result.append(path)
    return sorted(result)


def report_markdown(project_root: Path, modules: list[NativeModule]) -> str:
    lines = [
        "# HarmonyOS Native 静态清单",
        "",
        f"- 项目：`{project_root}`",
        f"- Native 模块数：{len(modules)}",
        "- 说明：仅报告静态可见、高置信度信息；动态注册、生成代码和跨模块消费者需沿调用链确认。",
        "",
    ]
    for module in modules:
        lines.extend(
            [
                f"## `{module.module_root}`",
                "",
                f"- CMake：`{module.cmake}`",
                f"- project：`{module.project_name or '未识别'}`",
                f"- SHARED targets：{', '.join(f'`{item}`' for item in module.shared_targets) or '未识别'}",
                f"- 注册模块：{', '.join(f'`{item}`' for item in module.registered_modules) or '未识别'}",
                f"- ArkTS imports：{', '.join(f'`{item}`' for item in module.arkts_imports) or '未识别'}",
                f"- Native exports：{', '.join(f'`{item}`' for item in module.native_exports) or '未识别'}",
                f"- ArkTS declarations：{', '.join(f'`{item}`' for item in module.arkts_declarations) or '未识别'}",
                f"- Native 特征：{', '.join(module.native_features) or '未识别'}",
                "",
                "### 提示",
                "",
            ]
        )
        if module.findings:
            lines.extend(
                f"- **{finding.level.upper()}**：{finding.message}"
                for finding in module.findings
            )
        else:
            lines.append("- 未发现高置信度差异。")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="只读扫描 HarmonyOS Native 构建、注册、声明和图形关键点。"
    )
    parser.add_argument("project_root", type=Path)
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="只扫描指定模块；可重复传入，例如 --module drawing",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="存在 error/warning 时返回非零；review/note 不影响退出码",
    )
    args = parser.parse_args()

    project_root = args.project_root.expanduser().resolve()
    if not project_root.is_dir():
        print(f"项目目录不存在：{project_root}", file=sys.stderr)
        return 2

    cmake_files = discover_cmake_files(project_root, args.module)
    modules = [audit_module(path, project_root) for path in cmake_files]
    if args.json:
        print(
            json.dumps(
                {
                    "project_root": str(project_root),
                    "modules": [asdict(module) for module in modules],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(report_markdown(project_root, modules))

    if not modules:
        print("未发现 */src/main/cpp/CMakeLists.txt。", file=sys.stderr)
        return 1 if args.strict else 0
    has_problem = any(
        finding.level in {"error", "warning"}
        for module in modules
        for finding in module.findings
    )
    return 1 if args.strict and has_problem else 0


if __name__ == "__main__":
    raise SystemExit(main())
