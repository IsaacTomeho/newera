# MergeGuard Verification Report

## Pull Request Context
- Repo: newera
- Diff range: HEAD...HEAD
- Files analyzed: 1
- Total lines changed (code files): 60

## Trust Score
- Overall trust score (0-100): 70
- Risk tier: Medium
- Gate decision: Review required

## Risk Drivers
- Test coverage gap
- Security-sensitive change

## Suggested Test Additions
- Add unit tests for landing/script.js covering success and failure paths.
- Add negative-path tests for auth/permission handling in landing/script.js.

## File-Level Findings
- `landing/script.js` (+60/-0) flags: missing-tests, security
