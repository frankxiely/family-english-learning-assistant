from __future__ import annotations

from pathlib import Path

from services.api.app import core


def test_lesson_generation_uses_content_knowledge_route(isolated_runtime) -> None:
    run_id, plan = core.generate_lesson_plan_json("user_mom", "2026-07-01")
    lesson = core.normalize_lesson_plan(run_id, plan)

    assert plan["route_basis"]["content_route_item_id"] == "vi_phonics_001"
    assert plan["route_basis"]["content_route_day"] == 1
    assert plan["progress_summary"]["main_knowledge_label"] == "/iː/ 和 /ɪ/"
    assert lesson["source_basis"] == ["src_cefr_official", "src_cambridge_pre_a1", "src_oxford_3000_5000"]
    assert lesson["audio_assets"]
    assert {asset["provider"] for asset in lesson["audio_assets"]} == {"web_speech_runtime"}
    assert all("rate" in asset and "voice_key" in asset for asset in lesson["audio_assets"])
    assert lesson["vocabulary"][0]["part_of_speech_zh"]
    assert lesson["passage"]["lines"][0]["text"] == "Hi, Vi. Please sit here."
    assert lesson["quiz"]["questions"][0]["question_type"] == "sound_choice"
    assert lesson["quiz"]["questions"][0]["audio_text"] == "sit"
    assert any(asset["target_type"] == "quiz_question" for asset in lesson["audio_assets"])


def test_weekly_draft_generation_advances_content_route(isolated_runtime) -> None:
    drafts = core.generate_weekly_lesson_draft_workspaces("user_mom", "2026-07-01")

    assert len(drafts) == 7
    assert drafts[0]["lesson_date"] == "2026-07-01"
    assert drafts[-1]["lesson_date"] == "2026-07-07"

    day_one = core.get_lesson_draft(drafts[0]["draft_id"])["draft_json"]
    day_seven = core.get_lesson_draft(drafts[-1]["draft_id"])["draft_json"]

    assert day_one["route_basis"]["content_route_item_id"] == "vi_phonics_001"
    assert day_seven["route_basis"]["content_route_item_id"] == "vi_phonics_007"
    assert day_one["theme"] != day_seven["theme"]
    assert day_seven["vocabulary"][0]["learning_role"] == "review"


def test_weekly_generation_distributes_review_words(isolated_runtime) -> None:
    with core.connect() as conn:
        conn.executemany(
            """
            INSERT INTO review_queue (
              review_id, user_id, item_type, item_id, reason,
              priority, planned_review_date, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("review_test_book", "user_mom", "word", "word_book", "marked fuzzy", 90, "2026-07-01", "pending"),
                ("review_test_cup", "user_mom", "word", "word_cup", "marked fuzzy", 80, "2026-07-01", "pending"),
            ],
        )
        conn.commit()

    drafts = core.generate_weekly_lesson_draft_workspaces("user_mom", "2026-07-01", days=2)
    day_one = core.get_lesson_draft(drafts[0]["draft_id"])["draft_json"]
    day_two = core.get_lesson_draft(drafts[1]["draft_id"])["draft_json"]

    day_one_reviews = {
        item["word"].lower()
        for item in day_one["vocabulary"]
        if item.get("learning_role") == "review"
    }
    day_two_reviews = {
        item["word"].lower()
        for item in day_two["vocabulary"]
        if item.get("learning_role") == "review"
    }

    assert "book" in day_one_reviews
    assert "cup" in day_two_reviews
    assert "复习回顾" in day_one["knowledge_note"]["content"]


def test_generate_draft_audio_writes_local_urls(isolated_runtime, monkeypatch) -> None:
    def fake_tts(asset: dict, output_path: Path, voice: str, wpm: int) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"RIFF....WAVEfmt test audio")

    monkeypatch.setattr(core, "synthesize_local_tts_file", fake_tts)

    draft_id = core.generate_lesson_draft_workspace("user_mom", "2026-07-01")
    result = core.generate_lesson_draft_audio(draft_id)
    draft = core.get_lesson_draft(draft_id)
    lesson = draft["draft_json"]
    audio_assets = lesson["audio_assets"]

    assert result["generated_count"] == len(audio_assets)
    assert result["error_count"] == 0
    assert all(asset["provider"] == core.LOCAL_TTS_PROVIDER for asset in audio_assets)
    assert all(asset["local_url"].startswith("/audio/") for asset in audio_assets)
    assert any(asset["target_type"] == "quiz_question" for asset in audio_assets)

    first_path = core.AUDIO_DIR.parent / audio_assets[0]["local_url"].lstrip("/")
    assert first_path.exists()

    with core.connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS count FROM asset_sources WHERE asset_type = 'audio'"
        ).fetchone()
    assert row["count"] == len(audio_assets)


def test_generate_pending_draft_audio_batch(isolated_runtime, monkeypatch) -> None:
    def fake_tts(asset: dict, output_path: Path, voice: str, wpm: int) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"RIFF....WAVEfmt test audio")

    monkeypatch.setattr(core, "synthesize_local_tts_file", fake_tts)

    core.generate_weekly_lesson_draft_workspaces("user_mom", "2026-07-01", days=2)
    result = core.generate_pending_lesson_drafts_audio("user_mom", "2026-07-01", days=2)

    assert result["draft_count"] == 2
    assert result["generated_count"] > 0
    assert result["error_count"] == 0


def test_frank_lesson_generation_uses_advanced_user_route(isolated_runtime) -> None:
    run_id, plan = core.generate_lesson_plan_json("user_admin_1", "2026-07-01")
    lesson = core.normalize_lesson_plan(run_id, plan)

    assert plan["route_basis"]["content_route_item_id"] == "frank_business_001"
    assert plan["difficulty"] == "advanced"
    assert plan["progress_summary"]["route_module_label"] == "高阶诊断和口语校准"
    assert lesson["theme"] == "高阶诊断课：商务自我介绍与发音校准"
    assert lesson["vocabulary"][0]["word"] == "concise"
    assert lesson["passage"]["title"] == "A short briefing"
    assert lesson["quiz"]["questions"][0]["question_id"] == "frank_business_001_q1"


def test_published_lesson_can_be_completed_and_generate_next_draft(isolated_runtime) -> None:
    lesson_date = "2026-07-02"
    draft_id = core.generate_lesson_draft_workspace("user_mom", lesson_date)
    published = core.publish_lesson_draft_workspace(draft_id, reason="pytest_publish")
    lesson = core.get_today_lesson("user_mom", lesson_date)

    assert published["status"] == "published"
    assert lesson["lesson_date"] == lesson_date

    answers = {
        question["prompt"]: question["answer"]
        for question in lesson["quiz"]["questions"]
    }
    word_mastery = {
        item["word"]: "known"
        for item in lesson["vocabulary"]
    }
    result = core.submit_learning_progress(
        "user_mom",
        {
            "lesson_asset_id": lesson["lesson_asset_id"],
            "completed_sections": ["goal", "vocabulary", "passage", "knowledge", "quiz", "summary"],
            "word_mastery": word_mastery,
            "quiz_answers": answers,
            "learning_minutes": lesson["estimated_minutes"],
            "self_rating": "刚好",
        },
        lesson_date,
    )

    assert result["status"] == "ok"
    assert result["quiz_score"] == 1
    assert result["next_draft_id"].endswith("20260703")

    with core.connect() as conn:
        status = conn.execute(
            "SELECT learning_days, streak_days, last_learning_date FROM learning_status WHERE user_id = ?",
            ("user_mom",),
        ).fetchone()
        attempts = conn.execute("SELECT COUNT(*) AS count FROM quiz_attempts").fetchone()
        review = conn.execute("SELECT COUNT(*) AS count FROM learning_review_assets").fetchone()

    assert status["learning_days"] == 1
    assert status["streak_days"] == 1
    assert status["last_learning_date"] == lesson_date
    assert attempts["count"] == 1
    assert review["count"] == 1


def test_admin_account_name_and_password_survive_init_db(isolated_runtime) -> None:
    session = core.authenticate_local_account("AdminXLY", "Frank1229")
    renamed = core.update_account_display_name(session["session_token"], "Admin_Test_Name")
    assert renamed["nickname"] == "Admin_Test_Name"

    core.update_account_password(session["session_token"], "Frank1229", "Frank1229New")
    core.init_db()

    with core.connect() as conn:
        user = conn.execute("SELECT nickname FROM users WHERE user_id = ?", ("user_admin_1",)).fetchone()
        admin = conn.execute("SELECT nickname FROM admin_users WHERE admin_id = ?", ("AdminXLY",)).fetchone()

    assert user["nickname"] == "Admin_Test_Name"
    assert admin["nickname"] == "Admin_Test_Name"

    new_session = core.authenticate_local_account("AdminXLY", "Frank1229New")
    assert new_session["nickname"] == "Admin_Test_Name"

    try:
        core.authenticate_local_account("AdminXLY", "Frank1229")
    except ValueError:
        pass
    else:
        raise AssertionError("old password should not work after password update")
