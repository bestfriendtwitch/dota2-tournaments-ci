#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source"


def replace_once(relative: str, old: str, new: str, label: str) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual != 1:
        raise SystemExit(f"{label} mismatch in {relative}: expected 1, found {actual}")
    path.write_text(text.replace(old, new, 1))
    print(f"QA_RUNTIME_FINALPATCH={label}")


replace_once(
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

replace_once(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''  await goto(owner, "/organizer", "owner");
  const pendingBefore = await owner.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count();
  check(pendingBefore === manifest.participantCount, "owner sees all pending applications", { pendingBefore, expected: manifest.participantCount }, "High", "owner", "Approval");
  let accepted = 0;
  for (let index = 0; index < manifest.participantCount; index += 1) {
    const accept = owner.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).first();
    if (!(await accept.isVisible().catch(() => false))) break;
    await accept.click();
    await owner.waitForTimeout(400);
    accepted += 1;
  }
  await goto(owner, "/organizer", "owner");
  check(accepted === manifest.participantCount, "owner accepts all applications through UI", { accepted }, "Critical", "owner", "Approval");
  check(await owner.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count() === 0, "no pending approval buttons remain", {}, "High", "owner", "Approval");

  await goto(first, "/", firstKey);
  check(await first.getByRole("button", { name: /ОТМЕНИТЬ ЗАЯВКУ/i }).count() === 0, "accepted participant cannot self-cancel in approval mode", {}, "Critical", firstKey, "Registration permissions");

  await goto(owner, "/organizer", "owner");
  const openCheckin = owner.getByRole("button", { name: /ОТКРЫТЬ СЕЙЧАС/i }).first();
  check(await openCheckin.isVisible().catch(() => false), "owner can open check-in", {}, "High", "owner", "Check-in");
  if (await openCheckin.isVisible().catch(() => false)) { await openCheckin.click(); await owner.waitForTimeout(700); }

  let checkedIn = 0;
  for (const key of playerKeys) {
    const page = pages.get(key);
    await goto(page, "/", key);
    const button = page.getByRole("button", { name: /ПРОЙТИ CHECK-IN|ПОДТВЕРДИТЬ УЧАСТИЕ/i }).first();
    if (!(await button.isVisible().catch(() => false))) {
      defect("High", key, "Check-in", "Player check-in button is missing", { text: clip(await body(page)) });
      continue;
    }
    await button.click();
    await page.waitForTimeout(500);
    if (/CHECK-IN ПРОЙДЕН/i.test(await body(page))) checkedIn += 1;
  }
  check(checkedIn === manifest.participantCount, "all participants check in through their own browser sessions", { checkedIn }, "Critical", "players", "Check-in");

  await goto(owner, "/organizer", "owner");
  let readyCount = await owner.locator(".checkin-ready").count();
  check(readyCount === manifest.participantCount, "owner sees all participants checked in", { readyCount }, "Critical", "owner", "Check-in");

  const undoButtons = owner.getByRole("button", { name: /ОТМЕНИТЬ CHECK-IN/i });
  let undoCheckin = null;
  for (let index = 0; index < await undoButtons.count(); index += 1) {
    const candidate = undoButtons.nth(index);
    if (await candidate.isVisible().catch(() => false) && await candidate.isEnabled().catch(() => false)) {
      undoCheckin = candidate;
      break;
    }
  }
  if (undoCheckin) {
    const overrideCard = undoCheckin.locator("xpath=ancestor::*[contains(concat(' ', normalize-space(@class), ' '), ' staff-registration ')][1]");
    await clickDialogs(owner, undoCheckin, ["QA override off"]);
    await owner.waitForTimeout(500);
    readyCount = await owner.locator(".checkin-ready").count();
    check(readyCount === manifest.participantCount - 1, "organizer can remove one check-in", { readyCount }, "High", "owner", "Check-in override");
    const restoreButtons = owner.getByRole("button", { name: /ПОДТВЕРДИТЬ CHECK-IN/i });
    let restored = false;
    for (let index = 0; index < await restoreButtons.count(); index += 1) {
      const restoreCheckin = restoreButtons.nth(index);
      if (await restoreCheckin.isVisible().catch(() => false) && await restoreCheckin.isEnabled().catch(() => false)) {
        await clickDialogs(owner, restoreCheckin, ["QA override restore"]);
        restored = true;
        break;
      }
    }
    check(restored, "organizer can restore the removed check-in", {}, "High", "owner", "Check-in override");
    await owner.waitForTimeout(650);
    readyCount = await owner.locator(".checkin-ready").count();
    check(readyCount === manifest.participantCount, "organizer check-in override restores state", { readyCount }, "High", "owner", "Check-in override");
  } else {
    check(false, "organizer check-in undo control is available on a checked-in participant", {}, "Medium", "owner", "Check-in override");
  }

  const closeCheckin = owner.getByRole("button", { name: /ЗАКРЫТЬ CHECK-IN/i }).first();
  check(await closeCheckin.isVisible().catch(() => false), "owner can close check-in", {}, "High", "owner", "Check-in");
  if (await closeCheckin.isVisible().catch(() => false)) await clickDialogs(owner, closeCheckin, []);
  await owner.waitForTimeout(500);
''',
    '''  await goto(owner, "/organizer", "owner");
  const organizerSurface = owner.locator(".adaptive-direct-organizer").first();
  await organizerSurface.waitFor({ state: "visible", timeout: 5_000 });
  const pendingBefore = await organizerSurface.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count();
  check(pendingBefore === manifest.participantCount, "owner sees all pending applications", { pendingBefore, expected: manifest.participantCount }, "High", "owner", "Approval");
  let accepted = 0;
  for (let index = 0; index < manifest.participantCount; index += 1) {
    const accept = organizerSurface.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).first();
    if (!(await accept.isVisible().catch(() => false))) break;
    await accept.click();
    await owner.waitForTimeout(400);
    accepted += 1;
  }
  await goto(owner, "/organizer", "owner");
  const approvalSurfaceAfter = owner.locator(".adaptive-direct-organizer").first();
  await approvalSurfaceAfter.waitFor({ state: "visible", timeout: 5_000 });
  check(accepted === manifest.participantCount, "owner accepts all applications through UI", { accepted }, "Critical", "owner", "Approval");
  check(await approvalSurfaceAfter.getByRole("button", { name: "ПРИНЯТЬ", exact: true }).count() === 0, "no pending approval buttons remain", {}, "High", "owner", "Approval");

  await goto(first, "/", firstKey);
  check(await first.getByRole("button", { name: /ОТМЕНИТЬ ЗАЯВКУ/i }).count() === 0, "accepted participant cannot self-cancel in approval mode", {}, "Critical", firstKey, "Registration permissions");

  await goto(owner, "/organizer", "owner");
  const checkinSurface = owner.locator(".adaptive-direct-organizer").first();
  await checkinSurface.waitFor({ state: "visible", timeout: 5_000 });
  const openCheckin = checkinSurface.getByRole("button", { name: /ОТКРЫТЬ СЕЙЧАС/i }).first();
  check(await openCheckin.isVisible().catch(() => false), "owner can open check-in", {}, "High", "owner", "Check-in");
  if (await openCheckin.isVisible().catch(() => false)) { await openCheckin.click(); await owner.waitForTimeout(700); }

  let checkedIn = 0;
  for (const key of playerKeys) {
    const page = pages.get(key);
    await goto(page, "/", key);
    const button = page.getByRole("button", { name: /ПРОЙТИ CHECK-IN|ПОДТВЕРДИТЬ УЧАСТИЕ/i }).first();
    if (!(await button.isVisible().catch(() => false))) {
      defect("High", key, "Check-in", "Player check-in button is missing", { text: clip(await body(page)) });
      continue;
    }
    await button.click();
    await page.waitForTimeout(500);
    if (/CHECK-IN ПРОЙДЕН/i.test(await body(page))) checkedIn += 1;
  }
  check(checkedIn === manifest.participantCount, "all participants check in through their own browser sessions", { checkedIn }, "Critical", "players", "Check-in");

  await goto(owner, "/organizer", "owner");
  const checkinSurfaceAfter = owner.locator(".adaptive-direct-organizer").first();
  await checkinSurfaceAfter.waitFor({ state: "visible", timeout: 5_000 });
  let readyCount = await checkinSurfaceAfter.locator(".checkin-ready").count();
  check(readyCount === manifest.participantCount, "owner sees all participants checked in", { readyCount }, "Critical", "owner", "Check-in");

  const undoButtons = checkinSurfaceAfter.getByRole("button", { name: /ОТМЕНИТЬ CHECK-IN/i });
  let undoCheckin = null;
  for (let index = 0; index < await undoButtons.count(); index += 1) {
    const candidate = undoButtons.nth(index);
    if (await candidate.isVisible().catch(() => false) && await candidate.isEnabled().catch(() => false)) {
      undoCheckin = candidate;
      break;
    }
  }
  if (undoCheckin) {
    await clickDialogs(owner, undoCheckin, ["QA override off"]);
    await owner.waitForTimeout(500);
    readyCount = await checkinSurfaceAfter.locator(".checkin-ready").count();
    check(readyCount === manifest.participantCount - 1, "organizer can remove one check-in", { readyCount }, "High", "owner", "Check-in override");
    const restoreButtons = checkinSurfaceAfter.getByRole("button", { name: /ПОДТВЕРДИТЬ CHECK-IN/i });
    let restored = false;
    for (let index = 0; index < await restoreButtons.count(); index += 1) {
      const restoreCheckin = restoreButtons.nth(index);
      if (await restoreCheckin.isVisible().catch(() => false) && await restoreCheckin.isEnabled().catch(() => false)) {
        await clickDialogs(owner, restoreCheckin, ["QA override restore"]);
        restored = true;
        break;
      }
    }
    check(restored, "organizer can restore the removed check-in", {}, "High", "owner", "Check-in override");
    await owner.waitForTimeout(650);
    readyCount = await checkinSurfaceAfter.locator(".checkin-ready").count();
    check(readyCount === manifest.participantCount, "organizer check-in override restores state", { readyCount }, "High", "owner", "Check-in override");
  } else {
    check(false, "organizer check-in undo control is available on a checked-in participant", {}, "Medium", "owner", "Check-in override");
  }

  const closeCheckin = checkinSurfaceAfter.getByRole("button", { name: /ЗАКРЫТЬ CHECK-IN/i }).first();
  check(await closeCheckin.isVisible().catch(() => false), "owner can close check-in", {}, "High", "owner", "Check-in");
  if (await closeCheckin.isVisible().catch(() => false)) await clickDialogs(owner, closeCheckin, []);
  await owner.waitForTimeout(500);
''',
    "organizer-drawer-scope-v1",
)
