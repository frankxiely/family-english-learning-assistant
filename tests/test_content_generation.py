from __future__ import annotations

from services.api.app import core


def test_lesson_generation_uses_content_knowledge_route(isolated_runtime) -> None:
    run_id, plan = core.generate_lesson_plan_json("user_mom", "2026-07-01")
    lesson = core.normalize_lesson_plan(run_id, plan)

    assert plan["route_basis"]["content_route_item_id"] == "kb_route_phonics_001"
    assert plan["route_basis"]["content_route_day"] == 1
    assert plan["progress_summary"]["main_knowledge_label"] == "/iː/ 和 /ɪ/"
    assert lesson["source_basis"] == ["src_cefr_official", "src_cambridge_pre_a1", "src_oxford_3000_5000"]
    assert lesson["audio_assets"]
    assert {asset["provider"] for asset in lesson["audio_assets"]} == {"web_speech_runtime"}
    assert all("rate" in asset and "voice_key" in asset for asset in lesson["audio_assets"])
    assert lesson["vocabulary"][0]["part_of_speech_zh"]


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
