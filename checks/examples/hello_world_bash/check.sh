#!/bin/bash

read hostname < <(uname -n)

cat <<-.
{
  "schema_version": "1.0",
  "execution": {
    "execution_id": "7f1d6cb2-8c95-4c85-b2a0-9f0ce7133f4e",
    "timestamp": "2026-07-22T18:00:00Z",
    "hostname": "${hostname}",
    "environment": "PROD",
    "collector_version": "2.4.1"
  },
  "results": [
    {
      "resource_id": "DatabaseA",
      "status": "FAIL",
      "compliance_state": "NON_COMPLIANT",
      "severity": "HIGH",
      "score": 0,
      "summary": "Oracle Home exceeds patch threshold",
      "metrics": {
	"days_since_patch": 187,
	"required_threshold_days": 90
      },
      "facts": {
	"oracle_home": "/u01/app/oracle/product/19.0.0",
	"release_update": "19.22",
	"last_patch_date": "2026-01-16"
      },
      "findings": [
	{
	  "id": "PATCH_THRESHOLD_EXCEEDED",
	  "severity": "HIGH",
	  "message": "Oracle Home exceeds patch threshold",
	  "evidence": {
	    "days_since_patch": 187,
	    "threshold": 90
	  }
	}
      ],
      "remediation": {
	"owner": "DBA",
	"type": "manual",
	"runbook": "oracle-patching-standard"
      }
    },
    {
      "resource_id": "DatabaseB",
      "status": "FAIL",
      "compliance_state": "NON_COMPLIANT",
      "severity": "HIGH",
      "score": 0,
      "summary": "Oracle Home exceeds patch threshold",
      "metrics": {
	"days_since_patch": 187,
	"required_threshold_days": 90
      },
      "facts": {
	"oracle_home": "/u01/app/oracle/product/19.0.0",
	"release_update": "19.22",
	"last_patch_date": "2026-01-16"
      },
      "findings": [
	{
	  "id": "PATCH_THRESHOLD_EXCEEDED",
	  "severity": "HIGH",
	  "message": "Oracle Home exceeds patch threshold",
	  "evidence": {
	    "days_since_patch": 187,
	    "threshold": 90
	  }
	}
      ],
      "remediation": {
	"owner": "DBA",
	"type": "manual",
	"runbook": "oracle-patching-standard"
      }
    }
  ]
}
.
