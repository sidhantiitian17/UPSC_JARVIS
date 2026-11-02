"""WU-P02-012: Obsidian mirror (specs/vault.feature)."""

import json
import shutil
from datetime import UTC, datetime

import pytest

from jarvis.vault.writer import VaultError, VaultWriter, safe_filename, write_atomic
from tests.test_gate import FakeLLM, H, finished_session, make
from tests.test_gate_scoring import answer


def test_safe_filename_strips_windows_forbidden_characters():
    name = safe_filename('Laxmikanth: Polity / "Part 1"? <v7>|*\\')
    assert not set('<>:"/\\|?*') & set(name) and name and len(name) <= 80
    assert safe_filename("CON") != "CON" and safe_filename("") == "untitled"
    assert not safe_filename("name.").endswith(".")


def test_write_atomic_uses_lf_and_leaves_no_temp_files(tmp_path):
    target = tmp_path / "a" / "note.md"
    write_atomic(target, "line1\r\nline2\n")
    assert target.read_bytes() == b"line1\nline2\n"
    write_atomic(target, "replaced")
    assert target.read_text(encoding="utf-8") == "replaced"
    assert [p.name for p in target.parent.iterdir()] == ["note.md"]


def test_writer_refuses_text_containing_a_stored_secret(tmp_path):
    w = VaultWriter(tmp_path, secrets=lambda: ["AIzaSECRETVALUE1234567890"])
    with pytest.raises(VaultError):
        w.write("JARVIS/Cards/q-1.md", "stem mentions AIzaSECRETVALUE1234567890 here")
    assert not (tmp_path / "JARVIS").exists()
    w.write("JARVIS/Cards/q-2.md", "harmless")
    assert (tmp_path / "JARVIS/Cards/q-2.md").read_text() == "harmless"


def test_writer_refuses_paths_outside_the_vault(tmp_path):
    w = VaultWriter(tmp_path, secrets=lambda: [])
    with pytest.raises(VaultError):
        w.write("../outside.md", "x")


def vault_setup(tmp_path, llm=None):
    vault = tmp_path / "vault"
    vault.mkdir()
    client = make(tmp_path, llm or FakeLLM())
    assert client.put("/settings", headers=H, json={"vault_path": str(vault)}).status_code == 200
    return client, vault


def play(client, tmp_path, right):
    sid, _ = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    for i, qq in enumerate(g["questions"]):
        answer(client, sid, qq["id"], i < right)
    return sid, g, client.post(f"/sessions/{sid}/gate/finish", headers=H).json()


def files(vault, sub):
    d = vault / "JARVIS" / sub
    return sorted(d.glob("*.md")) if d.exists() else []


def test_nothing_is_written_without_a_vault(tmp_path):
    client = make(tmp_path, FakeLLM())
    play(client, tmp_path, 10)
    assert not (tmp_path / "vault").exists()
    assert not list(tmp_path.glob("**/JARVIS"))


def test_passed_gate_writes_session_and_daily_notes(tmp_path):
    client, vault = vault_setup(tmp_path)
    sid, g, result = play(client, tmp_path, 10)
    assert result["passed"] is True
    notes = files(vault, "Sessions")
    assert len(notes) == 1
    text = notes[0].read_text(encoding="utf-8")
    assert text.startswith("---\n") and "type: session" in text and "book: polity" in text
    assert f"session_id: {sid}" in text and "passed: true" in text and "retention: 100" in text
    assert "[[" in text and "Constitution and Polity" in text
    assert "\r" not in text
    daily = files(vault, "Daily")
    assert len(daily) == 1
    dtext = daily[0].read_text(encoding="utf-8")
    assert f"[[Sessions/{notes[0].stem}]]" in dtext and "verified" in dtext.lower()


def test_failed_gate_note_lists_restudy_quotes_and_cards_are_written(tmp_path):
    client, vault = vault_setup(tmp_path)
    sid, g, result = play(client, tmp_path, 3)
    assert result["passed"] is False
    text = files(vault, "Sessions")[0].read_text(encoding="utf-8")
    assert "## Restudy" in text and "page" in text
    wrong = len(g["questions"]) - 3
    cards = files(vault, "Cards")
    assert len(cards) == wrong
    ctext = cards[0].read_text(encoding="utf-8")
    for needle in ("type: card", "## Question", "## Answer", "## Source", "[["):
        assert needle in ctext


def test_skipped_gate_writes_a_session_note(tmp_path):
    client, vault = vault_setup(tmp_path)
    sid, _ = finished_session(client, tmp_path)
    client.post(f"/sessions/{sid}/gate", headers=H)
    client.post(f"/sessions/{sid}/gate/skip", headers=H, json={"penalty": True})
    text = files(vault, "Sessions")[0].read_text(encoding="utf-8")
    assert "skipped: true" in text


def test_rewriting_the_daily_note_is_idempotent(tmp_path):
    client, vault = vault_setup(tmp_path)
    play(client, tmp_path, 10)
    daily = files(vault, "Daily")[0]
    first = daily.read_text(encoding="utf-8")
    from jarvis.vault.mirror import mirror_daily

    state = client.app.state.jarvis
    mirror_daily(state.conn, VaultWriter(vault, secrets=lambda: []), datetime.now(UTC))
    assert daily.read_text(encoding="utf-8") == first


def test_no_vault_file_contains_a_stored_api_key(tmp_path):
    client, vault = vault_setup(tmp_path)
    secret = "AIzaSyD-FAKEKEY-1234567890abcdef"
    client.put("/secrets/gemini_key", headers=H, json={"value": secret})
    play(client, tmp_path, 4)
    for p in (vault / "JARVIS").rglob("*.md"):
        assert secret not in p.read_text(encoding="utf-8")


def test_a_question_containing_a_secret_is_not_mirrored_but_the_gate_still_completes(tmp_path):
    client, vault = vault_setup(tmp_path)
    secret = "AIzaSyD-FAKEKEY-1234567890abcdef"
    client.put("/secrets/gemini_key", headers=H, json={"value": secret})
    sid, _ = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    state = client.app.state.jarvis
    state.conn.execute(
        "update question set stem = stem || ? where id = ?", (f" {secret}", g["questions"][0]["id"])
    )
    for qq in g["questions"]:
        answer(client, sid, qq["id"], False)
    r = client.post(f"/sessions/{sid}/gate/finish", headers=H)
    assert r.status_code == 200
    for p in (vault / "JARVIS").rglob("*.md"):
        assert secret not in p.read_text(encoding="utf-8")


def test_a_deleted_vault_never_breaks_the_gate(tmp_path):
    client, vault = vault_setup(tmp_path)
    shutil.rmtree(vault)
    sid, g, result = play(client, tmp_path, 10)
    assert result["passed"] is True


def test_json_helpers_exist():
    assert json and safe_filename
