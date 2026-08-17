#!/usr/bin/env python3
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


# Copy-only changes in the adaptive UI.
replace("archive-mixed-roster.spec.ts", "5 игроков в финальном составе · 1 внеш.", "5 игроков в финальном составе · 1 замен")
for file in ("captain-transfer.spec.ts", "replacement-reject-external-outgoing.spec.ts", "replacements.spec.ts"):
    replace(
        file,
        'getByText("✓ Заявка отправлена организатору. До ACCEPT состав не изменится.", { exact: true })',
        'getByText(/✓ Заявка на (?:замену|обмен игроками) отправлена организатору/i)',
    )
replace("checkin-operations.spec.ts", 'getByRole("button", { name: "ПОДТВЕРДИТЬ УЧАСТИЕ" })', 'getByRole("button", { name: /ПРОЙТИ CHECK-IN|ПОДТВЕРДИТЬ УЧАСТИЕ/ })')
replace("match-readiness-lobby.spec.ts", 'getByRole("heading", { name: "Готовность, старт и таймеры" })', 'getByRole("heading", { name: "Готовность и старт матчей" })')
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
    "result-advancement.spec.ts": [("Browser E2E: результат и подтверждение проверены", "Результат подтверждён организатором")],
    "result-reject-resubmit.spec.ts": [("Browser E2E: подтверждение счёта недостаточно", "Результат отклонён организатором")],
    "tournament-completion.spec.ts": [("Browser E2E: Grand Final подтверждён", "Результат подтверждён организатором")],
}
for file, pairs in reason_updates.items():
    for old, new in pairs:
        replace(file, old, new)

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

print("BROWSER_RUNTIME_PATCH_SET=adaptive-workspace-v1")
