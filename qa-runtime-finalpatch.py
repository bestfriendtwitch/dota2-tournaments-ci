#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source"
path = ROOT / "apps/e2e/qa/max-match-ops-v3.mjs"
text = path.read_text()
old = '''    await goto(page, "/?view=bracket", key);
    const submit = page.getByRole("button", { name: /ОТПРАВИТЬ ЗАЯВКУ/i }).first();
    if (!(await submit.isVisible().catch(() => false))) continue;
    const outgoing = page.getByLabel(/Кого заменить/i);
    const incoming = page.getByLabel(/Кто входит/i);
    if (!(await outgoing.isVisible().catch(() => false)) || !(await incoming.isVisible().catch(() => false))) continue;'''
new = '''    await goto(page, "/?view=bracket", key);
    const replacementCard = page.locator(".replacement-request-card").first();
    await replacementCard.waitFor({ state: "visible", timeout: 5_000 }).catch(() => undefined);
    const submit = replacementCard.getByRole("button", { name: /ОТПРАВИТЬ ЗАЯВКУ/i }).first();
    if (!(await submit.isVisible().catch(() => false))) continue;
    const outgoing = replacementCard.getByLabel(/Кого заменить/i);
    const incoming = replacementCard.getByLabel(/Кто входит/i);
    if (!(await outgoing.isVisible().catch(() => false)) || !(await incoming.isVisible().catch(() => false))) continue;'''
actual = text.count(old)
if actual != 1:
    raise SystemExit(f"qa finalpatch mismatch: expected 1, found {actual}")
path.write_text(text.replace(old, new, 1))
print("QA_RUNTIME_FINALPATCH=replacement-hydration-v1")
