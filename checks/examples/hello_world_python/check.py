#!/usr/bin/env python
from __future__ import print_function

import argparse
import datetime
import json
import os
import socket
import uuid


def main():
    parser = argparse.ArgumentParser(description="Example Python compliance check")
    parser.add_argument("--ParameterA", required=True)
    args = parser.parse_args()

    response = {
        "schema_version": "1.0",
        "execution": {
            "execution_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "hostname": socket.gethostname(),
            "environment": "EXAMPLE",
            "collector_version": "1.0.0",
        },
        "results": [
            {
                "resource_id": "PythonExample",
                "status": "PASS",
                "compliance_state": "COMPLIANT",
                "severity": "INFO",
                "score": 100,
                "summary": "Python example check completed successfully",
                "metrics": {"result_count": 1},
                "facts": {
                    "parameter_a": args.ParameterA,
                    "variable_a": os.environ.get("VariableA"),
                    "language": "python",
                },
                "findings": [],
                "remediation": None,
            }
        ],
    }
    print(json.dumps(response, sort_keys=True))


if __name__ == "__main__":
    main()
