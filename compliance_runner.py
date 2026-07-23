#!/usr/bin/env python
from __future__ import print_function

import argparse
import json
import os
import signal
import subprocess
import sys
import threading

try:
    import yaml
except ImportError:
    yaml = None


class ConfigurationError(Exception):
    pass


def load_checks(checks_root, category):
    if yaml is None:
        raise ConfigurationError("PyYAML is required (install it with: pip install PyYAML)")
    category_dir = os.path.abspath(os.path.join(checks_root, category))
    checks_root = os.path.abspath(checks_root)
    if os.path.commonprefix([category_dir + os.sep, checks_root + os.sep]) != checks_root + os.sep:
        raise ConfigurationError("category must be below the checks directory")
    if not os.path.isdir(category_dir):
        raise ConfigurationError("category does not exist: %s" % category)

    checks = {}
    for current_dir, dirnames, filenames in os.walk(category_dir):
        dirnames.sort()
        for manifest_name in ("manifest.yml", "manifest.yaml"):
            if manifest_name not in filenames:
                continue
            manifest_path = os.path.join(current_dir, manifest_name)
            with open(manifest_path, "r") as manifest_file:
                manifest = yaml.safe_load(manifest_file)
            validate_manifest(manifest, current_dir, manifest_path)
            check_id = manifest["id"]
            if check_id in checks:
                raise ConfigurationError("duplicate check id: %s" % check_id)
            checks[check_id] = {
                "directory": current_dir,
                "manifest": manifest,
                "manifest_path": manifest_path,
            }
            break
    return checks


def validate_manifest(manifest, check_dir, manifest_path):
    if not isinstance(manifest, dict):
        raise ConfigurationError("manifest must be a mapping: %s" % manifest_path)
    for field in ("id", "name", "enabled", "entrypoint", "timeout"):
        if field not in manifest:
            raise ConfigurationError("missing '%s' in %s" % (field, manifest_path))
    if manifest["id"] != os.path.basename(check_dir):
        raise ConfigurationError("check id must match directory name in %s" % manifest_path)
    if not isinstance(manifest["enabled"], bool):
        raise ConfigurationError("enabled must be true or false in %s" % manifest_path)
    try:
        timeout = float(manifest["timeout"])
    except (TypeError, ValueError):
        raise ConfigurationError("timeout must be a number in %s" % manifest_path)
    if timeout <= 0:
        raise ConfigurationError("timeout must be greater than zero in %s" % manifest_path)
    for field in ("variables", "parameters"):
        value = manifest.get(field, {})
        if value is None:
            manifest[field] = {}
        elif not isinstance(value, dict):
            raise ConfigurationError("%s must be a mapping in %s" % (field, manifest_path))
    requires = manifest.get("requires", [])
    if requires is None:
        manifest["requires"] = []
    elif not isinstance(requires, list):
        raise ConfigurationError("requires must be a list in %s" % manifest_path)


def dependency_order(checks):
    enabled = dict((check_id, check) for check_id, check in checks.items()
                   if check["manifest"]["enabled"])
    visiting = set()
    visited = set()
    ordered = []

    def visit(check_id, trail):
        if check_id in visited:
            return
        if check_id in visiting:
            raise ConfigurationError("dependency cycle: %s" % " -> ".join(trail + [check_id]))
        visiting.add(check_id)
        for dependency in enabled[check_id]["manifest"].get("requires", []):
            if dependency not in checks:
                raise ConfigurationError("check '%s' requires missing check '%s'" %
                                         (check_id, dependency))
            if not checks[dependency]["manifest"]["enabled"]:
                raise ConfigurationError("check '%s' requires disabled check '%s'" %
                                         (check_id, dependency))
            visit(dependency, trail + [check_id])
        visiting.remove(check_id)
        visited.add(check_id)
        ordered.append(check_id)

    for check_id in sorted(enabled):
        visit(check_id, [])
    return ordered


def stringify(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value)


def build_command(entrypoint, parameters):
    command = [entrypoint]
    for key in sorted(parameters):
        option = "--" + str(key).replace("_", "-")
        value = parameters[key]
        if isinstance(value, bool):
            if value:
                command.append(option)
        elif isinstance(value, list):
            for item in value:
                command.extend([option, stringify(item)])
        else:
            command.extend([option, stringify(value)])
    return command


def execute_check(check):
    manifest = check["manifest"]
    entrypoint = os.path.abspath(os.path.join(check["directory"], manifest["entrypoint"]))
    if not entrypoint.startswith(os.path.abspath(check["directory"]) + os.sep):
        raise ConfigurationError("entrypoint escapes check directory for '%s'" % manifest["id"])
    if not os.path.isfile(entrypoint):
        raise ConfigurationError("entrypoint does not exist for '%s': %s" %
                                 (manifest["id"], entrypoint))

    environment = os.environ.copy()
    for key, value in manifest.get("variables", {}).items():
        environment[str(key)] = stringify(value)

    command = build_command(entrypoint, manifest.get("parameters", {}))
    process = subprocess.Popen(
        command,
        cwd=check["directory"],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid,
    )
    timed_out = [False]

    def terminate():
        if process.poll() is None:
            timed_out[0] = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass

    timer = threading.Timer(float(manifest["timeout"]), terminate)
    timer.daemon = True
    timer.start()
    stdout, stderr = process.communicate()
    timer.cancel()
    stdout = stdout.decode("utf-8", "replace") if not isinstance(stdout, str) else stdout
    stderr = stderr.decode("utf-8", "replace") if not isinstance(stderr, str) else stderr

    if timed_out[0]:
        return {"error": "check timed out", "timeout": manifest["timeout"], "stderr": stderr}
    if process.returncode != 0:
        return {"error": "check exited with a non-zero status", "exit_code": process.returncode,
                "stderr": stderr}
    try:
        response = json.loads(stdout)
    except ValueError as error:
        return {"error": "check returned invalid JSON: %s" % error, "stderr": stderr,
                "stdout": stdout}
    if not isinstance(response, dict):
        return {"error": "check response must be a JSON object", "stderr": stderr}
    return response


def run_category(checks_root, category):
    checks = load_checks(checks_root, category)
    output = {}
    for check_id in dependency_order(checks):
        response = execute_check(checks[check_id])
        response["check"] = checks[check_id]["manifest"].copy()
        output[check_id] = response
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run compliance checks in dependency order")
    parser.add_argument("category", help="category below the checks directory")
    parser.add_argument("--checks-root", default=os.path.join(os.path.dirname(__file__), "checks"),
                        help="checks directory (default: checks beside this script)")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON output")
    args = parser.parse_args(argv)
    if yaml is None:
        parser.error("PyYAML is required (install it with: pip install PyYAML)")
    try:
        result = run_category(args.checks_root, args.category)
    except (ConfigurationError, OSError) as error:
        print("error: %s" % error, file=sys.stderr)
        return 2
    indent = 2 if args.pretty else None
    print(json.dumps(result, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
