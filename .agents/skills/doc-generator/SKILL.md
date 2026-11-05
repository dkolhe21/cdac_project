---
name: doc-generator
description: Automatically generates and formats documentation logs and architecture documents.
---

# doc-generator

When invoked via `/doc-generator` or when the user asks to "generate docs", you should act as a strict technical writer:

1. **Format**: Follow the user's preferred format exactly (e.g., ADR for decisions, Keep-a-Changelog for changelogs).
2. **Tone**: Concise, professional, and clear. No fluff.
3. **Action**: Create or update the necessary Markdown files in the `docs/` directory.

### Guidelines for updating logs
- **01_DECISION_LOG.md**: Append new architectural decisions (ADRs). Include Context, Decision, and Consequences.
- **02_PROBLEM_LOG.md**: Document bugs using: Symptom → Reproduction → Root cause → Resolution → Verification → Lesson.
- **03_CHANGELOG.md**: Add bullet points under an "Unreleased" or versioned section.
- **04_TECH_STACK.md**: Ensure new tools/dependencies are added to the table with Version, License, and Why.
- **05_DATA_SAFETY.md**: Ensure any new sensitive files are documented.
