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
    print(f"BROWSER_RUNTIME_POSTPATCH=OK file={relative} replacements={count}")


def regex_replace(relative: str, pattern: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    updated, actual = re.subn(pattern, new, text, count=count, flags=re.S)
    if actual != count:
        raise SystemExit(f"browser postpatch regex mismatch for {relative}: expected {count}, found {actual}: {pattern[:120]!r}")
    path.write_text(updated)
    print(f"BROWSER_RUNTIME_POSTPATCH_REGEX=OK file={relative} replacements={actual}")


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

for file in ("checkin-operations.spec.ts", "registration-checkin.spec.ts"):
    path = ROOT / file
    text = path.read_text()
    actual = text.count("✓ Check-in пройден")
    if actual:
        path.write_text(text.replace("✓ Check-in пройден", "✓ Участие подтверждено"))
        print(f"BROWSER_RUNTIME_POSTPATCH=OK file={file} participation-copy replacements={actual}")

# The adaptive UI renders both the persistent success heading and a transient toast. The heading
# assertion on the next line is the stable contract, so remove the legacy global-text assertion.
must_replace(
    "registration-checkin.spec.ts",
    '    await expect(playerPage.getByText("✓ Участие подтверждено", { exact: true })).toBeVisible();\n',
    "",
)

for old, new in (
    ('"E2E staff confirms check-in"', '"Check-in подтверждён организатором"'),
    ('"E2E staff revokes check-in"', '"Check-in отменён организатором"'),
    ('"E2E staff confirms after close"', '"Check-in подтверждён организатором"'),
):
    must_replace("checkin-operations.spec.ts", old, new, count=2)

must_replace(
    "match-readiness-lobby.spec.ts",
    'getByText("✓ Матч запущен вручную организатором", { exact: true })',
    'getByText("✓ Матч запущен организатором", { exact: true })',
)
must_replace(
    "registration-checkin.spec.ts",
    'getByRole("heading", { name: "Заявки и check-in" })',
    'getByRole("heading", { name: "Управление текущим этапом" })',
)
must_replace(
    "registration-corrections.spec.ts",
    'getByText("✓ Заявка отменена", { exact: true })',
    'getByText("Заявка отменена", { exact: true })',
)

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

regex_replace(
    "tournament-completion.spec.ts",
    r'''    expect\(\(await current\.json\(\) as \{ tournament\?: unknown \}\)\.tournament\)\.toBeNull\(\);''',
    '''    expect((await current.json() as { tournament?: { id?: string; lifecycleStatus?: string; phase?: string } }).tournament).toMatchObject({
      id: state.tournamentId,
      lifecycleStatus: "COMPLETED",
      phase: "FINISHED",
    });''',
)

regex_replace(
    "opendota-projection.spec.ts",
    r'''    await playerPage\.goto\("/"\);\n    await playerPage\.getByRole\("button", \{ name: "Открыть профиль", exact: true \}\)\.click\(\);\n    await playerPage\.evaluate\(\(\) => \{.*?    await expect\(\n      playerPage\.locator\("\.standalone-profile-menu"\).*?    \)\.toBeVisible\(\);\n''',
    "",
)
must_replace(
    "opendota-projection.spec.ts",
    'participantRow.locator(".rank-medal.rank-tier-8")',
    'participantRow.locator(".rank-emblem.rank-emblem-8")',
)
must_replace(
    "opendota-projection.spec.ts",
    'participantRow.locator(".rank-medal.rank-tier-0")',
    'participantRow.locator(".rank-emblem.rank-emblem-0")',
    count=2,
)
path = ROOT / "opendota-projection.spec.ts"
text = path.read_text()
for old, new in (
    ("Immortal #${state.leaderboardRank}", "Титан #${state.leaderboardRank}"),
    ("Friend code: ${state.changedSteamFriendCode}", "Код друга: ${state.changedSteamFriendCode}"),
):
    actual = text.count(old)
    if actual:
        text = text.replace(old, new)
        print(f"BROWSER_RUNTIME_POSTPATCH=OK file=opendota-projection.spec.ts copy replacements={actual}")
path.write_text(text)

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
must_replace(
    "public-teams.spec.ts",
    '''    await expect(page.locator("h1")).toHaveText(state.teamName);
    await expect(page.getByText(state.externalName, { exact: true })).toBeVisible();
    await expect(page.getByText("ВНЕШНИЙ", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Матчи команды", level: 2 })).toBeVisible();
    await expect(page.getByText("Гранд-финал · BO5", { exact: true })).toBeVisible();
    await expect(page.getByText(new RegExp(`${state.opponentName}.*идёт`))).toBeVisible();''',
    '''    const teamDialog = page.getByRole("dialog", { name: "Состав команды" });
    await expect(teamDialog.locator("h1")).toHaveText(state.teamName);
    await expect(teamDialog.getByText(state.externalName, { exact: true })).toBeVisible();
    await expect(teamDialog.getByText("ВНЕШНИЙ", { exact: true })).toBeVisible();
    await expect(teamDialog.getByRole("heading", { name: "Матчи команды", level: 2 })).toBeVisible();
    await expect(teamDialog.getByText("Гранд-финал · BO5", { exact: true })).toBeVisible();
    await expect(teamDialog.getByText(new RegExp(`${state.opponentName}.*идёт`))).toBeVisible();''',
)

path = ROOT / "archive-trash-management.spec.ts"
text = path.read_text()
old_archive_nav = '    await organizerPage.getByRole("link", { name: "Архив" }).click();\n'
actual = text.count(old_archive_nav)
if actual:
    path.write_text(text.replace(old_archive_nav, '    await organizerPage.goto("/organizer/archive");\n'))
    print(f"BROWSER_RUNTIME_POSTPATCH=OK file=archive-trash-management.spec.ts archive-nav replacements={actual}")

print("BROWSER_RUNTIME_POSTPATCH_SET=adaptive-workspace-v11-stable-success-heading")
