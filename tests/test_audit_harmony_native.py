from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "audit_harmony_native.py"


def load_audit_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("audit_harmony_native", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


audit = load_audit_module()


class AuditHarmonyNativeTest(unittest.TestCase):
    def create_project(
        self,
        root: Path,
        *,
        target: str = "foo",
        registration: str = "foo",
        imported_library: str = "libfoo.so",
        declaration: str = "export function ping(value: number): number",
        source_name: str = "napi_init.cpp",
    ) -> Path:
        module_root = root / "entry"
        cpp_root = module_root / "src" / "main" / "cpp"
        ets_root = module_root / "src" / "main" / "ets"
        types_root = cpp_root / "types" / f"lib{target}"
        cpp_root.mkdir(parents=True)
        ets_root.mkdir(parents=True)
        types_root.mkdir(parents=True)

        (module_root / "build-profile.json5").write_text(
            """
{
    "buildOption": {
        "externalNativeOptions": {
            "path": "./src/main/cpp/CMakeLists.txt",
            "abiFilters": ["arm64-v8a"]
        }
    }
}
""".strip(),
            encoding="utf-8",
        )
        (cpp_root / "CMakeLists.txt").write_text(
            f"""
cmake_minimum_required(VERSION 3.5.0)
project({target})
add_library({target} SHARED {source_name})
target_link_libraries({target} PRIVATE libace_napi.z.so)
""".strip(),
            encoding="utf-8",
        )
        (cpp_root / source_name).write_text(
            f"""
#include <napi/native_api.h>

napi_value Ping(napi_env env, napi_callback_info info)
{{
    return nullptr;
}}

napi_value Init(napi_env env, napi_value exports)
{{
    napi_property_descriptor properties[] = {{
        {{"ping", nullptr, Ping, nullptr, nullptr, nullptr, napi_default, nullptr}},
    }};
    napi_define_properties(env, exports, 1, properties);
    return exports;
}}

NAPI_MODULE({registration}, Init)
""".strip(),
            encoding="utf-8",
        )
        (ets_root / "NativeBridge.ets").write_text(
            f"import nativeModule from '{imported_library}'\n",
            encoding="utf-8",
        )
        (types_root / "index.d.ts").write_text(
            declaration + "\n",
            encoding="utf-8",
        )
        return cpp_root / "CMakeLists.txt"

    def test_consistent_module_has_no_error_or_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            cmake_path = self.create_project(project_root)

            result = audit.audit_module(cmake_path, project_root)

            self.assertEqual(["foo"], result.shared_targets)
            self.assertEqual(["foo"], result.registered_modules)
            self.assertEqual(["libfoo.so"], result.arkts_imports)
            self.assertIn("ping", result.native_exports)
            self.assertIn("ping", result.arkts_declarations)
            self.assertFalse(
                [
                    finding
                    for finding in result.findings
                    if finding.level in {"error", "warning"}
                ]
            )

    def test_exported_const_function_declaration_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            cmake_path = self.create_project(
                project_root,
                declaration="export const ping: (value: number) => number",
            )

            result = audit.audit_module(cmake_path, project_root)

            self.assertIn("ping", result.arkts_declarations)
            self.assertFalse(
                any(
                    "Native 导出缺少 ArkTS 声明" in finding.message
                    for finding in result.findings
                )
            )

    def test_native_interface_declaration_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            cmake_path = self.create_project(
                project_root,
                declaration="""
interface FooNATIVEBridge {
    ping(value: number): number
}
""".strip(),
            )

            result = audit.audit_module(cmake_path, project_root)

            self.assertIn("ping", result.arkts_declarations)

    def test_alias_mismatch_is_warning_not_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            cmake_path = self.create_project(
                project_root,
                registration="bar",
                imported_library="libbar.so",
            )

            result = audit.audit_module(cmake_path, project_root)
            mismatch_findings = [
                finding
                for finding in result.findings
                if "不一致" in finding.message
            ]

            self.assertEqual(2, len(mismatch_findings))
            self.assertTrue(
                all(finding.level == "warning" for finding in mismatch_findings)
            )

    def test_missing_cmake_source_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            cmake_path = self.create_project(project_root)
            (cmake_path.parent / "napi_init.cpp").unlink()

            result = audit.audit_module(cmake_path, project_root)

            self.assertTrue(
                any(
                    finding.level == "error"
                    and "不存在的源文件" in finding.message
                    for finding in result.findings
                )
            )

    def test_cli_strict_succeeds_for_consistent_module(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            self.create_project(project_root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(project_root),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_cli_strict_fails_for_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project_root = Path(temporary_directory)
            self.create_project(
                project_root,
                registration="bar",
                imported_library="libbar.so",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(project_root),
                    "--strict",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(1, result.returncode, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
