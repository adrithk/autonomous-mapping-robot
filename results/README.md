# Test result records

This directory is the evidence store for bench, robot, and integrated physical tests. No physical results were present when the engineering harness was created on 2026-09-01.

Name each report `YYYY-MM-DD-short-test-name.md`. Put larger associated artifacts in a same-named directory and link them from the report. Avoid committing secrets or needlessly large raw data; document durable storage when an artifact must live elsewhere.

Use this structure:

```md
# Test name

**Date:**
**Operator:**
**Git commit:**
**Test level:** Bench | Robot | Integrated
**Hardware revision:**
**Configuration:**

## Goal
## Acceptance criteria
## Safety setup
## Environment and equipment
## Procedure
## Measurements and observations
## Result
Pass | Fail | Inconclusive

## Anomalies
## Artifacts
## Follow-up
```

Use units for every measurement, preserve raw observations, and state pass/fail only against criteria written before the test. Link the result from its execution plan and from the roadmap when it changes milestone evidence.
