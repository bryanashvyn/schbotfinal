# Model routing (token saving)

The main session (Opus) is the advisor. It plans, decides, and reviews. It delegates execution.

- Opus handles directly ONLY: database/schema design, architecture, hard debugging, security, final review of delegated work.
- Delegate to `haiku-worker`: searching, reading/summarizing files, simple edits, running tests, commit messages.
- Delegate to `sonnet-worker`: implementing features from a plan, multi-file edits, ordinary bug fixes, tests.
- Give subagents a precise, self-contained task. Ask for terse results (file:line), not file dumps.
- Do not re-read files a subagent already summarized.
