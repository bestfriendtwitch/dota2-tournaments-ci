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

print("QA_RUNTIME_POSTPATCH_SET=final-flow-v1+strict-round-robin")
