#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source"


def replace_exact(relative: str, old: str, new: str, label: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"{label} mismatch in {relative}: expected {count}, found {actual}")
    path.write_text(text.replace(old, new, count))
    print(f"QA_RUNTIME_FINALPATCH={label}")


# Replacement request controls hydrate after bracket navigation. Scope to the real card.
replace_exact(
    "apps/e2e/qa/max-match-ops-v3.mjs",
    '''    await goto(page, "/?view=bracket", key);
    const submit = page.getByRole("button", { name: /ОТПРАВИТЬ ЗАЯВКУ/i }).first();
    if (!(await submit.isVisible().catch(() => false))) continue;
    const outgoing = page.getByLabel(/Кого заменить/i);
    const incoming = page.getByLabel(/Кто входит/i);
    if (!(await outgoing.isVisible().catch(() => false)) || !(await incoming.isVisible().catch(() => false))) continue;''',
    '''    await goto(page, "/?view=bracket", key);
    const replacementCard = page.locator(".replacement-request-card").first();
    await replacementCard.waitFor({ state: "visible", timeout: 5_000 }).catch(() => undefined);
    const submit = replacementCard.getByRole("button", { name: /ОТПРАВИТЬ ЗАЯВКУ/i }).first();
    if (!(await submit.isVisible().catch(() => false))) continue;
    const outgoing = replacementCard.getByLabel(/Кого заменить/i);
    const incoming = replacementCard.getByLabel(/Кто входит/i);
    if (!(await outgoing.isVisible().catch(() => false)) || !(await incoming.isVisible().catch(() => false))) continue;''',
    "replacement-hydration-v1",
)

# On the current adaptive organizer route the legacy surface can remain mounted underneath
# the active direct-organizer drawer. Global role locators therefore see each action twice and
# .first() can point at an element intentionally covered by the backdrop. Scope only the affected
# organizer controls to the active drawer while leaving all behavioral assertions intact.
relative = "apps/e2e/qa/max-browser-extra-v3.mjs"

replace_exact(
    relative,
    '''  const pendingBefore = await owner.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count();''',
    '''  const organizerSurface = owner.locator(".adaptive-direct-organizer").first();
  await organizerSurface.waitFor({ state: "visible", timeout: 5_000 });
  const pendingBefore = await organizerSurface.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count();''',
    "organizer-drawer-pending-v2",
)

replace_exact(
    relative,
    '''    const accept = owner.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).first();''',
    '''    const accept = organizerSurface.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).first();''',
    "organizer-drawer-accept-v2",
)

replace_exact(
    relative,
    '''  check(await owner.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count() === 0, "no pending approval buttons remain", {}, "High", "owner", "Approval");''',
    '''  check(await owner.locator(".adaptive-direct-organizer").first().getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count() === 0, "no pending approval buttons remain", {}, "High", "owner", "Approval");''',
    "organizer-drawer-approval-empty-v2",
)

replace_exact(
    relative,
    '''  const openCheckin = owner.getByRole("button", { name: /ОТКРЫТЬ СЕЙЧАС/i }).first();''',
    '''  const openCheckin = owner.locator(".adaptive-direct-organizer").first().getByRole("button", { name: /ОТКРЫТЬ СЕЙЧАС/i }).first();''',
    "organizer-drawer-open-checkin-v2",
)

replace_exact(
    relative,
    '''  let readyCount = await owner.locator(".checkin-ready").count();''',
    '''  let readyCount = await owner.locator(".adaptive-direct-organizer .checkin-ready").count();''',
    "organizer-drawer-ready-initial-v2",
)

replace_exact(
    relative,
    '''  const undoButtons = owner.getByRole("button", { name: /ОТМЕНИТЬ CHECK-IN/i });''',
    '''  const undoButtons = owner.locator(".adaptive-direct-organizer").first().getByRole("button", { name: /ОТМЕНИТЬ CHECK-IN/i });''',
    "organizer-drawer-undo-v2",
)

replace_exact(
    relative,
    '''    readyCount = await owner.locator(".checkin-ready").count();''',
    '''    readyCount = await owner.locator(".adaptive-direct-organizer .checkin-ready").count();''',
    "organizer-drawer-ready-updates-v2",
    count=2,
)

replace_exact(
    relative,
    '''    const restoreButtons = owner.getByRole("button", { name: /ПОДТВЕРДИТЬ CHECK-IN/i });''',
    '''    const restoreButtons = owner.locator(".adaptive-direct-organizer").first().getByRole("button", { name: /ПОДТВЕРДИТЬ CHECK-IN/i });''',
    "organizer-drawer-restore-v2",
)

replace_exact(
    relative,
    '''  const closeCheckin = owner.getByRole("button", { name: /ЗАКРЫТЬ CHECK-IN/i }).first();''',
    '''  const closeCheckin = owner.locator(".adaptive-direct-organizer").first().getByRole("button", { name: /ЗАКРЫТЬ CHECK-IN/i }).first();''',
    "organizer-drawer-close-checkin-v2",
)

print("QA_RUNTIME_FINALPATCH_SET=replacement-hydration-v1+organizer-drawer-scope-v2")
