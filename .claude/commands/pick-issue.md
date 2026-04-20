# /pick-issue

## 0 — Check for orphaned issues first
Use linear-server MCP to find any issues with status "In Progress".
If found: show list (ID, title, last updated). Ask user: "Resume one or start fresh?"
- Resume → skip to Step 4 with that issue
- Ignore → comment on orphan: "[Agent] Prior session ended without closing. Ignored [timestamp]." then continue to Step 1.

## 1 — Fetch real backlog from Linear
Use linear-server MCP tools to get real issues. No inventing, guessing, or recalling from memory.
Filter: status "Ready" first, then "Todo". Sort: High before Medium.

## 2 — Confirm with user
Show before acting: ID, title, project, priority, full description.
Ask: "Proceed with this issue?" Wait for confirmation. If no → next issue, repeat.

## 3 — Log start in Linear
Via MCP:
1. Set status → "In Progress"
2. Post comment:
   "[Agent] 🚀 Started
    Time: [timestamp]
    Plan: [2-3 lines]
    Files: [estimated list]"
If status update fails → stop and report error.

## 4 — Build task prompt for @coder
Use only real issue data. Include:
- What to build (from issue title + description)
- Likely files (from CLAUDE.md)
- Which context/ files to read first
- Module constraints (from module CLAUDE.md)

## 5 — Invoke @coder
Pass the task prompt. When done, post MCP comment:
"[Agent] ✅ Implementation done
 Files changed: [list with one-line summary each]
 Assumptions: [coder's assumptions]
 How to verify: [exact steps]"

## 6 — Parallel validation
Post MCP comment: "[Agent] 🔍 Running @reviewer + @test-runner in parallel"
Invoke @reviewer and @test-runner simultaneously.

If both pass, post:
"[Agent] ✅ Validation passed
 Reviewer: APPROVED — [verdict]
 Tests: [X passed, Y failed]"

If either fails, post:
"[Agent] ❌ Validation failed
 Reviewer: [blockers]
 Tests: [failures with file:line and error]
 Action: retrying with @coder."

## 7 — Close or iterate

**Both pass:**
- Set status → "Done" via MCP
- Confirm to user.

**Either fails:**
- Keep status "In Progress" (never leave in ambiguous state)
- Re-invoke @coder with exact reviewer/test-runner feedback
- Repeat steps 5 → 6
- After 2 failed iterations:
  - Set status → "Triage" via MCP
  - Post: "[Agent] ⚠️ Blocked after 2 iterations. Needs human review. Last error: [description]"
  - Stop and report to user.

## Always — Session summary (success, failure, or interruption)
Post final MCP comment on the issue:
"[Agent] 📋 Session summary
 Start: [timestamp] | End: [timestamp]
 Final status: [Done / Triage / Interrupted]
 Coder iterations: [n]
 Reviewer: [verdict]
 Tests: [X/Y passed]"