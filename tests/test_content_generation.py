from __future__ import annotations

import json
from pathlib import Path

from services.api.app import core


def insert_published_route_day(user_id: str, lesson_date: str, route_day: int) -> str:
    lesson_asset_id = f"lesson_completed_{user_id}_{lesson_date.replace('-', '')}_{route_day}"
    lesson_json = {
        "schema_version": "lesson_json.v1",
        "lesson_asset_id": lesson_asset_id,
        "user_id": user_id,
        "lesson_date": lesson_date,
        "theme": f"completed route day {route_day}",
        "route_basis": {
            "content_route_day": route_day,
            "content_route_item_id": f"route_day_{route_day}",
        },
    }
    text = json.dumps(lesson_json, ensure_ascii=False, sort_keys=True)
    with core.connect() as conn:
        conn.execute(
            """
            INSERT INTO lesson_json_assets (
              lesson_asset_id, user_id, lesson_date, schema_version, source_provider,
              status, validation_status, human_readable_summary, content_hash, lesson_json,
              published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lesson_asset_id,
                user_id,
                lesson_date,
                "lesson_json.v1",
                "pytest",
                "published",
                "passed",
                f"completed route day {route_day}",
                f"hash_completed_{route_day}",
                text,
                f"{lesson_date}T08:00:00",
            ),
        )
        conn.commit()
    return lesson_asset_id


def insert_completed_route_day(user_id: str, lesson_date: str, route_day: int) -> str:
    lesson_asset_id = insert_published_route_day(user_id, lesson_date, route_day)
    with core.connect() as conn:
        conn.execute(
            """
            INSERT INTO daily_progress (
              progress_id, user_id, lesson_asset_id, progress_date,
              completed_sections_json, learning_minutes, self_rating, generated_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                f"progress_{lesson_asset_id}",
                user_id,
                lesson_asset_id,
                lesson_date,
                "[]",
                30,
                "刚好",
                f"completed route day {route_day}",
            ),
        )
        conn.commit()
    return lesson_asset_id


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


def test_quiz_answer_positions_are_randomized_per_lesson(isolated_runtime) -> None:
    for user_id in ("user_mom", "user_admin_1"):
        run_id, plan = core.generate_lesson_plan_json(user_id, "2026-07-01")
        lesson = core.normalize_lesson_plan(run_id, plan)

        positions = []
        for question in lesson["quiz"]["questions"]:
            options = question["options"]
            answer = question["answer"]
            assert answer in options
            if len(options) > 1:
                positions.append(options.index(answer))

        assert len(set(positions)) > 1
        quiz_before = json.dumps(lesson["quiz"], ensure_ascii=False, sort_keys=True)
        core.randomize_quiz_options(lesson)
        assert json.dumps(lesson["quiz"], ensure_ascii=False, sort_keys=True) == quiz_before


def test_quiz_randomizer_forces_non_uniform_answer_positions(monkeypatch) -> None:
    monkeypatch.setattr(core, "next_answer_position", lambda _cycles, _count, _rng: 0)
    lesson = {
        "user_id": "user_test",
        "lesson_date": "2026-07-01",
        "lesson_asset_id": "lesson_test",
        "source_generation_run_id": "gen_test",
        "quiz": {
            "questions": [
                {"prompt": "q1", "options": ["A", "B", "C"], "answer": "A"},
                {"prompt": "q2", "options": ["D", "E", "F"], "answer": "D"},
            ]
        },
    }

    core.randomize_quiz_options(lesson)
    positions = [
        question["options"].index(question["answer"])
        for question in lesson["quiz"]["questions"]
    ]

    assert len(set(positions)) > 1


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


def test_vi_easy_streak_generates_challenge_lesson(isolated_runtime) -> None:
    easy_review = {
        "quiz_score": 1.0,
        "self_rating": "轻松",
        "weak_words": [],
        "difficulty_points": [],
        "incorrect_answers": [],
    }
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (9, 3, "2026-07-10", "user_mom"),
        )
        for index in range(3):
            review_date = f"2026-07-{8 + index:02d}"
            lesson_asset_id = f"lesson_easy_{index}"
            conn.execute(
                """
                INSERT INTO lesson_json_assets (
                  lesson_asset_id, user_id, lesson_date, schema_version, source_provider,
                  status, validation_status, human_readable_summary, content_hash, lesson_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lesson_asset_id,
                    "user_mom",
                    review_date,
                    "lesson_json.v1",
                    "pytest",
                    "published",
                    "passed",
                    "easy fixture",
                    f"hash_easy_{index}",
                    "{}",
                ),
            )
            conn.execute(
                """
                INSERT INTO learning_review_assets (
                  review_asset_id, user_id, lesson_asset_id, review_date,
                  schema_version, status, validation_status, human_readable_summary, review_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"review_easy_{index}",
                    "user_mom",
                    lesson_asset_id,
                    review_date,
                    "learning_review_json.v1",
                    "published",
                    "passed",
                    "测试正确率 100%，今天没有明显薄弱词。",
                    json.dumps({**easy_review, "review_date": review_date}, ensure_ascii=False),
                ),
            )
        conn.commit()

    run_id, plan = core.generate_lesson_plan_json("user_mom", "2026-07-11")
    lesson = core.normalize_lesson_plan(run_id, plan)

    assert plan["route_basis"]["content_route_item_id"] == "vi_nce_010"
    assert plan["difficulty"] == "challenge"
    assert lesson["theme"] == "礼貌打断与物品确认"
    assert plan["route_basis"]["difficulty_profile"]["level"] == "challenge"
    assert len(lesson["vocabulary"]) >= 10
    assert len(lesson["quiz"]["questions"]) >= 8
    assert lesson["passage"]["title"] == "Is this your ticket?"
    assert {"sentence_audio_choice", "sentence_order", "scenario_choice"}.issubset(
        {question["question_type"] for question in lesson["quiz"]["questions"]}
    )


def test_vi_travel_extension_generates_two_week_route(isolated_runtime) -> None:
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (25, 7, "2026-08-03", "user_mom"),
        )
        conn.commit()

    drafts = core.generate_weekly_lesson_draft_workspaces("user_mom", "2026-08-04", days=14)
    day_one = core.get_lesson_draft(drafts[0]["draft_id"])["draft_json"]
    day_fourteen = core.get_lesson_draft(drafts[-1]["draft_id"])["draft_json"]

    assert len(drafts) == 14
    assert day_one["route_basis"]["content_route_item_id"] == "vi_travel_026"
    assert day_fourteen["route_basis"]["content_route_item_id"] == "vi_travel_039"
    assert day_one["theme"] == "澳洲旅行第一天：抵达悉尼机场"
    assert day_fourteen["theme"] == "澳洲旅行第十四天：返程确认和阶段复盘"
    assert len(day_one["vocabulary"]) == 10
    assert len(day_fourteen["quiz"]["questions"]) == 9
    assert day_one["passage"]["title"] == "At Sydney Airport"
    assert day_fourteen["passage"]["title"] == "Going home"


def test_vi_work_life_extension_generates_next_two_week_route(isolated_runtime) -> None:
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (39, 14, "2026-08-19", "user_mom"),
        )
        conn.commit()
    insert_completed_route_day("user_mom", "2026-08-19", 39)

    drafts = core.generate_weekly_lesson_draft_workspaces("user_mom", "2026-08-20", days=14)
    day_one = core.get_lesson_draft(drafts[0]["draft_id"])["draft_json"]
    day_fourteen = core.get_lesson_draft(drafts[-1]["draft_id"])["draft_json"]

    assert len(drafts) == 14
    assert day_one["route_basis"]["content_route_day"] == 40
    assert day_one["route_basis"]["content_route_item_id"] == "vi_work_040"
    assert day_one["theme"] == "回到工作第一天：办公室寒暄和状态"
    assert day_fourteen["route_basis"]["content_route_day"] == 53
    assert day_fourteen["route_basis"]["content_route_item_id"] == "vi_work_053"
    assert day_fourteen["theme"] == "两周工作英语复盘"
    assert len(day_one["vocabulary"]) == 10
    assert len(day_fourteen["quiz"]["questions"]) == 9


def test_vi_daily_life_extension_generates_following_two_week_route(isolated_runtime) -> None:
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (53, 28, "2026-09-08", "user_mom"),
        )
        conn.commit()
    insert_completed_route_day("user_mom", "2026-09-08", 53)

    drafts = core.generate_weekly_lesson_draft_workspaces("user_mom", "2026-09-09", days=14)
    day_one = core.get_lesson_draft(drafts[0]["draft_id"])["draft_json"]
    day_fourteen = core.get_lesson_draft(drafts[-1]["draft_id"])["draft_json"]

    assert len(drafts) == 14
    assert day_one["route_basis"]["content_route_day"] == 54
    assert day_one["route_basis"]["content_route_item_id"] == "vi_daily_054"
    assert day_one["theme"] == "回到日常第一天：早餐和一天安排"
    assert day_fourteen["route_basis"]["content_route_day"] == 67
    assert day_fourteen["route_basis"]["content_route_item_id"] == "vi_daily_067"
    assert day_fourteen["theme"] == "两周日常生活英语复盘"
    assert day_one["passage"]["title"] == "Breakfast at home"
    assert day_fourteen["passage"]["title"] == "My daily routine"
    assert len(day_one["vocabulary"]) == 10
    assert len(day_fourteen["quiz"]["questions"]) == 9


def test_generation_uses_completed_route_day_after_skipped_calendar_day(isolated_runtime) -> None:
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (27, 1, "2026-08-06", "user_mom"),
        )
        conn.commit()
    insert_completed_route_day("user_mom", "2026-08-06", 28)

    _run_id, plan = core.generate_lesson_plan_json("user_mom", "2026-08-07")

    assert plan["route_basis"]["content_route_day"] == 29
    assert plan["route_basis"]["content_route_item_id"] == "vi_travel_029"
    assert plan["theme"] == "澳洲旅行第四天：咖啡馆点餐和菜名"


def test_generation_advances_after_uncompleted_published_day(isolated_runtime) -> None:
    insert_published_route_day("user_mom", "2026-08-11", 31)

    _run_id, plan = core.generate_lesson_plan_json("user_mom", "2026-08-12")

    assert plan["route_basis"]["content_route_day"] == 32
    assert plan["route_basis"]["content_route_item_id"] == "vi_travel_032"
    assert plan["theme"] == "澳洲旅行第一周复盘：说出行程"


def test_auto_publish_regenerates_stale_pending_draft(isolated_runtime) -> None:
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (28, 2, "2026-08-08", "user_mom"),
        )
        conn.commit()
    stale_draft_id = core.generate_lesson_draft_workspace(
        "user_mom",
        "2026-08-09",
        action="test_generate_stale_draft",
        route_day_offset=2,
    )
    stale_draft = core.get_lesson_draft(stale_draft_id)["draft_json"]
    assert stale_draft["route_basis"]["content_route_day"] == 31

    insert_completed_route_day("user_mom", "2026-08-08", 29)
    with core.connect() as conn:
        conn.execute(
            "UPDATE learning_status SET learning_days = ?, streak_days = ?, last_learning_date = ? WHERE user_id = ?",
            (29, 3, "2026-08-08", "user_mom"),
        )
        conn.commit()

    lesson_asset_id = core.generate_and_save_today("user_mom", "2026-08-09")
    with core.connect() as conn:
        lesson = core.fetch_lesson_asset(conn, lesson_asset_id)["lesson_json"]

    assert lesson["route_basis"]["content_route_day"] == 30
    assert lesson["route_basis"]["content_route_item_id"] == "vi_travel_030"
    assert core.get_lesson_draft(stale_draft_id)["status"] == "published"


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
