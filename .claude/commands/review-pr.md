# Review current changes

Run a full review of recent changes using parallel agents.

Spawn in parallel:
1. @reviewer — code review for safety, correctness, and conventions
2. @test-runner — run test suite + API smoke tests + SQL safety check

Wait for both to complete, then synthesize:
- If both pass: report READY, suggest @linear-coordinator marks the issue Done
- If either fails: report blockers clearly, suggest what @coder needs to fix
