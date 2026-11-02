"""WU-P02-008: recall-gate generation + validation (specs/gate.feature). Offline: scripted LLM."""

import json

import pytest
from fastapi.testclient import TestClient

from jarvis.app import create_app
from jarvis.brain.context_pack import build_context_pack
from jarvis.gate.generate import target_count
from jarvis.gate.questions import validate_batch
from jarvis.llm.types import ProviderError, ProviderResult
from tests.pdfgen import make_pdf

TOKEN = "t" * 32
H = {"Authorization": f"Bearer {TOKEN}"}

SENTENCES = [
    "The Parliament of India consists of the President, the Lok Sabha and the Rajya Sabha.",
    "Article 14 guarantees equality before the law to every person in India.",
    "The Rajya Sabha is a permanent house and one third of its members retire every second year.",
    "The Lok Sabha has a maximum strength of 552 members under the Constitution.",
    "The Speaker of the Lok Sabha presides over the joint sitting of both Houses of Parliament.",
    "Article 21 protects the right to life and personal liberty of every citizen.",
    "The Finance Commission is constituted by the President every fifth year under Article 280.",
    "The Comptroller and Auditor General audits the accounts of the Union and the States.",
    "Money Bills can be introduced only in the Lok Sabha on the recommendation of the President.",
    "The Election Commission of India supervises elections to Parliament and State Legislatures.",
    "The Vice President of India acts as the ex officio Chairman of the Rajya Sabha.",
    "Article 32 empowers the Supreme Court to issue writs for the enforcement of Fundamental Rights.",
    "The Attorney General of India is the highest law officer appointed by the President.",
    "The Union Public Service Commission conducts the Civil Services Examination every year.",
    "Directive Principles of State Policy are non justiciable but fundamental to governance.",
    "The Tenth Schedule contains provisions on disqualification on grounds of defection.",
    "The Governor of a State is appointed by the President for a term of five years.",
    "Panchayati Raj institutions received constitutional status through the 73rd Amendment.",
    "Article 356 allows the imposition of President's Rule when constitutional machinery fails.",
    "The Planning Commission was replaced by the NITI Aayog in the year 2015.",
    "Zonal Councils were set up under the States Reorganisation Act of 1956.",
    "The Inter State Council is established under Article 263 of the Constitution.",
    "The National Human Rights Commission was established under a statute passed in 1993.",
    "The Right to Education became a Fundamental Right through the 86th Amendment.",
    "The Goods and Services Tax Council is chaired by the Union Finance Minister.",
    "The Seventh Schedule divides legislative subjects into Union, State and Concurrent Lists.",
]
PAGES = ["\n".join(SENTENCES[:13]), "\n".join(SENTENCES[13:])]


class FakeLLM:
    """Builds valid questions out of the passage lines it is shown; can inject bad ones or fail."""

    name, kind = "ollama", "local"

    def __init__(self, bad=0, error=None, per_call=None):
        self.bad, self.error, self.per_call, self.calls = bad, error, per_call, []

    def complete(self, messages, *, model, json_schema=None, timeout=60.0):
        self.calls.append(messages)
        if self.error:
            raise self.error
        user = messages[-1].content
        if "Write exactly " not in user:  # the tag_chunk call made when the session ends
            return ProviderResult(json.dumps({"node_ids": ["gs2.polity"]}), 1, 1, model)
        want = int(user.split("Write exactly ")[1].split(" ")[0])
        lines = [
            ln
            for ln in user.split("Passage:\n")[1].splitlines()
            if len(ln) > 40 and not ln.startswith("[chunk")
        ]
        qs = []
        for i, line in enumerate(lines[: self.per_call or want]):
            qs.append(
                {
                    "stem": f"Which statement is supported by the text (item {len(self.calls)}-{i})?",
                    "options": [
                        line[:60],
                        "an unrelated claim A",
                        "an unrelated claim B",
                        "an unrelated claim C",
                    ],
                    "answer_index": 0,
                    "source_quote": line,
                    "explanation": "Stated in the passage.",
                }
            )
        for j in range(self.bad):
            qs.append(
                {
                    **qs[0],
                    "stem": f"Fabricated question {j}?",
                    "source_quote": f"A made up sentence number {j} that is absent.",
                }
            )
        return ProviderResult(json.dumps({"questions": qs}), 10, 10, model)


def make(tmp_path, llm):
    app = create_app(TOKEN, data_dir=tmp_path / "d", provider_builder=lambda r, s: {"ollama": llm})
    return TestClient(app)


def finished_session(client, tmp_path, name="polity", pages=PAGES):
    p = tmp_path / f"{name}.pdf"
    p.write_bytes(make_pdf(pages))
    doc = client.post("/library/documents", headers=H, json={"path": str(p)}).json()["id"]
    first = client.get(f"/library/documents/{doc}/pages/1/chunks", headers=H).json()[0]["id"]
    last_page = len(pages)
    last = client.get(f"/library/documents/{doc}/pages/{last_page}/chunks", headers=H).json()[-1]["id"]
    sid = client.post("/sessions", headers=H, json={"document_id": doc, "start_chunk_id": first}).json()["id"]
    r = client.post(f"/sessions/{sid}/end", headers=H, json={"end_chunk_id": last, "focused_seconds": 3000})
    assert r.json()["status"] == "gate"
    return sid, doc


# ---------- pure units ----------
@pytest.mark.parametrize(
    "chunks,mult,expected",
    [(1, 1, 10), (4, 1, 10), (20, 1, 16), (60, 1, 30), (200, 1, 30), (6, 2, 20), (20, 2, 30)],
)
def test_target_count_adapts_and_is_capped(chunks, mult, expected):
    assert target_count(chunks, mult) == expected
    assert 10 <= target_count(chunks, mult) <= 30


CHUNKS = [
    {
        "id": 1,
        "page": 1,
        "ordinal": 0,
        "text": "The Rajya Sabha is a permanent house.\nArticle 14 guarantees equality.",
    },
    {"id": 2, "page": 1, "ordinal": 1, "text": "The Speaker presides over the Lok Sabha."},
]


def q(**kw):
    base = {
        "stem": "Which house is permanent?",
        "options": ["Rajya Sabha", "Lok Sabha", "Vidhan Sabha", "Gram Sabha"],
        "answer_index": 0,
        "source_quote": "The Rajya Sabha is a permanent house.",
        "explanation": "x",
    }
    base.update(kw)
    return base


def test_validate_accepts_a_good_question_and_finds_its_chunk():
    ok, bad = validate_batch([q()], CHUNKS)
    assert len(ok) == 1 and ok[0]["source_chunk_id"] == 1 and not bad


def test_quote_matching_tolerates_whitespace_and_case_only():
    ok, _ = validate_batch([q(source_quote="the rajya   sabha is a PERMANENT house.")], CHUNKS)
    assert len(ok) == 1


@pytest.mark.parametrize(
    "bad,reason",
    [
        (q(source_quote="The Rajya Sabha is a temporary house."), "not verbatim"),
        (q(source_quote="Something from another book."), "not verbatim"),
        (q(options=["a", "a", "b", "c"]), "distinct"),
        (q(options=["a", "b", "c"]), "four options"),
        (q(answer_index=4), "answer_index"),
        (q(stem=""), "stem"),
    ],
)
def test_validate_discards_with_reason(bad, reason):
    ok, discarded = validate_batch([bad], CHUNKS)
    assert not ok and reason in discarded[0]["reason"]


def test_validate_discards_repeated_stems_and_quote_spanning_chunks():
    ok, bad = validate_batch([q(), q(source_quote="The Speaker presides over the Lok Sabha.")], CHUNKS)
    assert len(ok) == 1 and "repeated stem" in bad[0]["reason"]
    spanning = q(stem="Another?", source_quote="Article 14 guarantees equality. The Speaker presides")
    assert not validate_batch([spanning], CHUNKS)[0]


# ---------- end to end ----------
@pytest.mark.golden
def test_gate_is_grounded_validated_and_sized(tmp_path):
    llm = FakeLLM(bad=3)
    client = make(tmp_path, llm)
    sid, _ = finished_session(client, tmp_path)
    r = client.post(f"/sessions/{sid}/gate", headers=H)
    body = r.json()
    assert r.status_code == 200 and 10 <= len(body["questions"]) <= 30
    assert body["discarded"] >= 3 and body["fallback_used"] is False
    ids = [qq["id"] for qq in body["questions"]]
    assert all("answer_index" not in qq for qq in body["questions"])  # not revealed before answering
    rng = {
        c["id"]
        for p in (1, 2)
        for c in client.get(f"/library/documents/1/pages/{p}/chunks", headers=H).json()
    }
    from jarvis.db.migrate import connect  # noqa: F401  (documents the DB path used below)

    state = client.app.state.jarvis
    rows = state.conn.execute(
        "select q.*, c.text as ctext from question q join chunk c on c.id = q.source_chunk_id "
        f"where q.id in ({','.join('?' * len(ids))})",
        ids,
    ).fetchall()
    assert len(rows) == len(ids)
    for row in rows:
        assert row["source_chunk_id"] in rng and row["source"] == "generated"
        assert " ".join(row["source_quote"].split()).casefold() in " ".join(row["ctext"].split()).casefold()
    assert state.conn.execute("select count(*) from question").fetchone()[0] == len(
        ids
    )  # discards never stored


def test_gate_is_built_once(tmp_path):
    llm = FakeLLM()
    client = make(tmp_path, llm)
    sid, _ = finished_session(client, tmp_path)
    first = client.post(f"/sessions/{sid}/gate", headers=H).json()
    calls = len(llm.calls)
    again = client.post(f"/sessions/{sid}/gate", headers=H).json()
    assert [x["id"] for x in again["questions"]] == [x["id"] for x in first["questions"]]
    assert len(llm.calls) == calls
    assert client.get(f"/sessions/{sid}/gate", headers=H).json()["questions"] == again["questions"]


@pytest.mark.golden
def test_llm_failure_falls_back_to_offline_cloze(tmp_path):
    client = make(tmp_path, FakeLLM(error=ProviderError("unavailable", "down")))
    sid, _ = finished_session(client, tmp_path)
    body = client.post(f"/sessions/{sid}/gate", headers=H).json()
    assert body["fallback_used"] is True and len(body["questions"]) >= 10
    state = client.app.state.jarvis
    srcs = {r["source"] for r in state.conn.execute("select source from question")}
    assert srcs == {"fallback"}
    one = body["questions"][0]
    assert "_____" in one["stem"] and len(one["options"]) == 4


def test_bank_questions_are_interleaved_and_reported_ones_are_excluded(tmp_path):
    llm = FakeLLM()
    client = make(tmp_path, llm)
    sid1, _ = finished_session(client, tmp_path, "a")
    g1 = client.post(f"/sessions/{sid1}/gate", headers=H).json()
    # a second session on the same node (keyword/LLM tag both resolve to the polity subject)
    sid2, _ = finished_session(
        client, tmp_path, "b", pages=[PAGES[0] + "\nExtra Constitution line number one.", PAGES[1]]
    )
    bad_id = g1["questions"][0]["id"]
    assert client.post(f"/questions/{bad_id}/report", headers=H, json={"reason": "wrong"}).status_code == 200
    g2 = client.post(f"/sessions/{sid2}/gate", headers=H).json()
    inter = [x for x in g2["questions"] if x["interleaved"]]
    n = len(g2["questions"])
    assert 1 <= len(inter) <= round(0.2 * n) + 1
    assert bad_id not in [x["id"] for x in g2["questions"]]
    assert all(x["id"] in {y["id"] for y in g1["questions"]} for x in inter)
    state = client.app.state.jarvis
    assert (
        state.conn.execute("select status from question where id = ?", (bad_id,)).fetchone()[0] == "reported"
    )
    assert (
        state.conn.execute(
            "select count(*) from question_report where question_id = ?", (bad_id,)
        ).fetchone()[0]
        == 1
    )


def test_reported_question_disappears_from_its_own_gate(tmp_path):
    client = make(tmp_path, FakeLLM())
    sid, _ = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    qid = g["questions"][2]["id"]
    client.post(f"/questions/{qid}/report", headers=H, json={})
    assert qid not in [x["id"] for x in client.get(f"/sessions/{sid}/gate", headers=H).json()["questions"]]


def test_gate_api_errors(tmp_path):
    client = make(tmp_path, FakeLLM())
    assert client.post("/sessions/1/gate").status_code == 401
    assert client.post("/sessions/99/gate", headers=H).status_code == 404
    assert client.post("/questions/99/report", headers=H, json={}).status_code == 404
    p = tmp_path / "x.pdf"
    p.write_bytes(make_pdf(PAGES))
    doc = client.post("/library/documents", headers=H, json={"path": str(p)}).json()["id"]
    first = client.get(f"/library/documents/{doc}/pages/1/chunks", headers=H).json()[0]["id"]
    sid = client.post("/sessions", headers=H, json={"document_id": doc, "start_chunk_id": first}).json()["id"]
    assert client.post(f"/sessions/{sid}/gate", headers=H).status_code == 409  # still running


def test_context_pack_summarises_weak_nodes_and_mistakes(tmp_path):
    client = make(tmp_path, FakeLLM())
    sid, _ = finished_session(client, tmp_path)
    g = client.post(f"/sessions/{sid}/gate", headers=H).json()
    state = client.app.state.jarvis
    for i, item in enumerate(g["questions"][:6]):
        state.conn.execute(
            "insert into attempt(question_id, session_id, chosen_index, correct, confidence, "
            "mistake_type, answered_at) "
            "values (?,?,?,?,?,?,?)",
            (
                item["id"],
                sid,
                1,
                0 if i < 4 else 1,
                "A",
                "silly" if i < 3 else "conceptual" if i < 4 else None,
                "2999-01-01T00:00:00+00:00",
            ),
        )
    pack = build_context_pack(state.conn)
    assert "WEAK NODES" in pack and "Constitution and Polity" in pack and "33%" in pack
    assert "silly 75%" in pack.lower() and len(pack) <= 6000


def test_empty_context_pack_is_still_valid(tmp_path):
    client = make(tmp_path, FakeLLM())
    pack = build_context_pack(client.app.state.jarvis.conn)
    assert pack.startswith("STUDENT:") and "no attempts yet" in pack.lower()


def test_pack_is_part_of_the_generation_prompt(tmp_path):
    llm = FakeLLM()
    client = make(tmp_path, llm)
    sid, _ = finished_session(client, tmp_path)
    client.post(f"/sessions/{sid}/gate", headers=H)
    gen = [c for c in llm.calls if "Write exactly " in c[-1].content]
    assert gen and all("STUDENT:" in c[0].content for c in gen)
