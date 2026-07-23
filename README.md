# Compliance check runner

`compliance_runner.py` discovers `manifest.yml` or `manifest.yaml` files below one
category, validates and topologically orders enabled checks, executes each check,
and emits one JSON object keyed by check ID.

## Requirements

- Python 2.7 or newer
- PyYAML (`pip install PyYAML`)
- A POSIX operating system (timeouts terminate the check's entire process group)

Each entrypoint must be executable and have an appropriate shebang, for example
`#!/usr/bin/env python`, `#!/bin/bash`, or `#!/usr/bin/env perl`.

## Usage

```sh
python compliance_runner.py oracle --pretty
python compliance_runner.py oracle --checks-root /path/to/checks --pretty
```

Manifest `parameters` become deterministic command-line options: an
`expected_version: "13.5"` entry becomes `--expected-version 13.5`. True boolean
values become flags, false boolean values are omitted, and list values repeat the
option. Manifest `variables` are added only to that child process's environment,
using their manifest keys exactly.

Every successful check must write one JSON object to stdout. Diagnostics should
go to stderr. The check's response receives a `check` member containing the full
manifest, and all responses are collected as follows:

```json
{
  "oem_agent": {
    "schema_version": "1.0",
    "execution": {},
    "results": [],
    "check": {
      "id": "oem_agent",
      "name": "OEM Agent Validation"
    }
  }
}
```

Timeouts, non-zero exits, and malformed JSON become per-check error objects so
other ordered checks can still run. Invalid manifests, missing/disabled
requirements, duplicate IDs, and dependency cycles are category-level
configuration errors and cause exit status 2.

## Example checks

The `checks/examples` category contains equivalent checks in several languages:

- `hello_world_bash` writes JSON with a Bash heredoc.
- `hello_world_python` serializes its response with Python's standard `json` module.
- `hello_world_perl` serializes its response with Perl's core `JSON::PP` module.

All examples receive `--ParameterA foo` and the private `VariableA=bar`
environment variable. The Python and Perl examples include both values in their
result facts to demonstrate how entrypoints consume manifest configuration.

Some minimal Perl OS packages split `JSON::PP` out of the base Perl installation.
On those systems, install the distribution's `perl-JSON-PP` package or install the
module from CPAN before running the complete examples category.

Run all examples with:

```sh
python compliance_runner.py examples --pretty
```

Run the unit tests with:

```sh
python -m unittest test_compliance_runner
```
# compliance
