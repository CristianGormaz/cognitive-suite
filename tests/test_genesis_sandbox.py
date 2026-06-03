import asyncio
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cognition.genesis_sandbox import GenesisSandbox, SandboxResult
from core.iafa_auditor import IafaAuditor


class GenesisSandboxTests(unittest.TestCase):
    def test_allows_basic_safe_code_and_audits(self):
        code = """import math
from datetime import datetime
from typing import List

def normalize(values: List[float]) -> list[float]:
    total = sum(values)
    return [round(value / total, 3) for value in values]
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            auditor = IafaAuditor(str(Path(temp_dir) / "audit.log"), secret_key="test-secret")
            sandbox = GenesisSandbox(auditor)

            result = asyncio.run(sandbox.validate_code_proposal(code, "task_safe"))
            entries = list(auditor.iter_verified_entries())

        self.assertIsInstance(result, SandboxResult)
        self.assertTrue(result.is_safe)
        self.assertEqual(result.validation_errors, [])
        self.assertEqual(result.code_hash, hashlib.sha256(code.encode("utf-8")).hexdigest())
        self.assertEqual(len(entries), 1)
        payload = entries[0]["payload"]
        self.assertEqual(payload["record_type"], "genesis_sandbox_validation")
        self.assertEqual(payload["original_task_id"], "task_safe")
        self.assertTrue(payload["result"]["is_safe"])

    def test_rejects_dangerous_imports(self):
        code = """import os
import subprocess
from shutil import rmtree
"""

        result = asyncio.run(GenesisSandbox().validate_code_proposal(code, "task_bad_import"))

        self.assertFalse(result.is_safe)
        self.assertTrue(any("dangerous import rejected: os" in error for error in result.validation_errors))
        self.assertTrue(any("dangerous import rejected: subprocess" in error for error in result.validation_errors))
        self.assertTrue(any("dangerous import rejected: shutil" in error for error in result.validation_errors))

    def test_rejects_imports_not_in_allowlist(self):
        code = "import requests\n"

        result = asyncio.run(GenesisSandbox().validate_code_proposal(code, "task_requests"))

        self.assertFalse(result.is_safe)
        self.assertEqual(result.validation_errors, ["import not in allowlist: requests"])

    def test_rejects_dangerous_import_aliases(self):
        code = """import math as open
from json import dumps as eval
"""

        result = asyncio.run(GenesisSandbox().validate_code_proposal(code, "task_alias"))

        self.assertFalse(result.is_safe)
        self.assertTrue(any("dangerous alias rejected: open" in error for error in result.validation_errors))
        self.assertTrue(any("dangerous imported name rejected: eval" in error for error in result.validation_errors))

    def test_rejects_dangerous_builtin_calls(self):
        code = """def run(payload):
    eval(payload)
    exec(payload)
    open("x.txt", "w")
    getattr(payload, "__class__")
"""

        result = asyncio.run(GenesisSandbox().validate_code_proposal(code, "task_calls"))

        self.assertFalse(result.is_safe)
        self.assertTrue(any("dangerous call rejected: eval" in error for error in result.validation_errors))
        self.assertTrue(any("dangerous call rejected: exec" in error for error in result.validation_errors))
        self.assertTrue(any("dangerous call rejected: open" in error for error in result.validation_errors))
        self.assertTrue(any("dangerous call rejected: getattr" in error for error in result.validation_errors))

    def test_rejects_dunder_attribute_access(self):
        code = """def inspect(obj):
    return obj.__class__
"""

        result = asyncio.run(GenesisSandbox().validate_code_proposal(code, "task_dunder"))

        self.assertFalse(result.is_safe)
        self.assertEqual(result.validation_errors, ["dangerous attribute access rejected: __class__"])

    def test_rejects_blocked_node_types(self):
        code = """class X:
    pass

async def run():
    await other()
"""

        result = asyncio.run(GenesisSandbox().validate_code_proposal(code, "task_nodes"))

        self.assertFalse(result.is_safe)
        self.assertTrue(any("node type rejected: ClassDef" in error for error in result.validation_errors))
        self.assertTrue(any("node type rejected: AsyncFunctionDef" in error for error in result.validation_errors))
        self.assertTrue(any("node type rejected: Await" in error for error in result.validation_errors))

    def test_syntax_error_is_reported_as_rejection(self):
        result = asyncio.run(GenesisSandbox().validate_code_proposal("def broken(:\n", "task_syntax"))

        self.assertFalse(result.is_safe)
        self.assertTrue(result.validation_errors[0].startswith("syntax error:"))

    def test_rejects_invalid_task_id_before_audit(self):
        with self.assertRaises(ValueError):
            asyncio.run(GenesisSandbox().validate_code_proposal("x = 1", ""))


if __name__ == "__main__":
    unittest.main()
