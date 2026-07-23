from __future__ import print_function

import json
import os
import shutil
import stat
import tempfile
import unittest

import compliance_runner


class ComplianceRunnerTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.category = os.path.join(self.root, "test")
        os.mkdir(self.category)

    def tearDown(self):
        shutil.rmtree(self.root)

    def add_check(self, check_id, requires=None, body=None, timeout=2):
        check_dir = os.path.join(self.category, check_id)
        os.mkdir(check_dir)
        manifest = {
            "id": check_id,
            "name": check_id,
            "enabled": True,
            "entrypoint": "check.py",
            "timeout": timeout,
            "requires": requires or [],
            "variables": {"PRIVATE_VALUE": "secret"},
            "parameters": {"expected_version": "13.5"},
        }
        with open(os.path.join(check_dir, "manifest.yml"), "w") as output:
            compliance_runner.yaml.safe_dump(manifest, output)
        script = body or """#!/usr/bin/env python
from __future__ import print_function
import json, os, sys
print(json.dumps({"schema_version": "1.0", "execution": {"argv": sys.argv[1:], "value": os.environ.get("PRIVATE_VALUE")}, "results": []}))
"""
        path = os.path.join(check_dir, "check.py")
        with open(path, "w") as output:
            output.write(script)
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)

    def test_dependencies_parameters_environment_and_merge(self):
        self.add_check("first")
        self.add_check("second", ["first"])
        checks = compliance_runner.load_checks(self.root, "test")
        self.assertEqual(["first", "second"], compliance_runner.dependency_order(checks))
        result = compliance_runner.run_category(self.root, "test")
        self.assertEqual("secret", result["second"]["execution"]["value"])
        self.assertEqual(["--expected-version", "13.5"],
                         result["second"]["execution"]["argv"])
        self.assertEqual("second", result["second"]["check"]["id"])

    def test_timeout_is_returned_as_check_error(self):
        self.add_check("slow", body="#!/usr/bin/env python\nimport time\ntime.sleep(5)\n", timeout=.05)
        result = compliance_runner.run_category(self.root, "test")
        self.assertEqual("check timed out", result["slow"]["error"])

    def test_missing_dependency_is_configuration_error(self):
        self.add_check("dependent", ["missing"])
        checks = compliance_runner.load_checks(self.root, "test")
        with self.assertRaises(compliance_runner.ConfigurationError):
            compliance_runner.dependency_order(checks)


if __name__ == "__main__":
    unittest.main()
