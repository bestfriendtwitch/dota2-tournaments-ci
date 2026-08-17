#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source"


def must_replace(relative: str, old: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"postpatch mismatch for {relative}: expected {count} occurrence(s), found {actual}")
    path.write_text(text.replace(old, new, count))
    print(f"QA_RUNTIME_POSTPATCH=OK file={relative}")


# The check-in card re-renders after the undo action, so a locator rooted in the old button
# can no longer find the replacement control. There is exactly one unchecked participant in
# this isolated scenario; re-query all restore buttons and click the first visible/enabled one.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''    const restoreCheckin = overrideCard.getByRole("button", { name: /ПОДТВЕРДИТЬ CHECK-IN/i }).first();
    if (await restoreCheckin.isVisible().catch(() => false) && await restoreCheckin.isEnabled().catch(() => false)) {
      await clickDialogs(owner, restoreCheckin, ["QA override restore"]);
    }
    await owner.waitForTimeout(500);
''',
    '''    const restoreButtons = owner.getByRole("button", { name: /ПОДТВЕРДИТЬ CHECK-IN/i });
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
''',
)

# Every synthetic Twitch identity in this scenario is registered and accepted before check-in closes.
# A disabled opt-in is therefore unexpected and should be diagnosed as a real High failure, not accepted
# as a generic eligibility gate. Capture the actual panel explanation to make failures actionable.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''      if (!(await enable.isEnabled().catch(() => false))) {
        const note = await streamPage.locator(".inline-note").first().textContent().catch(() => "");
        check(Boolean(note?.trim()), "ineligible Twitch-linked participant sees an explanation for disabled stream opt-in", { note: clip(note || "") }, "Medium", streamKey, "Streams eligibility");
        guardedStreamerSeen = true;
        continue;
      }
''',
    '''      if (!(await enable.isEnabled().catch(() => false))) {
        const note = await streamPage.locator(".my-tournament-stream-copy p").first().textContent().catch(() => "");
        check(false, "accepted Twitch-linked participant has enabled stream opt-in", { note: clip(note || ""), text: clip(await body(streamPage)) }, "High", streamKey, "Streams eligibility");
        guardedStreamerSeen = true;
        continue;
      }
''',
)

# Regular rounds are BO1, but the grand final is BO3 in these fixtures. The old harness always
# submitted 1:0, which is valid in BO1 but rejected before organizer review in the BO3 final.
# Read BO from the same captain result card and submit the minimum valid winning score.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''    const answers = ["1:0", "", true];
''',
    '''    const resultCardText = await submitting.button.locator("xpath=ancestor::article[1]").innerText().catch(() => "");
    const reportedScore = /BO5/i.test(resultCardText) ? "3:0" : /BO3/i.test(resultCardText) ? "2:0" : "1:0";
    const answers = [reportedScore, "", true];
''',
)

# Product requirement changed from snake boundaries to strict repeated captain order.
# Keep Max QA on the existing v3 workflow but patch its order assertion at runtime.
must_replace(
    "infra/qa/run-max-browser-audit-v3.sh",
    '''const expectedKey = roundNo % 2 === 1 ? captains[position] : captains[captains.length - 1 - position];''',
    '''const expectedKey = captains[position];''',
)
must_replace(
    "infra/qa/run-max-browser-audit-v3.sh",
    '''snake captain order''',
    '''strict round-robin captain order''',
)

# Issue #113 removed the separate user-facing rules page. Creation still validates the
# tournament name, while registration now happens directly from the stage-driven home workspace.
for obsolete in (
    '  await owner.getByLabel(/Правила турнира/i).fill("");\n',
    '  check(await owner.getByLabel(/Правила турнира/i).evaluate((el) => !el.validity.valid), "browser validation rejects empty rules", {}, "Medium", "owner", "Creation validation");\n',
    '  await owner.getByLabel(/Правила турнира/i).fill("QA browser rules v3. Registration, approval and check-in are tested through the real UI.");\n',
):
    must_replace("apps/e2e/qa/max-browser-extra-v3.mjs", obsolete, "")

must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    'await goto(page, "/?view=rules", key);',
    'await goto(page, "/", key);',
)
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    'await goto(first, "/?view=rules", firstKey);',
    'await goto(first, "/", firstKey);',
)
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    'getByRole("button", { name: /ПРИНИМАЮ ПРАВИЛА И РЕГИСТРИРУЮСЬ/i })',
    'getByRole("button", { name: /ЗАРЕГИСТРИРОВАТЬСЯ/i })',
    count=2,
)

# Replacement history is hydrated asynchronously after returning from the organizer decision.
# Wait for the accepted state instead of sampling the first post-navigation render.
must_replace(
    "apps/e2e/qa/max-match-ops-v3.mjs",
    '''  await goto(requesterPage, "/?view=bracket", requesterKey);
  const requesterText = await body(requesterPage);''',
    '''  await goto(requesterPage, "/?view=bracket", requesterKey);
  await requesterPage.waitForFunction(() => /ПРИНЯТА|принята|ACCEPTED/i.test(document.body?.innerText || ""), undefined, { timeout: 5_000 }).catch(() => undefined);
  const requesterText = await body(requesterPage);''',
)

# During an active draft the new home screen embeds DraftClient directly; there is intentionally
# no legacy hero CTA to /draft. Preserve the regression intent by asserting the embedded live
# workspace, its turn clock, and that the interaction remains on the home stage.
must_replace(
    "apps/e2e/qa/user-reported-regression-v1.mjs",
    '''async function homeDraftCtaCheck() {
  const page = pages.get("player01");
  await goto(page, "/", "player01");
  const button = page.locator(".hero-cta button.primary").first();
  const label = (await button.innerText().catch(() => "")).trim();
  check(/ДРАФТ/i.test(label) && !/ПОДГОТОВКА ДРАФТА/i.test(label), "home primary CTA is an action that opens the draft", { label }, "High", "player01", "Home CTA");
  if (await button.isVisible().catch(() => false)) {
    await button.click();
    await page.waitForURL((url) => url.pathname === "/draft", { timeout: 8_000 }).catch(() => undefined);
    check(new URL(page.url()).pathname === "/draft", "home draft CTA navigates to /draft instead of showing unavailable-action toast", { url: page.url() }, "Critical", "player01", "Home CTA");
  }
}''',
    '''async function homeDraftCtaCheck() {
  const page = pages.get("player01");
  await goto(page, "/", "player01");
  const embeddedDraft = page.locator(".adaptive-stage-embedded .draft-page").first();
  await embeddedDraft.waitFor({ state: "visible", timeout: 8_000 }).catch(() => undefined);
  check(await embeddedDraft.isVisible().catch(() => false), "home embeds the active live-draft workspace", { url: page.url() }, "High", "player01", "Home draft workspace");
  const clock = page.locator(".adaptive-stage-embedded .draft-clock").first();
  const clockText = (await clock.innerText().catch(() => "")).trim();
  check(Boolean(clockText) && clockText !== "—:—", "embedded home draft exposes the live turn clock", { clockText }, "Critical", "player01", "Home draft workspace");
  check(new URL(page.url()).pathname === "/", "active draft stays actionable on the stage-driven home workspace", { url: page.url() }, "Critical", "player01", "Home draft workspace");
}''',
)

print("QA_RUNTIME_POSTPATCH_SET=final-flow-v1+strict-round-robin+adaptive-workspace-v1")
