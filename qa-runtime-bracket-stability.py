#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source"


def must_replace(relative: str, old: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"bracket stability patch mismatch for {relative}: expected {count} occurrence(s), found {actual}")
    path.write_text(text.replace(old, new, count))
    print(f"QA_RUNTIME_BRACKET_STABILITY=OK file={relative}")


# CaptainResultPanel and organizer review panels hydrate asynchronously after navigation.
# The previous harness sampled controls immediately after DOMContentLoaded, which produced a
# non-deterministic false High: one run missed bracket-40 while the next missed draft-byes-36,
# even though the other scenario completed the same result workflow. Wait for initial network
# activity to settle before deciding that a role has no actionable result/review control.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''      await goto(page, "/?view=bracket", key);\n      const button = page.getByRole("button", { name: /СООБЩИТЬ СЧЁТ/i }).first();\n      if (await button.isVisible().catch(() => false)) {\n''',
    '''      await goto(page, "/?view=bracket", key);\n      await page.waitForLoadState("networkidle", { timeout: 2_500 }).catch(() => undefined);\n      await page.waitForTimeout(150);\n      const button = page.getByRole("button", { name: /СООБЩИТЬ СЧЁТ/i }).first();\n      if (await button.isVisible().catch(() => false)) {\n''',
)

must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''    await goto(owner, "/organizer/bracket", "owner");\n    const accept = owner.getByRole("button", { name: /^ПРИНЯТЬ$/i }).first();\n''',
    '''    await goto(owner, "/organizer/bracket", "owner");\n    await owner.waitForLoadState("networkidle", { timeout: 2_500 }).catch(() => undefined);\n    await owner.waitForTimeout(150);\n    const accept = owner.getByRole("button", { name: /^ПРИНЯТЬ$/i }).first();\n''',
)

print("QA_RUNTIME_BRACKET_STABILITY_SET=async-result-panels-v1")
