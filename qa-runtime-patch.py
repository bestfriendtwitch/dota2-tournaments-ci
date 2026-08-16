#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source"


def must_replace(relative: str, old: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"patch mismatch for {relative}: expected {count} occurrence(s), found {actual}")
    path.write_text(text.replace(old, new, count))
    print(f"QA_RUNTIME_PATCH=OK file={relative}")


# creation/lifecycle: make publish assertion strict and capture the actual lifecycle response.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''  const publish = owner.getByRole("button", { name: /^ОПУБЛИКОВАТЬ$/i }).first();
  check(await publish.isVisible().catch(() => false), "publish lifecycle action is visible", {}, "High", "owner", "Lifecycle");
  if (await publish.isVisible().catch(() => false)) await clickDialogs(owner, publish, []);
  await owner.waitForTimeout(900);
  text = await body(owner);
  check(/АКТИВЕН|РЕГИСТРАЦ/i.test(text), "published tournament becomes active registration", { text: clip(text) }, "Critical", "owner", "Lifecycle");
''',
    '''  const publish = owner.getByRole("button", { name: /^ОПУБЛИКОВАТЬ$/i }).first();
  check(await publish.isVisible().catch(() => false), "publish lifecycle action is visible", {}, "High", "owner", "Lifecycle");
  const publishResponsePromise = owner.waitForResponse(
    (response) => response.request().method() === "POST" && /\\/api\\/v1\\/tournaments\\/[^/]+\\/lifecycle$/.test(response.url()),
    { timeout: 6000 },
  ).catch(() => null);
  if (await publish.isVisible().catch(() => false)) await clickDialogs(owner, publish, []);
  const publishResponse = await publishResponsePromise;
  const publishBody = publishResponse ? await publishResponse.text().catch(() => "") : "";
  report.metrics.publish = {
    status: publishResponse?.status() ?? null,
    url: publishResponse?.url() ?? null,
    body: clip(publishBody),
  };
  await owner.waitForTimeout(900);
  await goto(owner, "/organizer", "owner");
  text = await body(owner);
  check(!/ЧЕРНОВИК/i.test(text) && /АКТИВЕН/i.test(text), "published tournament becomes active registration", { text: clip(text), response: report.metrics.publish }, "Critical", "owner", "Lifecycle");
''',
)

# The archive UI uses the shorter restore label.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    "/^ВОССТАНОВИТЬ ИЗ КОРЗИНЫ$/i",
    "/^ВОССТАНОВИТЬ(?: ИЗ КОРЗИНЫ)?$/i",
)

# TRASH navigates away from the live organizer card and reports success with a toast.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''  const text = await body(page);
  check(expected.test(text), `lifecycle ${label} reaches expected UI state`, { text: clip(text) }, "High", "owner", "Lifecycle");
  return true;
''',
    '''  const text = await body(page);
  const expectedReached = expected.test(text) || (/trash/i.test(label) && /перемещён в корзину/i.test(text));
  check(expectedReached, `lifecycle ${label} reaches expected UI state`, { text: clip(text) }, "High", "owner", "Lifecycle");
  return true;
''',
)

# Hard delete succeeds on the archive page; it does not redirect to the create form.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''    const text = await body(owner);
    check(/Создать турнир/i.test(text), "hard-deleted isolated tournament disappears and create UI returns", { text: clip(text) }, "Critical", "owner", "Hard delete");
''',
    '''    const text = await body(owner);
    const deletedFromArchive = !text.includes(manifest.tournamentName) && /удалён навсегда|0 В КОРЗИНЕ/i.test(text);
    check(deletedFromArchive, "hard-deleted isolated tournament disappears from archive", { text: clip(text) }, "Critical", "owner", "Hard delete");
    await goto(owner, "/organizer", "owner");
    check(/Создать турнир/i.test(await body(owner)), "create UI is available after hard delete", { text: clip(await body(owner)) }, "High", "owner", "Hard delete");
''',
)

# /organizer/audit has client assets but is not a route; smoke the real organizer surface instead.
must_replace(
    "apps/e2e/qa/max-browser-extra-v3.mjs",
    '''  await goto(owner, "/organizer/audit", "owner");
  check(!/Нет прав|Требуется Discord/i.test(await body(owner)), "owner audit page remains accessible after mass workflow", {}, "Medium", "owner", "Audit");
''',
    '''  await goto(owner, "/organizer", "owner");
  check(!/Нет прав|Требуется Discord|404/i.test(await body(owner)), "owner organizer surface remains accessible after mass workflow", {}, "Medium", "owner", "Organizer smoke");
''',
)

# Full-flow: diagnose the one-off identity failure with page text.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''    check(identityVisible, `${key}: expected identity visible`, { expected: user.discordUsername, displayName: user.displayName }, "High", key, "Auth");
''',
    '''    check(identityVisible, `${key}: expected identity visible`, { expected: user.discordUsername, displayName: user.displayName, text: clip(text) }, "High", key, "Auth");
''',
)

# Do not treat a non-route as an organizer permission smoke target.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''  for (const target of ["/organizer", "/organizer/draft", "/organizer/bracket", "/organizer/streams", "/organizer/audit", "/organizer/archive", "/admin", "/verification", "/notifications"]) {
''',
    '''  for (const target of ["/organizer", "/organizer/draft", "/organizer/bracket", "/organizer/streams", "/organizer/archive", "/admin", "/verification", "/notifications"]) {
''',
)

# Responsive failures now name the actual elements extending outside the viewport.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''        const geometry = await page.evaluate(() => ({
          innerWidth: window.innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          bodyScrollWidth: document.body.scrollWidth,
        }));
''',
    '''        const geometry = await page.evaluate(() => {
          const innerWidth = window.innerWidth;
          const overflowers = [...document.querySelectorAll("body *")]
            .map((el) => {
              const rect = el.getBoundingClientRect();
              const style = getComputedStyle(el);
              return {
                tag: el.tagName.toLowerCase(),
                id: el.id || null,
                className: typeof el.className === "string" ? el.className.slice(0, 160) : null,
                text: (el.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 120),
                left: Math.round(rect.left),
                right: Math.round(rect.right),
                width: Math.round(rect.width),
                position: style.position,
                overflowX: style.overflowX,
              };
            })
            .filter((item) => item.width > 0 && (item.right > innerWidth + 1 || item.left < -1))
            .sort((a, b) => Math.max(b.right - innerWidth, -b.left) - Math.max(a.right - innerWidth, -a.left))
            .slice(0, 24);
          return {
            innerWidth,
            scrollWidth: document.documentElement.scrollWidth,
            bodyScrollWidth: document.body.scrollWidth,
            overflowers,
          };
        });
''',
)

# Accessibility failures now include exact offending DOM snippets.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''        const buttonsWithoutName = [...document.querySelectorAll("button")].filter((el) => !(el.innerText || el.getAttribute("aria-label") || el.getAttribute("title"))?.trim()).length;
        const linksWithoutName = [...document.querySelectorAll("a")].filter((el) => !(el.innerText || el.getAttribute("aria-label") || el.getAttribute("title"))?.trim()).length;
        return { duplicateIds: [...new Set(duplicateIds)], broken, buttonsWithoutName, linksWithoutName };
''',
    '''        const unnamedButtons = [...document.querySelectorAll("button")]
          .filter((el) => !(el.innerText || el.getAttribute("aria-label") || el.getAttribute("title"))?.trim())
          .map((el) => el.outerHTML.slice(0, 500));
        const unnamedLinks = [...document.querySelectorAll("a")]
          .filter((el) => !(el.innerText || el.getAttribute("aria-label") || el.getAttribute("title"))?.trim())
          .map((el) => el.outerHTML.slice(0, 500));
        return {
          duplicateIds: [...new Set(duplicateIds)], broken,
          buttonsWithoutName: unnamedButtons.length,
          linksWithoutName: unnamedLinks.length,
          unnamedButtons, unnamedLinks,
        };
''',
)

# Result review panel loads asynchronously; wait before classifying it as missing.
must_replace(
    "apps/e2e/qa/max-browser-audit-v2.mjs",
    '''    const accept = owner.getByRole("button", { name: /^ПРИНЯТЬ$/i }).first();
    if (!(await accept.isVisible().catch(() => false))) {
''',
    '''    const accept = owner.getByRole("button", { name: /^ПРИНЯТЬ$/i }).first();
    await accept.waitFor({ state: "visible", timeout: 5000 }).catch(() => undefined);
    if (!(await accept.isVisible().catch(() => false))) {
''',
)

# Lobby discovery is asynchronous because captains probe only their eligible active matches.
must_replace(
    "apps/e2e/qa/max-match-ops-v3.mjs",
    '''    const button = page.getByRole("button", { name: /СОЗДАТЬ ЛОББИ/i }).first();
    if (await button.isVisible().catch(() => false)) { creatorKey = key; creatorPage = page; break; }
''',
    '''    const button = page.getByRole("button", { name: /СОЗДАТЬ ЛОББИ/i }).first();
    await button.waitFor({ state: "visible", timeout: 5000 }).catch(() => undefined);
    if (await button.isVisible().catch(() => false)) { creatorKey = key; creatorPage = page; break; }
''',
)

print("QA_RUNTIME_PATCH_SET=diagnostics-v1")
