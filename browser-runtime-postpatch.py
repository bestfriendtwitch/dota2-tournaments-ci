#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source" / "apps" / "e2e" / "tests"


def must_replace(relative: str, old: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f"browser postpatch mismatch for {relative}: expected {count}, found {actual}: {old[:120]!r}")
    path.write_text(text.replace(old, new, count))
    print(f"BROWSER_RUNTIME_POSTPATCH=OK file={relative}")


def regex_replace(relative: str, pattern: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    updated, actual = re.subn(pattern, new, text, count=count, flags=re.S)
    if actual != count:
        raise SystemExit(f"browser postpatch regex mismatch for {relative}: expected {count}, found {actual}: {pattern[:120]!r}")
    path.write_text(updated)
    print(f"BROWSER_RUNTIME_POSTPATCH_REGEX=OK file={relative}")


# A closed participation-confirmation window is represented by an explanatory stage card rather
# than a deliberately failing action button. Staff override after close remains covered below.
regex_replace(
    "checkin-operations.spec.ts",
    r'''    const playerCheckInButton = playerPage\.getByRole\("button", \{ name: /PROYTI_SENTINEL/ \}\);'''.replace("PROYTI_SENTINEL", r"ПРОЙТИ CHECK-IN\|ПОДТВЕРДИТЬ УЧАСТИЕ"),
    '''    await expect(playerPage.getByRole("heading", { name: "Ожидаем открытия" })).toBeVisible();''',
)
regex_replace(
    "checkin-operations.spec.ts",
    r'''    await expect\(playerCheckInButton\)\.toBeVisible\(\);\n    await playerCheckInButton\.click\(\);\n    await expect\(playerPage\.getByText\("Окно check-in сейчас закрыто", \{ exact: true \}\)\)\.toBeVisible\(\);\n''',
    "",
)

# The product copy is now fully Russian. The first compatibility pass rewrites legacy checks to
# the previous adaptive wording, so normalize those generated expectations here.
for file in ("checkin-operations.spec.ts", "registration-checkin.spec.ts"):
    path = ROOT / file
    text = path.read_text()
    old = "✓ Check-in пройден"
    actual = text.count(old)
    if actual:
        path.write_text(text.replace(old, "✓ Участие подтверждено"))
        print(f"BROWSER_RUNTIME_POSTPATCH=OK file={file} participation-copy replacements={actual}")

# The adaptive controls supply stable product audit reasons instead of browser-entered E2E text.
# Each legacy reason appears once in the dialog setup and once in the final audit assertion.
for old, new in (
    ('"E2E staff confirms check-in"', '"Check-in подтверждён организатором"'),
    ('"E2E staff revokes check-in"', '"Check-in отменён организатором"'),
    ('"E2E staff confirms after close"', '"Check-in подтверждён организатором"'),
):
    must_replace("checkin-operations.spec.ts", old, new, count=2)

# Copy changed in the restored organizer match controls.
must_replace(
    "match-readiness-lobby.spec.ts",
    'getByText("✓ Матч запущен вручную организатором", { exact: true })',
    'getByText("✓ Матч запущен организатором", { exact: true })',
)

# Organizer registration controls still exist, but their heading follows the adaptive wording.
must_replace(
    "registration-checkin.spec.ts",
    'getByRole("heading", { name: "Заявки и check-in" })',
    'getByRole("heading", { name: "Управление текущим этапом" })',
)

# Adaptive toast copy intentionally omits the decorative leading check mark on cancellation.
must_replace(
    "registration-corrections.spec.ts",
    'getByText("✓ Заявка отменена", { exact: true })',
    'getByText("Заявка отменена", { exact: true })',
)

# Inline result evidence uses a URL input; target it semantically rather than by placeholder copy.
for file in (
    "result-advancement.spec.ts",
    "result-correct-accept.spec.ts",
    "result-reject-resubmit.spec.ts",
    "result-reversal.spec.ts",
    "tournament-completion.spec.ts",
):
    path = ROOT / file
    text = path.read_text()
    old = '''locator('input[placeholder="https://..."]')'''
    if old in text:
        path.write_text(text.replace(old, '''locator('input[type="url"]')'''))
        print(f"BROWSER_RUNTIME_POSTPATCH=OK file={file} evidence-selector")

# The completed tournament intentionally remains the current read model so the adaptive home
# can render champion, final rosters and the final bracket without a dead transition state.
regex_replace(
    "tournament-completion.spec.ts",
    r'''    expect\(\(await current\.json\(\) as \{ tournament\?: unknown \}\)\.tournament\)\.toBeNull\(\);''',
    '''    expect((await current.json() as { tournament?: { id?: string; lifecycleStatus?: string; phase?: string } }).tournament).toMatchObject({
      id: state.tournamentId,
      lifecycleStatus: "COMPLETED",
      phase: "FINISHED",
    });''',
)

# OpenDota projection is the subject of this spec; the old standalone profile-menu logout shell
# was removed by the adaptive workspace and is covered separately by auth tests.
regex_replace(
    "opendota-projection.spec.ts",
    r'''    await playerPage\.goto\("/"\);\n    await playerPage\.getByRole\("button", \{ name: "Открыть профиль", exact: true \}\)\.click\(\);\n    await playerPage\.evaluate\(\(\) => \{.*?    await expect\(\n      playerPage\.locator\("\.standalone-profile-menu"\).*?    \)\.toBeVisible\(\);\n''',
    "",
)

# Rank names/classes changed with the Russian adaptive participant UI.
must_replace(
    "opendota-projection.spec.ts",
    'participantRow.locator(".rank-medal.rank-tier-8")',
    'participantRow.locator(".rank-emblem.rank-emblem-8")',
)
path = ROOT / "opendota-projection.spec.ts"
text = path.read_text()
rank_copy_count = text.count("Immortal #${state.leaderboardRank}")
if rank_copy_count:
    path.write_text(text.replace("Immortal #${state.leaderboardRank}", "Титан #${state.leaderboardRank}"))
    print(f"BROWSER_RUNTIME_POSTPATCH=OK file=opendota-projection.spec.ts rank-copy replacements={rank_copy_count}")

# The public teams view is now modal. Anchor assertions to the intended surface instead of matching
# duplicate text rendered by both the legacy route and the modal compatibility layer.
must_replace(
    "public-teams.spec.ts",
    'const mixedCard = page.locator("article").filter({ hasText: state.teamName });',
    'const mixedCard = page.getByRole("heading", { name: state.teamName, exact: true }).locator("xpath=ancestor::article[1]");',
)
must_replace(
    "public-teams.spec.ts",
    'await expect(page.getByText(state.reserveName, { exact: true })).toBeVisible();',
    'await expect(page.getByRole("main").getByText(state.reserveName, { exact: true })).toBeVisible();',
)

# The old organizer topbar was removed. Archive remains a dedicated operational fallback route,
# so browser lifecycle coverage navigates to it directly after exercising the adaptive drawer.
path = ROOT / "archive-trash-management.spec.ts"
text = path.read_text()
old_archive_nav = '''    await organizerPage.getByRole("link", { name: "Архив" }).click();\n'''
archive_nav_count = text.count(old_archive_nav)
if archive_nav_count:
    path.write_text(text.replace(old_archive_nav, '''    await organizerPage.goto("/organizer/archive");\n'''))
    print(f"BROWSER_RUNTIME_POSTPATCH=OK file=archive-trash-management.spec.ts archive-nav replacements={archive_nav_count}")

print("BROWSER_RUNTIME_POSTPATCH_SET=adaptive-workspace-v8-organizer-drawer-russian-ranks-modal-scope")
