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

# The stress scenario used to read body text immediately after route readiness. On a busy
# 64-player render the participant data can hydrate just after that 80ms boundary. Wait for the
# same >=30 synthetic names that the original assertion requires, then keep the original count
# assertion unchanged. This removes timing nondeterminism without weakening coverage.
replace_exact(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''    await goto(page, "/?view=players", role);
    const text = await bodyText(page);''',
    '''    await goto(page, "/?view=players", role);
    const participantNames = Object.entries(manifest.users)
      .filter(([key]) => key !== "owner")
      .map(([, user]) => user.displayName);
    await page.waitForFunction(
      (names) => {
        const text = document.body?.innerText || "";
        return names.filter((name) => text.includes(name)).length >= Math.min(30, names.length);
      },
      participantNames,
      { timeout: 5_000 },
    ).catch(() => undefined);
    const text = await bodyText(page);''',
    "stress-participant-hydration-v1",
)

# run-max-browser-audit-v3.sh first widens the short creation/check-in waits while generating
# an isolated runtime copy. Keep its original source needle intact, but make the generated copy
# assert the current stable participant heading instead of the retired CHECK-IN marker.
replace_exact(
    "infra/qa/run-max-browser-audit-v3.sh",
    '''        'await page.waitForTimeout(180);\\n    if (/CHECK-IN ПРОЙДЕН/i.test(await body(page)))': 'await page.waitForTimeout(500);\\n    if (/CHECK-IN ПРОЙДЕН/i.test(await body(page)))',''',
    '''        'await page.waitForTimeout(180);\\n    if (/CHECK-IN ПРОЙДЕН/i.test(await body(page)))': 'await page.waitForTimeout(500);\\n    const confirmedHeading = page.getByRole("heading", { name: /Участие подтверждено/i }).first();\\n    await confirmedHeading.waitFor({ state: "visible", timeout: 5_000 }).catch(() => undefined);\\n    if (await confirmedHeading.isVisible().catch(() => false))',''',
    "generated-participant-checkin-confirmed-v2",
)

print("QA_RUNTIME_FINALPATCH_SET=replacement-hydration-v1+organizer-drawer-scope-v2+stress-participant-hydration-v1+generated-participant-checkin-confirmed-v2")
