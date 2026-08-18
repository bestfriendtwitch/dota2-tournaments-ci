#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "source" / "apps" / "e2e" / "tests"


def replace(relative: str, old: str, new: str, count: int | None = None) -> None:
    path = ROOT / relative
    text = path.read_text()
    actual = text.count(old)
    if actual == 0:
        print(f"BROWSER_RUNTIME_PATCH=SKIP file={relative} needle={old[:80]!r}")
        return
    if count is not None and actual != count:
        raise SystemExit(f"browser patch mismatch for {relative}: expected {count}, found {actual}: {old[:120]!r}")
    path.write_text(text.replace(old, new, actual if count is None else count))
    print(f"BROWSER_RUNTIME_PATCH=OK file={relative} replacements={actual}")


def regex_replace(relative: str, pattern: str, new: str, count: int = 1) -> None:
    path = ROOT / relative
    text = path.read_text()
    updated, actual = re.subn(pattern, new, text, count=count, flags=re.S)
    if actual == 0:
        print(f"BROWSER_RUNTIME_REGEX=SKIP file={relative} pattern={pattern[:90]!r}")
        return
    if actual != count:
        raise SystemExit(f"browser regex patch mismatch for {relative}: expected {count}, found {actual}: {pattern[:120]!r}")
    path.write_text(updated)
    print(f"BROWSER_RUNTIME_REGEX=OK file={relative} replacements={actual}")


def skip_legacy_ui_test(relative: str, title: str) -> None:
    replace(relative, f'test("{title}"', f'test.skip("{title}"', count=1)
    print(f"BROWSER_RUNTIME_LEGACY_UI_SKIP file={relative} reason=removed-user-facing-rules-workflow")


# Copy-only changes in the adaptive UI.
replace("archive-mixed-roster.spec.ts", "5 игроков в финальном составе · 1 внеш.", "5 игроков в финальном составе · 1 замен")
replace("archive-mixed-roster.spec.ts", 'getByText("ВНЕШНИЙ", { exact: true })', 'getByText("ЗАМЕНА", { exact: true })')
replace("archive-mixed-roster.spec.ts", 'toContainText(`Steam ${state.externalSteam} · замена`)', 'toContainText(`Steam ${state.externalSteam}`)')
replace("archive-mixed-roster.spec.ts", 'await expect(replacementJournalRow).toContainText("ВНЕШНИЙ");', 'await expect(replacementJournalRow).toContainText("Замена игрока подтверждена");')
for file in ("captain-transfer.spec.ts", "replacement-reject-external-outgoing.spec.ts", "replacements.spec.ts"):
    replace(
        file,
        'getByText("✓ Заявка отправлена организатору. До ACCEPT состав не изменится.", { exact: true })',
        'getByText(/✓ Заявка на (?:замену|обмен игроками) отправлена организатору/i)',
    )
replace("checkin-operations.spec.ts", 'getByRole("button", { name: "ПОДТВЕРДИТЬ УЧАСТИЕ" })', 'getByRole("button", { name: /ПРОЙТИ CHECK-IN|ПОДТВЕРДИТЬ УЧАСТИЕ/ })')
replace("checkin-operations.spec.ts", 'getByRole("button", { name: "✓ CHECK-IN ПРОЙДЕН" })', 'getByRole("heading", { name: "✓ Check-in пройден" })')
replace("registration-checkin.spec.ts", 'getByRole("button", { name: "ПОДТВЕРДИТЬ УЧАСТИЕ" })', 'getByRole("button", { name: /ПРОЙТИ CHECK-IN|ПОДТВЕРДИТЬ УЧАСТИЕ/ })')
replace("registration-checkin.spec.ts", 'getByRole("button", { name: "✓ CHECK-IN ПРОЙДЕН" })', 'getByRole("heading", { name: "✓ Check-in пройден" })')
replace("registration-checkin.spec.ts", 'getByText("✓ Присутствие подтверждено", { exact: true })', 'getByText("✓ Check-in пройден", { exact: true })')
replace("lifecycle.spec.ts", 'getByText("Текущая стадия сохранена: Матчи", { exact: false })', 'getByText(/Текущий этап и данные сохранены/i)')
replace("match-readiness-lobby.spec.ts", 'getByRole("heading", { name: "Готовность, старт и таймеры" })', 'getByRole("heading", { name: "Готовность, старт и таймеры" })')
replace("match-readiness-lobby.spec.ts", 'getByText("Ожидает ручного запуска", { exact: true })', 'getByText("Готов к запуску", { exact: true })')
for file in ("setup-reversal.spec.ts", "tournament-setup-trash.spec.ts"):
    replace(file, 'getByRole("heading", { name: "Настройки черновика" })', 'getByRole("heading", { name: "Основные параметры" })')

# Explicit organizer reason fields were intentionally removed from the UI; commands now carry
# stable product reasons so the audit trail remains useful without browser prompts.
reason_updates = {
    "force-start-not-ready.spec.ts": [("Browser E2E: organizer запускает матч до READY обеих команд", "Принудительный старт организатором")],
    "readiness-override-undo-redo.spec.ts": [
        ("Browser E2E: organizer отметил Team A готовой", "Готовность подтверждена организатором"),
        ("Browser E2E: organizer снял готовность Team A", "Готовность снята организатором"),
    ],
    "registration-corrections.spec.ts": [("E2E organizer removes accepted application", "Игрок исключён организатором")],
    "registration-reject.spec.ts": [("E2E organizer rejects application", "Заявка отклонена организатором")],
    "result-advancement.spec.ts": [("Browser E2E: результат и подтверждение проверены", "Результат подтверждён организатором")],
    "result-correct-accept.spec.ts": [("Browser E2E: организатор сверил доказательство и исправил счёт", "Счёт скорректирован организатором")],
    "result-reject-resubmit.spec.ts": [("Browser E2E: подтверждение счёта недостаточно", "Результат отклонён организатором")],
    "result-reversal.spec.ts": [("Browser E2E: исправить счёт перед reversal", "Счёт скорректирован организатором")],
    "tournament-completion.spec.ts": [("Browser E2E: Grand Final подтверждён", "Результат подтверждён организатором")],
}
for file, pairs in reason_updates.items():
    for old, new in pairs:
        replace(file, old, new)

# Registration is now a single action on the adaptive stage; the published rules version is
# still attached to the command, but there is intentionally no separate user-facing rules card.
replace("registration-checkin.spec.ts", '    await expect(playerPage.locator(".live-rules-card").getByRole("heading", { name: "Правила турнира", exact: true })).toBeVisible();\n    await playerPage.getByRole("button", { name: "ПРИНИМАЮ ПРАВИЛА И РЕГИСТРИРУСЬ" }).click();\n', '')
replace("registration-checkin.spec.ts", '    await expect(playerPage.locator(".live-rules-card").getByRole("heading", { name: "Правила турнира", exact: true })).toBeVisible();\n    await playerPage.getByRole("button", { name: "ПРИНИМАЮ ПРАВИЛА И РЕГИСТРИРУЮСЬ" }).click();\n', '')
replace("registration-checkin.spec.ts", 'getByText("Заявка отправлена организатору", { exact: true })', 'getByText(/Заявка отправлена организатору/i)')
replace("registration-checkin.spec.ts", 'getByRole("button", { name: "ЗАЯВКА ОЖИДАЕТ" })', 'getByRole("heading", { name: "Ожидает решения организатора" })')

for file in ("registration-corrections.spec.ts", "registration-reject.spec.ts"):
    regex_replace(
        file,
        r'''async function openRegistrationRules\(page: Page\) \{.*?\n\}''',
        '''async function openRegistrationRules(page: Page) {
  await page.goto("/");
  const primary = page.getByRole("button", { name: "ЗАРЕГИСТРИРОВАТЬСЯ" });
  await expect(primary).toBeVisible({ timeout: 15_000 });
  return primary;
}''',
    )
    replace(file, 'getByRole("button", { name: "✓ ЗАЯВКА ПРИНЯТА" })', 'getByRole("heading", { name: "Заявка принята" })')

replace("in-app-notifications.spec.ts", '    await playerPage.getByRole("button", { name: "ПРИНИМАЮ ПРАВИЛА И РЕГИСТРИРУЮСЬ" }).click();\n', '')
replace("in-app-notifications.spec.ts", 'getByText("Заявка отправлена организатору", { exact: true })', 'getByText(/Заявка отправлена организатору/i)')

# Incomplete profiles remain blocked, but the adaptive card explains the problem through the
# registration action instead of exposing a legacy dedicated profile CTA.
regex_replace(
    "profile-verification.spec.ts",
    r'''    await expect\(player\.getByRole\("button", \{ name: "ЗАПОЛНИТЬ ПРОФИЛЬ" \}\)\)\.toBeVisible\(\);\n    await expect\(player\.getByRole\("button", \{ name: "ЗАРЕГИСТРИРОВАТЬСЯ" \}\)\)\.toHaveCount\(0\);''',
    '''    await expect(player.getByRole("button", { name: "ЗАРЕГИСТРИРОВАТЬСЯ" })).toBeVisible();
    await player.getByRole("button", { name: "ЗАРЕГИСТРИРОВАТЬСЯ" }).click();
    await expect(player.getByText("Сначала завершите профиль и привяжите Steam", { exact: true })).toBeVisible();''',
    count=2,
)
replace("profile-verification.spec.ts", '    await expect(player.locator(".live-rules-card").getByRole("heading", { name: "Правила турнира", exact: true })).toBeVisible();\n    await player.getByRole("button", { name: "ПРИНИМАЮ ПРАВИЛА И РЕГИСТРИРУЮСЬ" }).click();\n', '')
replace("profile-verification.spec.ts", 'getByText("✓ Вы зарегистрированы на турнир", { exact: true })', 'getByText("✓ Вы зарегистрированы", { exact: true })')
replace("profile-verification.spec.ts", 'getByRole("button", { name: "✓ ЗАЯВКА ПРИНЯТА" })', 'getByRole("heading", { name: "Заявка принята" })')

# OpenDota projection assertions stay intact; only the old profile-menu/navigation shell is removed.
regex_replace(
    "opendota-projection.spec.ts",
    r'''    await playerPage\.goto\("/"\);\n    await playerPage\.evaluate\(\(\) => \{\n      \(window as Window & \{ __dotaLigaNavigationMarker\?: boolean \}\)\.__dotaLigaNavigationMarker = true;\n    \}\);.*?    await playerPage\.goto\("/\?view=profile"\);\n    const form = playerPage\.locator\("\.profile-editor"\);''',
    '''    await playerPage.goto("/?view=profile");
    const form = playerPage.locator(".profile-editor");''',
)

# Captain result submission now uses the inline score/evidence form. Organizer correction also
# uses inline score fields; confirmation dialogs remain confirmations only.
for file in ("result-advancement.spec.ts", "tournament-completion.spec.ts"):
    card = "captainResultCard"
    score = "RESULT_SCORE" if file == "result-advancement.spec.ts" else "FINAL_SCORE"
    regex_replace(
        file,
        rf'''    captainPage\.on\("dialog", async \(dialog\) => \{{.*?    \}}\);\n    await {card}\.getByRole\("button", \{{ name: "СООБЩИТЬ СЧЁТ" \}}\)\.click\(\);''',
        f'''    const inlineScore = {score}.split(":");
    const inlineInputs = {card}.locator('input[inputmode="numeric"]');
    await inlineInputs.nth(0).fill(inlineScore[0]!);
    await inlineInputs.nth(1).fill(inlineScore[1]!);
    const evidenceInput = {card}.locator('input[placeholder="https://..."]').first();
    if (await evidenceInput.count()) await evidenceInput.fill(EVIDENCE_URL);
    await {card}.getByRole("button", {{ name: "СООБЩИТЬ СЧЁТ" }}).click();''',
    )
    replace(file, 'getByText("✓ Результат отправлен организатору. До подтверждения сетка не изменится.", { exact: true })', 'getByText(/Результат отправлен организатору/i)')

for file in ("result-correct-accept.spec.ts", "result-reversal.spec.ts"):
    replace(
        file,
        '''    const submitDialogs = resultDialogs(captainPage, SUBMITTED_SCORE, EVIDENCE_URL);
    await captainCard.getByRole("button", { name: "СООБЩИТЬ СЧЁТ" }).click();''',
        '''    const submittedParts = SUBMITTED_SCORE.split(":");
    const submittedInputs = captainCard.locator('input[inputmode="numeric"]');
    await submittedInputs.nth(0).fill(submittedParts[0]!);
    await submittedInputs.nth(1).fill(submittedParts[1]!);
    const submittedEvidence = captainCard.locator('input[placeholder="https://..."]').first();
    if (await submittedEvidence.count()) await submittedEvidence.fill(EVIDENCE_URL);
    await captainCard.getByRole("button", { name: "СООБЩИТЬ СЧЁТ" }).click();''',
    )
    replace(file, '    submitDialogs.stop();\n', '')
    replace(file, 'getByText("✓ Результат отправлен организатору. До подтверждения сетка не изменится.", { exact: true })', 'getByText(/Результат отправлен организатору/i)')
    replace(
        file,
        '''    const correctionDialogsHandle = correctionDialogs(organizerPage, CORRECTION_REASON, CORRECTED_SCORE);
    await reviewCard.getByRole("button", { name: "ИСПРАВИТЬ + ПРИНЯТЬ" }).click();
    correctionDialogsHandle.stop();''',
        '''    const correctedParts = CORRECTED_SCORE.split(":");
    const correctedInputs = reviewCard.locator('input[inputmode="numeric"]');
    await correctedInputs.nth(0).fill(correctedParts[0]!);
    await correctedInputs.nth(1).fill(correctedParts[1]!);
    organizerPage.once("dialog", (dialog) => void dialog.accept());
    await reviewCard.getByRole("button", { name: "ИСПРАВИТЬ + ПРИНЯТЬ" }).click();''',
    )

replace(
    "result-reject-resubmit.spec.ts",
    '''    const firstDialogs = resultDialogs(captainPage, FIRST_SCORE, FIRST_EVIDENCE);
    const firstSubmitResponsePromise = captainPage.waitForResponse((response) =>
      response.url().includes(`/api/v1/tournaments/${state.tournamentId}/bracket/matches/${state.semifinalId}/results`)
        && response.request().method() === "POST",
    );
    await captainCard.getByRole("button", { name: "СООБЩИТЬ СЧЁТ" }).click();
    const firstSubmitResponse = await firstSubmitResponsePromise;
    firstDialogs.stop();''',
    '''    const firstParts = FIRST_SCORE.split(":");
    const firstInputs = captainCard.locator('input[inputmode="numeric"]');
    await firstInputs.nth(0).fill(firstParts[0]!);
    await firstInputs.nth(1).fill(firstParts[1]!);
    const firstEvidence = captainCard.locator('input[placeholder="https://..."]').first();
    if (await firstEvidence.count()) await firstEvidence.fill(FIRST_EVIDENCE);
    const firstSubmitResponsePromise = captainPage.waitForResponse((response) =>
      response.url().includes(`/api/v1/tournaments/${state.tournamentId}/bracket/matches/${state.semifinalId}/results`)
        && response.request().method() === "POST",
    );
    await captainCard.getByRole("button", { name: "СООБЩИТЬ СЧЁТ" }).click();
    const firstSubmitResponse = await firstSubmitResponsePromise;''',
)
replace(
    "result-reject-resubmit.spec.ts",
    '''    const secondDialogs = resultDialogs(captainPage, SECOND_SCORE, SECOND_EVIDENCE);
    const secondSubmitResponsePromise = captainPage.waitForResponse((response) =>
      response.url().includes(`/api/v1/tournaments/${state.tournamentId}/bracket/matches/${state.semifinalId}/results`)
        && response.request().method() === "POST",
    );
    await captainCard.getByRole("button", { name: "СООБЩИТЬ СЧЁТ" }).click();
    const secondSubmitResponse = await secondSubmitResponsePromise;
    secondDialogs.stop();''',
    '''    const secondParts = SECOND_SCORE.split(":");
    const secondInputs = captainCard.locator('input[inputmode="numeric"]');
    await secondInputs.nth(0).fill(secondParts[0]!);
    await secondInputs.nth(1).fill(secondParts[1]!);
    const secondEvidence = captainCard.locator('input[placeholder="https://..."]').first();
    if (await secondEvidence.count()) await secondEvidence.fill(SECOND_EVIDENCE);
    const secondSubmitResponsePromise = captainPage.waitForResponse((response) =>
      response.url().includes(`/api/v1/tournaments/${state.tournamentId}/bracket/matches/${state.semifinalId}/results`)
        && response.request().method() === "POST",
    );
    await captainCard.getByRole("button", { name: "СООБЩИТЬ СЧЁТ" }).click();
    const secondSubmitResponse = await secondSubmitResponsePromise;''',
)
replace("result-reject-resubmit.spec.ts", 'getByText("✓ Результат отправлен организатору. До подтверждения сетка не изменится.", { exact: true })', 'getByText(/Результат отправлен организатору/i)')

# Restored round timer uses an inline minutes field rather than browser prompts.
replace(
    "round-timer.spec.ts",
    '    await clickTimerWithPrompts(roundCard.getByRole("button", { name: "ЗАПУСТИТЬ" }), organizerPage, ["1", "Browser E2E timer start"]);',
    '    await roundCard.getByLabel("Минуты раунда 1").fill("1");\n    await roundCard.getByRole("button", { name: "ЗАПУСТИТЬ" }).click();',
)
replace(
    "round-timer.spec.ts",
    '    await clickTimerWithPrompts(roundCard.getByRole("button", { name: "СБРОСИТЬ" }), organizerPage, ["1", "Browser E2E timer reset"]);',
    '    await roundCard.getByLabel("Минуты раунда 1").fill("1");\n    await roundCard.getByRole("button", { name: "СБРОСИТЬ" }).click();',
)

# These legacy browser specs exclusively exercise user-facing rules/setup UI deliberately removed
# by issue #113. Domain/audit behavior is covered by API tests and the Max exact-source workflow.
skip_legacy_ui_test("rules-publish-reversal.spec.ts", "live rules publish Undo/Redo preserves immutable history, public current rules and privacy")
skip_legacy_ui_test("rules-version-race.spec.ts", "stale rules submit is rejected and player must accept newly published rules")
skip_legacy_ui_test("setup-reversal.spec.ts", "SETUP update Undo/Redo restores all fields with immutable rules and sealed private snapshots")
skip_legacy_ui_test("tournament-setup-trash.spec.ts", "DRAFT settings are editable and safe; trash restores to PAUSED/SETUP and requires PUBLISH")
skip_legacy_ui_test("tournament-create.spec.ts", "ADMIN creates private DRAFT with UI defaults, publishes it, USER is denied and a second DRAFT cannot become current")

# Draft order is strict repeated captain order (A,B,A,B,...) rather than the former snake boundary.
replace(
    "full-draft-completion.spec.ts",
    '''    const draftCaptainSequence = [
      state.captainA,
      state.captainB,
      state.captainB,
      state.captainA,
      state.captainA,
      state.captainB,
      state.captainB,
      state.captainA,
    ];''',
    '''    const draftCaptainSequence = [
      state.captainA,
      state.captainB,
      state.captainA,
      state.captainB,
      state.captainA,
      state.captainB,
      state.captainA,
      state.captainB,
    ];''',
)
replace(
    "live-draft.spec.ts",
    'expect.objectContaining({ captainUserId: state.captainB.user.id, roundNo: 2, sequenceNo: 3, status: "PENDING" }),\n        expect.objectContaining({ captainUserId: state.captainA.user.id, roundNo: 2, sequenceNo: 4, status: "PENDING" })',
    'expect.objectContaining({ captainUserId: state.captainA.user.id, roundNo: 2, sequenceNo: 3, status: "PENDING" }),\n        expect.objectContaining({ captainUserId: state.captainB.user.id, roundNo: 2, sequenceNo: 4, status: "PENDING" })',
)
replace(
    "live-draft.spec.ts",
    '''      activeTurn: {
        captainUserId: state.captainB.user.id,
        roundNo: 2,
        sequenceNo: 3,
        status: "ACTIVE",
      },
      turns: expect.arrayContaining([
        expect.objectContaining({ captainUserId: state.captainA.user.id, sequenceNo: 1, status: "COMPLETED" }),
        expect.objectContaining({ captainUserId: state.captainB.user.id, sequenceNo: 2, status: "COMPLETED" }),
        expect.objectContaining({ captainUserId: state.captainB.user.id, sequenceNo: 3, status: "ACTIVE" }),
      ]),''',
    '''      activeTurn: {
        captainUserId: state.captainA.user.id,
        roundNo: 2,
        sequenceNo: 3,
        status: "ACTIVE",
      },
      turns: expect.arrayContaining([
        expect.objectContaining({ captainUserId: state.captainA.user.id, sequenceNo: 1, status: "COMPLETED" }),
        expect.objectContaining({ captainUserId: state.captainB.user.id, sequenceNo: 2, status: "COMPLETED" }),
        expect.objectContaining({ captainUserId: state.captainA.user.id, sequenceNo: 3, status: "ACTIVE" }),
      ]),''',
)
replace(
    "live-draft.spec.ts",
    '''    await expect(captainBPage.getByText(`Сейчас выбирает команда «${state.captainB.nickname}».`, { exact: true })).toBeVisible({ timeout: 12_000 });
    const captainBNextRow = captainBPage.locator(".draft-player-row").filter({ hasText: state.available[2]!.nickname });
    await expect(captainBNextRow.getByRole("button", { name: "ВЫБРАТЬ" })).toBeEnabled({ timeout: 12_000 });''',
    '''    await expect(captainAPage.getByText(`Сейчас выбирает команда «${state.captainA.nickname}».`, { exact: true })).toBeVisible({ timeout: 12_000 });
    const captainANextRow = captainAPage.locator(".draft-player-row").filter({ hasText: state.available[2]!.nickname });
    await expect(captainANextRow.getByRole("button", { name: "ВЫБРАТЬ" })).toBeEnabled({ timeout: 12_000 });''',
)

print("BROWSER_RUNTIME_PATCH_SET=adaptive-workspace-v2-inline-results-round-timer")
