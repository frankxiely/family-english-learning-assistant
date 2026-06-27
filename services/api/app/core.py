from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]


def resolve_project_path(raw_path: str | Path) -> Path:
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else ROOT / path


DB_PATH = resolve_project_path(os.environ.get("MOMO_DB_PATH", "data/sqlite/app.db"))
SCHEMA_PATH = ROOT / "db" / "migrations" / "001_initial_schema.sql"
SEED_PATH = ROOT / "db" / "seeds" / "seed_v1_1.sql"
RAW_DIR = ROOT / "data" / "lesson_json" / "raw"
NORMALIZED_DIR = ROOT / "data" / "lesson_json" / "normalized"
VALIDATED_DIR = ROOT / "data" / "lesson_json" / "validated"
EXPORT_DIR = ROOT / "data" / "lesson_exports"
TEACHING_KNOWLEDGE_DIR = ROOT / "data" / "teaching_knowledge"
STARTER_PHONICS_ROUTE_PATH = TEACHING_KNOWLEDGE_DIR / "starter_phonics_route.v1.json"
USER_ROUTE_DIR = TEACHING_KNOWLEDGE_DIR / "user_routes"
USER_ROUTE_PATHS = {
    "user_mom": USER_ROUTE_DIR / "vi_route.v1.json",
    "user_admin_1": USER_ROUTE_DIR / "frank_route.v1.json",
}
WEB_PUBLIC_DIR = ROOT / "apps" / "web" / "public"
WORD_IMAGE_DIR = WEB_PUBLIC_DIR / "generated" / "word_images"
SESSION_TTL_HOURS = 12

STARTER_WORD_BANK: dict[str, dict[str, Any]] = {
    "see": {"phonetic": "/siː/", "part_of_speech": "verb", "part_of_speech_zh": "动词", "meaning": "看见", "needs_image": True},
    "sit": {"phonetic": "/sɪt/", "part_of_speech": "verb", "part_of_speech_zh": "动词", "meaning": "坐", "needs_image": True},
    "seat": {"phonetic": "/siːt/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "座位", "needs_image": True},
    "it": {"phonetic": "/ɪt/", "part_of_speech": "pronoun", "part_of_speech_zh": "代词", "meaning": "它", "needs_image": False},
    "pen": {"phonetic": "/pen/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "笔", "needs_image": True},
    "bed": {"phonetic": "/bed/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "床", "needs_image": True},
    "bag": {"phonetic": "/bæɡ/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "包", "needs_image": True},
    "map": {"phonetic": "/mæp/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "地图", "needs_image": True},
    "car": {"phonetic": "/kɑːr/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "汽车", "needs_image": True},
    "cup": {"phonetic": "/kʌp/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "杯子", "needs_image": True},
    "arm": {"phonetic": "/ɑːrm/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "手臂", "needs_image": True},
    "sun": {"phonetic": "/sʌn/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "太阳", "needs_image": True},
    "food": {"phonetic": "/fuːd/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "食物", "needs_image": True},
    "book": {"phonetic": "/bʊk/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "书", "needs_image": True},
    "good": {"phonetic": "/ɡʊd/", "part_of_speech": "adjective", "part_of_speech_zh": "形容词", "meaning": "好的", "needs_image": False},
    "look": {"phonetic": "/lʊk/", "part_of_speech": "verb", "part_of_speech_zh": "动词", "meaning": "看", "needs_image": True},
    "day": {"phonetic": "/deɪ/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "一天", "needs_image": True},
    "name": {"phonetic": "/neɪm/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "名字", "needs_image": True},
    "i": {"phonetic": "/aɪ/", "part_of_speech": "pronoun", "part_of_speech_zh": "代词", "meaning": "我", "needs_image": False},
    "like": {"phonetic": "/laɪk/", "part_of_speech": "verb", "part_of_speech_zh": "动词", "meaning": "喜欢", "needs_image": True},
    "bank": {"phonetic": "/bæŋk/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "银行", "needs_image": True},
    "please": {"phonetic": "/pliːz/", "part_of_speech": "interjection", "part_of_speech_zh": "礼貌用语", "meaning": "请", "needs_image": False},
    "today": {"phonetic": "/təˈdeɪ/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "今天", "needs_image": False},
    "tea": {"phonetic": "/tiː/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "茶", "needs_image": True},
    "desk": {"phonetic": "/desk/", "part_of_speech": "noun", "part_of_speech_zh": "名词", "meaning": "书桌", "needs_image": True},
    "is": {"phonetic": "/ɪz/", "part_of_speech": "verb", "part_of_speech_zh": "动词", "meaning": "是", "needs_image": False},
    "zero": {"phonetic": "/ˈzɪroʊ/", "part_of_speech": "number", "part_of_speech_zh": "数词", "meaning": "零", "needs_image": False},
    "me": {"phonetic": "/miː/", "part_of_speech": "pronoun", "part_of_speech_zh": "代词", "meaning": "我；我自己", "needs_image": False},
}

SENTENCE_TRANSLATIONS = {
    "I see it.": "我看见它。",
    "Sit on the seat.": "坐在座位上。",
    "I see a pen.": "我看见一支笔。",
    "It is a bag.": "它是一个包。",
    "I see a cup.": "我看见一个杯子。",
    "The car is here.": "车在这里。",
    "Look at the book.": "看这本书。",
    "The food is good.": "食物很好。",
    "I am Vi.": "我是 Vi。",
    "I like it.": "我喜欢它。",
    "Please sit.": "请坐。",
    "This is a bank.": "这是一家银行。",
    "Good day.": "日安。",
    "Tea is on the desk.": "茶在桌子上。",
    "Please see this.": "请看这个。",
    "It is zero.": "它是零。",
    "Read it.": "读它。",
    "I can read it.": "我能读它。",
}

ADMIN_FIELDS = {
    "age_band",
    "occupation",
    "english_foundation",
    "goal",
    "daily_minutes",
    "interest_preferences",
    "scenario_preferences",
    "visual_preferences",
    "pronunciation_preference",
    "cefr_stage",
    "admin_note",
}


def today_iso() -> str:
    return date.today().isoformat()


def next_day_iso(day: str) -> str:
    return (date.fromisoformat(day) + timedelta(days=1)).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(seed_test_data: bool = False) -> None:
    with connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        if seed_test_data:
            conn.executescript(SEED_PATH.read_text(encoding="utf-8"))
        log_debug(
            conn,
            "db",
            "info",
            "database initialized",
            {"db_path": str(DB_PATH), "seed_test_data": seed_test_data},
        )
        conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def safe_json_loads(text: str | None, fallback: Any) -> Any:
    if not text:
        return fallback
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return fallback


def load_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def path_for_record(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_starter_phonics_route() -> dict[str, Any]:
    data = load_json_file(STARTER_PHONICS_ROUTE_PATH, {})
    return data if isinstance(data, dict) else {}


def load_user_learning_route(user_id: str | None) -> dict[str, Any]:
    if not user_id:
        return {}
    path = USER_ROUTE_PATHS.get(user_id)
    if not path:
        return {}
    data = load_json_file(path, {})
    return data if isinstance(data, dict) else {}


def route_data_for_user(user_id: str | None) -> dict[str, Any]:
    return load_user_learning_route(user_id) or load_starter_phonics_route()


def pick_content_route_item(context: dict[str, Any]) -> dict[str, Any]:
    route_data = route_data_for_user(context.get("user_id"))
    route_items = route_data.get("route_items") or []
    if not route_items:
        return {}
    status = context.get("status") or {}
    try:
        learning_days = int(status.get("learning_days") or 0)
    except (TypeError, ValueError):
        learning_days = 0
    index = max(0, min(learning_days, len(route_items) - 1))
    item = dict(route_items[index])
    item["daily_constraints"] = route_data.get("daily_constraints") or {}
    item["stage"] = route_data.get("stage") or {}
    item["route_schema_version"] = route_data.get("schema_version")
    item["route_user_id"] = route_data.get("user_id")
    return item


def build_vocabulary_item(word: str, phonics_focus: list[str]) -> dict[str, Any]:
    key = word.lower()
    source = STARTER_WORD_BANK.get(key, {})
    part_of_speech = str(source.get("part_of_speech") or "word")
    needs_image = bool(source.get("needs_image", part_of_speech in {"noun", "verb"}))
    return {
        "word": word,
        "phonetic": source.get("phonetic") or f"/{word.lower()}/",
        "part_of_speech": part_of_speech,
        "part_of_speech_zh": source.get("part_of_speech_zh") or "单词",
        "meaning": source.get("meaning") or "今日词",
        "cefr_level": "pre_a1",
        "is_phonics_word": True,
        "phonics_focus": phonics_focus,
        "needs_image": needs_image,
        "image_hint": f"simple clear illustration of {word}" if needs_image else None,
        "audio_text": word,
    }


def build_route_vocabulary(content_route_item: dict[str, Any], phonics_focus: list[str]) -> list[dict[str, Any]]:
    vocabulary_items = content_route_item.get("vocabulary") or []
    if vocabulary_items:
        result = []
        for source in vocabulary_items:
            if isinstance(source, str):
                result.append(build_vocabulary_item(source, phonics_focus))
                continue
            word = str(source.get("word") or "").strip()
            if not word:
                continue
            base = build_vocabulary_item(word, phonics_focus)
            merged = {**base, **source}
            merged["audio_text"] = merged.get("audio_text") or merged["word"]
            if "cefr_level" not in source:
                merged["cefr_level"] = content_route_item.get("cefr_level") or content_route_item.get("level_code") or base["cefr_level"]
            if "is_phonics_word" not in source:
                merged["is_phonics_word"] = bool(phonics_focus)
            merged["needs_image"] = bool(merged.get("needs_image", base["needs_image"]))
            if merged.get("needs_image") and not merged.get("image_hint"):
                merged["image_hint"] = f"simple clear illustration of {merged['word']}"
            result.append(merged)
        return result
    new_words = [str(item) for item in content_route_item.get("new_words") or []]
    review_words = [str(item) for item in content_route_item.get("review_words") or []]
    return [build_vocabulary_item(word, phonics_focus) for word in (new_words or review_words[:4])]


def build_audio_asset(
    target_type: str,
    target_ref: str,
    text: str,
    *,
    role: str | None = None,
    rate: float = 0.88,
) -> dict[str, Any]:
    content_hash = hashlib.sha256(f"{target_type}:{target_ref}:{text}:{role}:{rate}".encode("utf-8")).hexdigest()[:16]
    return {
        "audio_id": f"audio_{asset_slug(target_type)}_{asset_slug(target_ref)}_{content_hash}",
        "target_type": target_type,
        "target_ref": target_ref,
        "text": text,
        "role": role,
        "provider": "web_speech_runtime",
        "voice_key": "browser-en-US-default",
        "locale": "en-US",
        "rate": rate,
        "pitch": 1,
        "style": "neutral",
        "local_url": None,
        "content_hash": content_hash,
        "duration_ms": None,
    }


def build_kb_passage(content_route_item: dict[str, Any], vocabulary: list[dict[str, Any]]) -> dict[str, Any]:
    provided_passage = content_route_item.get("passage")
    if isinstance(provided_passage, dict):
        passage = dict(provided_passage)
        lines = [dict(line) for line in passage.get("lines") or []]
        words = {item["word"].lower() for item in vocabulary}
        for line in lines:
            text = str(line.get("text") or "")
            line["audio_text"] = line.get("audio_text") or text
            line["highlight_words"] = line.get("highlight_words") or [
                word for word in words if re.search(rf"\b{re.escape(word)}\b", text, re.I)
            ]
            line["audio_ref"] = line.get("audio_ref") or build_audio_asset(
                "passage_line",
                f"{line.get('role')}_{text}",
                text,
                role=line.get("role"),
            )["audio_id"]
        passage["lines"] = lines
        passage["passage_type"] = passage.get("passage_type") or "dialogue"
        passage["english_text"] = passage.get("english_text") or "\n".join(
            f"{line.get('role')}: {line.get('text')}" for line in lines
        )
        passage["chinese_support"] = passage.get("chinese_support") or "\n".join(
            f"{line.get('role')}：{line.get('translation')}" for line in lines if line.get("translation")
        )
        passage["translation"] = passage.get("translation") or "\n".join(
            str(line.get("translation") or "") for line in lines
        )
        passage["difficult_words"] = passage.get("difficult_words") or []
        passage["audio_plan"] = passage.get("audio_plan") or {
            "normal_rate": 0.88,
            "slow_rate": 0.68,
            "provider": "web_speech_runtime",
            "fallback": True,
        }
        return passage

    sentence_patterns = content_route_item.get("sentence_patterns") or ["I see it.", "Read it."]
    first = str(sentence_patterns[0])
    second = str(sentence_patterns[1] if len(sentence_patterns) > 1 else sentence_patterns[0])
    lines = [
        {"role": "Teacher", "text": first, "translation": SENTENCE_TRANSLATIONS.get(first, "请跟读这句话。")},
        {"role": "Vi", "text": first, "translation": SENTENCE_TRANSLATIONS.get(first, "我来跟读。")},
        {"role": "Teacher", "text": second, "translation": SENTENCE_TRANSLATIONS.get(second, "再读一句。")},
        {"role": "Vi", "text": second, "translation": SENTENCE_TRANSLATIONS.get(second, "我再读一句。")},
    ]
    words = {item["word"].lower() for item in vocabulary}
    for line in lines:
        line["audio_text"] = line["text"]
        line["highlight_words"] = [word for word in words if re.search(rf"\b{re.escape(word)}\b", line["text"], re.I)]
        line["audio_ref"] = build_audio_asset("passage_line", f"{line['role']}_{line['text']}", line["text"], role=line["role"])["audio_id"]
    return {
        "title": second.rstrip(".") if len(second.split()) <= 5 else str(content_route_item.get("passage_module_label") or "今日对话"),
        "passage_type": "dialogue",
        "english_text": "\n".join(f"{line['role']}: {line['text']}" for line in lines),
        "chinese_support": "\n".join(f"{line['role']}：{line['translation']}" for line in lines),
        "lines": lines,
        "translation": "\n".join(line["translation"] for line in lines),
        "difficult_words": [
            {"word": "the", "meaning": "这个；那个"},
            {"word": "on", "meaning": "在……上"},
        ],
        "audio_plan": {
            "normal_rate": 0.88,
            "slow_rate": 0.68,
            "provider": "web_speech_runtime",
            "fallback": True,
        },
    }


def build_kb_audio_assets(template: dict[str, Any]) -> list[dict[str, Any]]:
    assets = [
        build_audio_asset("word", f"word_{item['word'].lower()}", item.get("audio_text") or item["word"], rate=0.86)
        for item in template.get("vocabulary", [])
    ]
    for line in (template.get("passage") or {}).get("lines", []):
        text = str(line.get("audio_text") or line.get("text") or "")
        if text:
            assets.append(build_audio_asset("passage_line", f"{line.get('role')}_{text}", text, role=line.get("role")))
            assets.append(
                build_audio_asset(
                    "passage_line_slow",
                    f"{line.get('role')}_{text}",
                    text,
                    role=line.get("role"),
                    rate=0.68,
                )
            )
    return assets


def build_kb_route_template(content_route_item: dict[str, Any], review_text: str) -> dict[str, Any]:
    phonics_focus = [str(item) for item in content_route_item.get("phonics_focus") or []]
    review_words = [str(item) for item in content_route_item.get("review_words") or []]
    vocabulary = build_route_vocabulary(content_route_item, phonics_focus)
    focus_text = " 和 ".join(phonics_focus) if phonics_focus else str(content_route_item.get("main_knowledge_label") or "今日知识点")
    route_label = str(content_route_item.get("route_module_label") or "音标和基础拼读")
    passage_label = str(content_route_item.get("passage_module_label") or "今日对话")
    passage = build_kb_passage(content_route_item, vocabulary)
    if phonics_focus:
        focus_section_content = f"{focus_text} 是今天的主知识点。先听差别，再读单词。"
        default_content_lines = [
            f"1. 今天的主题是 {focus_text}，先听清声音，再跟读单词。",
            "2. 音节里通常有一个核心元音，拼读时先找到这个核心声音。",
            f"3. 今天的词是 {', '.join(item['word'] for item in vocabulary) or '复习词'}，只记一个核心意思。",
            f"4. 最后把这些词放进“{passage_label}”里读出来。",
        ]
    else:
        focus_section_content = f"{focus_text} 是今天的主知识点。先看表达结构，再做短句输出。"
        default_content_lines = [
            f"1. 今天的主题是 {focus_text}，先明确场景、对象和沟通目的。",
            "2. 高质量表达优先做到清楚、简洁、有重点，不靠堆叠长句。",
            f"3. 今天的词是 {', '.join(item['word'] for item in vocabulary) or '复习词'}，每个先记一个核心用法。",
            f"4. 最后把这些表达放进“{passage_label}”里读出来。",
        ]
    if review_words:
        default_content_lines.append(f"5. 今天主要复习 {', '.join(review_words[:4])}，不增加太多新负担。")
    content_lines = [str(line) for line in content_route_item.get("knowledge_cards") or default_content_lines]
    quiz_words = vocabulary[:3] or [build_vocabulary_item("see", phonics_focus)]
    provided_questions = content_route_item.get("quiz_questions") or []
    questions = [
        {
            "question_id": str(question.get("question_id") or f"{content_route_item.get('route_item_id')}_q{index}"),
            "prompt": str(question.get("prompt") or ""),
            "options": [str(option) for option in question.get("options") or []],
            "answer": str(question.get("answer") or ""),
            "explanation": str(question.get("explanation") or ""),
            "related_knowledge_id": question.get("related_knowledge_id") or content_route_item.get("knowledge_id"),
            "related_word_ids": question.get("related_word_ids") or [],
            "error_tag": question.get("error_tag") or "route_quiz",
        }
        for index, question in enumerate(provided_questions, start=1)
        if isinstance(question, dict)
    ] or [
        {
            "question_id": f"{content_route_item.get('route_item_id')}_q1",
            "prompt": "今天主要练习的是？",
            "options": [focus_text, "长篇阅读", "复杂语法"],
            "answer": focus_text,
            "explanation": f"今天只集中练习 {focus_text}。",
            "related_knowledge_id": content_route_item.get("knowledge_id"),
            "related_word_ids": [],
            "error_tag": "knowledge_focus",
        },
        {
            "question_id": f"{content_route_item.get('route_item_id')}_q2",
            "prompt": f"{quiz_words[0]['word']} 的核心意思是？",
            "options": [quiz_words[0]["meaning"], "会议", "明天"],
            "answer": quiz_words[0]["meaning"],
            "explanation": f"{quiz_words[0]['word']} 今天只记“{quiz_words[0]['meaning']}”。",
            "related_knowledge_id": content_route_item.get("knowledge_id"),
            "related_word_ids": [f"word_{quiz_words[0]['word'].lower()}"],
            "error_tag": "word_meaning",
        },
        {
            "question_id": f"{content_route_item.get('route_item_id')}_q3",
            "prompt": "今天表达练习最应该优先做到什么？" if not phonics_focus else "一个音节里通常最核心的声音是？",
            "options": ["清楚、简洁、有重点", "句子越长越好", "尽量使用生僻词"] if not phonics_focus else ["元音", "标点", "中文意思"],
            "answer": "清楚、简洁、有重点" if not phonics_focus else "元音",
            "explanation": "高质量表达先追求结构清楚，再追求自然。" if not phonics_focus else "先记住：元音通常是一个音节的中心。",
            "related_knowledge_id": content_route_item.get("knowledge_id"),
            "related_word_ids": [],
            "error_tag": "output_clarity" if not phonics_focus else "syllable_awareness",
        },
    ]
    objectives = [str(item) for item in content_route_item.get("objectives") or []] or [
        f"认识 {focus_text} 的声音特点",
        f"能读出 {', '.join(item['word'] for item in vocabulary) or '复习词'}",
        f"能完成“{passage_label}”短对话跟读",
        f"完成 {len(questions)} 道测试题",
    ]
    theme = str(content_route_item.get("theme") or f"{route_label}：{focus_text}")
    return {
        "theme": theme,
        "human_readable_text": str(
            content_route_item.get("human_readable_text")
            or f"今天用 30 分钟学习 {route_label}，重点是 {focus_text}。{review_text}"
        ),
        "objectives": objectives,
        "sections": [
            {"type": "preview", "title": "今日目标", "content": str(content_route_item.get("preview") or f"今天只集中练习 {focus_text}，先听清，再读顺。")},
            {"type": "phonics" if phonics_focus else "language_focus", "title": route_label, "content": focus_section_content},
            {"type": "system_knowledge", "title": "知识讲解", "content": "\n".join(content_lines)},
            {"type": "summary_prompt", "title": "今日总结", "content": f"完成后回忆：今天的重点是不是 {focus_text}？"},
        ],
        "vocabulary": vocabulary,
        "passage": passage,
        "knowledge_note": {
            "title": str(content_route_item.get("knowledge_title") or theme),
            "content": "\n".join(content_lines),
        },
        "quiz": {"title": "今日小测试", "questions": questions},
        "progress_summary": {
            "route_module_label": route_label,
            "main_knowledge_label": str(content_route_item.get("main_knowledge_label") or focus_text),
            "passage_module_label": passage_label,
        },
        "route_content_basis": content_route_item,
        "teaching_knowledge_id": content_route_item.get("teaching_knowledge_id"),
    }


def asset_slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in text).strip("_") or "asset"


def ensure_word_image_asset(conn: sqlite3.Connection, item: dict[str, Any]) -> str | None:
    if not item.get("needs_image"):
        return item.get("image_url")
    word = str(item.get("word") or "").strip()
    if not word:
        return item.get("image_url")
    slug = asset_slug(word)
    WORD_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    image_path = WORD_IMAGE_DIR / f"{slug}.svg"
    image_url = f"/generated/word_images/{slug}.svg"
    if not image_path.exists():
        palette = [
            ("#58cc02", "#e8fbdc"),
            ("#1cb0f6", "#e8f7ff"),
            ("#ff9600", "#fff4df"),
            ("#ff4b4b", "#fff1f1"),
        ]
        primary, soft = palette[sum(ord(ch) for ch in word) % len(palette)]
        label = word[:1].upper()
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="{soft}"/>
  <circle cx="256" cy="236" r="142" fill="{primary}" opacity="0.95"/>
  <circle cx="206" cy="174" r="30" fill="#fff" opacity="0.35"/>
  <path d="M156 342c42 38 158 38 200 0" fill="none" stroke="#fff" stroke-width="24" stroke-linecap="round" opacity="0.9"/>
  <text x="256" y="286" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="154" font-weight="800" fill="#fff">{label}</text>
  <text x="256" y="424" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="700" fill="#1f2937">{word}</text>
</svg>
"""
        image_path.write_text(svg, encoding="utf-8")
    conn.execute(
        """
        INSERT OR IGNORE INTO asset_sources (
          asset_id, asset_type, local_path, source_name, license, generation_params_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            f"asset_word_image_{slug}",
            "image",
            path_for_record(image_path),
            "local_svg_generator",
            "original-local-generated",
            json.dumps({"word": word, "image_hint": item.get("image_hint")}, ensure_ascii=False),
        ),
    )
    item["image_url"] = image_url
    return image_url


def ensure_lesson_runtime_assets(conn: sqlite3.Connection, lesson_json: dict[str, Any]) -> dict[str, Any]:
    for item in lesson_json.get("vocabulary", []):
        ensure_word_image_asset(conn, item)
    if not lesson_json.get("completion_encouragement"):
        lesson_json["completion_encouragement"] = build_completion_encouragement(
            {"vocabulary": lesson_json.get("vocabulary", [])},
            lesson_json.get("lesson_date") or today_iso(),
        )
    if not lesson_json.get("home_encouragement"):
        lesson_json["home_encouragement"] = build_home_encouragement(lesson_json.get("lesson_date") or today_iso())
    if not lesson_json.get("progress_summary"):
        lesson_json["progress_summary"] = build_progress_summary(lesson_json)
    passage = lesson_json.get("passage") or {}
    if passage and not passage.get("lines"):
        english_lines = [line.strip() for line in str(passage.get("english_text") or "").splitlines() if line.strip()]
        chinese_lines = [line.strip() for line in str(passage.get("chinese_support") or "").splitlines() if line.strip()]
        parsed_chinese = [parse_dialogue_line(line) for line in chinese_lines]
        passage["lines"] = [
            {
                "role": parsed["role"],
                "text": parsed["text"],
                "translation": parsed_chinese[index]["text"] if index < len(parsed_chinese) else None,
            }
            for index, parsed in enumerate(parse_dialogue_line(line) for line in english_lines)
        ]
    elif passage and passage.get("lines"):
        english_lines = [line.strip() for line in str(passage.get("english_text") or "").splitlines() if line.strip()]
        parsed_english = [parse_dialogue_line(line) for line in english_lines]
        for index, line in enumerate(passage["lines"]):
            if not isinstance(line, dict):
                continue
            if not line.get("role") and index < len(parsed_english):
                line["role"] = parsed_english[index]["role"]
            if line.get("text"):
                line["text"] = parse_dialogue_line(str(line["text"]))["text"]
            if line.get("translation"):
                line["translation"] = parse_dialogue_line(str(line["translation"]))["text"]
    if passage and not passage.get("difficult_words"):
        passage["difficult_words"] = [
            {"word": "the", "meaning": "这个；那个"},
            {"word": "on", "meaning": "在……上"},
        ]
    if passage.get("title"):
        passage["title"] = str(passage["title"]).replace("课堂对话：", "").replace("课堂对话:", "").rstrip(".。")
    note = lesson_json.get("knowledge_note") or {}
    if str(note.get("title") or "").startswith("系统知识"):
        note["title"] = str(note["title"]).replace("系统知识", "知识讲解", 1)
    return lesson_json


def build_progress_summary(lesson_json: dict[str, Any]) -> dict[str, str]:
    route_basis = lesson_json.get("route_basis") or {}
    theme = str(lesson_json.get("theme") or "")
    objectives = " ".join(str(item) for item in lesson_json.get("objectives", []))
    text = f"{theme} {objectives}"
    match = re.search(r"/[^/]+/\s*和\s*/[^/]+/", text)
    passage = lesson_json.get("passage") or {}
    passage_title = str(passage.get("title") or "")
    if "bank" in passage_title.lower() or "银行" in passage_title:
        passage_label = "银行对话"
    elif "hello" in passage_title.lower() or "见面" in passage_title or "问候" in passage_title:
        passage_label = "日常问候"
    else:
        passage_label = "日常对话"
    return {
        "route_module_label": str(route_basis.get("knowledge_name") or "音标和音节入门"),
        "main_knowledge_label": (match.group(0) if match else str((lesson_json.get("objectives") or ["今日知识点"])[0])),
        "passage_module_label": passage_label,
    }


def build_route_progress_summary(route_item: dict[str, Any]) -> dict[str, str]:
    route_label = str(route_item.get("knowledge_name") or route_item.get("theme") or "学习模块")
    source_text = " ".join(
        str(route_item.get(key) or "")
        for key in (
            "main_knowledge_label",
            "scenario_goal",
            "vocabulary_scope",
            "sentence_scope",
            "objective",
            "knowledge_description",
            "knowledge_name",
        )
    )
    if route_item.get("main_knowledge_label"):
        knowledge_label = str(route_item["main_knowledge_label"])
    else:
        match = re.search(r"/[^/]+/\s*和\s*/[^/]+/", source_text)
        if match:
            knowledge_label = match.group(0)
        elif route_item.get("sentence_scope") and "音标" not in str(route_item.get("sentence_scope")):
            knowledge_label = str(route_item["sentence_scope"])
        elif route_item.get("vocabulary_scope"):
            words = [
                item.strip()
                for item in str(route_item["vocabulary_scope"]).split(",")
                if item.strip()
            ]
            knowledge_label = " / ".join(words[:3]) if words else route_label
        else:
            knowledge_label = str(route_item.get("objective") or route_label)

    scenario_name = str(route_item.get("passage_module_label") or route_item.get("scenario_name") or "")
    if scenario_name == "音标拼读":
        passage_label = "日常对话"
    else:
        passage_label = scenario_name or "日常对话"
    return {
        "route_module_label": route_label,
        "main_knowledge_label": knowledge_label,
        "passage_module_label": passage_label,
    }


def parse_dialogue_line(line: str) -> dict[str, str | None]:
    if ":" in line:
        role, text = line.split(":", 1)
        return {"role": role.strip() or None, "text": text.strip()}
    if "：" in line:
        role, text = line.split("：", 1)
        return {"role": role.strip() or None, "text": text.strip()}
    return {"role": None, "text": line.strip()}


def log_debug(
    conn: sqlite3.Connection,
    module: str,
    level: str,
    message: str,
    detail: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        "INSERT INTO debug_events (event_id, module, level, message, detail_json) VALUES (?, ?, ?, ?, ?)",
        (new_id("debug"), module, level, message, json.dumps(detail or {}, ensure_ascii=False)),
    )


def log_admin_adjustment(
    conn: sqlite3.Connection,
    admin_id: str,
    target_type: str,
    target_id: str,
    action: str,
    detail: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO admin_adjustments (
          adjustment_id, admin_id, target_type, target_id, action, detail_json
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("adj"),
            admin_id,
            target_type,
            target_id,
            action,
            json.dumps(detail or {}, ensure_ascii=False),
        ),
    )


def get_admin_note(
    conn: sqlite3.Connection,
    user_id: str,
    target_type: str,
    target_id: str,
) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT admin_note, admin_instruction, admin_revision_note
        FROM admin_notes
        WHERE user_id = ? AND target_type = ? AND target_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, target_type, target_id),
    ).fetchone()
    if not row:
        return {"admin_note": None, "admin_instruction": None, "admin_revision_note": None}
    return {
        "admin_note": row["admin_note"],
        "admin_instruction": row["admin_instruction"],
        "admin_revision_note": row["admin_revision_note"],
    }


def build_generation_context(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    profile = row_to_dict(
        conn.execute("SELECT * FROM learning_profiles WHERE user_id = ?", (user_id,)).fetchone()
    )
    status = row_to_dict(
        conn.execute("SELECT * FROM learning_status WHERE user_id = ?", (user_id,)).fetchone()
    )
    route = rows_to_dicts(
        conn.execute(
            """
            SELECT
              cri.*,
              kp.name AS knowledge_name,
              kp.category AS knowledge_category,
              sm.scenario_id,
              sm.name AS scenario_name,
              sm.priority AS scenario_priority,
              sl.level_code,
              COALESCE(ukp.status, 'not_started') AS knowledge_status,
              COALESCE(ukp.mastery_score, 0) AS knowledge_mastery_score,
              COALESCE(usp.status, 'not_started') AS scenario_status
            FROM curriculum_route_items cri
            LEFT JOIN knowledge_points kp ON kp.knowledge_id = cri.knowledge_id
            LEFT JOIN scenario_levels sl ON sl.scenario_level_id = cri.scenario_level_id
            LEFT JOIN scenario_modules sm ON sm.scenario_id = sl.scenario_id
            LEFT JOIN user_knowledge_progress ukp
              ON ukp.user_id = ? AND ukp.knowledge_id = cri.knowledge_id
            LEFT JOIN user_scenario_progress usp
              ON usp.user_id = ? AND usp.scenario_id = sm.scenario_id
            ORDER BY cri.recommended_order
            """,
            (user_id, user_id),
        ).fetchall()
    )
    review_items = rows_to_dicts(
        conn.execute(
            """
            SELECT *
            FROM review_queue
            WHERE user_id = ? AND status = 'pending'
            ORDER BY priority DESC, created_at DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()
    )
    recent_errors = rows_to_dicts(
        conn.execute(
            """
            SELECT item_type, item_id, error_type, context, next_review_plan, created_at
            FROM error_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()
    )
    recent_difficulties = rows_to_dicts(
        conn.execute(
            """
            SELECT module_type, description, system_label, admin_label, created_at
            FROM difficulty_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 8
            """,
            (user_id,),
        ).fetchall()
    )
    route_item_for_context = choose_next_route_item({"route": route})
    teaching_knowledge = get_teaching_knowledge_asset(
        conn,
        route_item_for_context.get("knowledge_id"),
    )
    return {
        "user_id": user_id,
        "profile": profile,
        "status": status,
        "route": route,
        "review_queue": review_items,
        "recent_errors": recent_errors,
        "recent_difficulties": recent_difficulties,
        "teaching_knowledge": teaching_knowledge,
    }


def authenticate_local_account(login_account: str, password: str, remember: bool = True) -> dict[str, Any]:
    init_db()
    password_sha256 = hashlib.sha256(password.encode("utf-8")).hexdigest()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT la.username, la.user_id, la.role, la.status, COALESCE(u.nickname, au.nickname) AS nickname
            FROM local_login_accounts la
            LEFT JOIN users u ON u.user_id = la.user_id
            LEFT JOIN admin_users au ON au.admin_id = la.username
            WHERE la.username = ? AND la.password_sha256 = ? AND la.status = 'active'
            """,
            (login_account, password_sha256),
        ).fetchone()
        if not row:
            log_debug(conn, "auth", "warn", "local login failed", {"login_account": login_account})
            conn.commit()
            raise ValueError("账号或密码不正确")
        conn.execute(
            """
            UPDATE local_login_accounts
            SET remember_enabled = ?, last_login_at = CURRENT_TIMESTAMP
            WHERE username = ?
            """,
            (int(remember), login_account),
        )
        log_debug(
            conn,
            "auth",
            "info",
            "local login succeeded",
            {"login_account": login_account, "user_id": row["user_id"]},
        )
        session_token = secrets.token_urlsafe(32)
        expires_at = (datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS)).isoformat(timespec="seconds") + "Z"
        conn.execute(
            """
            INSERT INTO local_auth_sessions (
              session_token, login_account, role, expires_at
            ) VALUES (?, ?, ?, ?)
            """,
            (session_token, row["username"], row["role"], expires_at),
        )
        conn.execute(
            """
            UPDATE local_auth_sessions
            SET revoked_at = CURRENT_TIMESTAMP
            WHERE login_account = ?
              AND session_token <> ?
              AND revoked_at IS NULL
              AND expires_at < ?
            """,
            (row["username"], session_token, datetime.utcnow().isoformat(timespec="seconds") + "Z"),
        )
        conn.commit()
        display_username = row["nickname"] or row["username"]
        return {
            "login_account": row["username"],
            "username": display_username,
            "user_id": row["user_id"],
            "role": row["role"],
            "nickname": display_username,
            "remember": remember,
            "session_token": session_token,
            "expires_at": expires_at,
        }


def verify_local_session(session_token: str, required_role: str | None = None) -> dict[str, Any]:
    if not session_token:
        raise ValueError("missing session token")
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT
              las.session_token,
              las.login_account,
              la.user_id,
              las.role,
              las.expires_at,
              la.status AS account_status
            FROM local_auth_sessions las
            JOIN local_login_accounts la ON la.username = las.login_account
            WHERE las.session_token = ? AND las.revoked_at IS NULL
            """,
            (session_token,),
        ).fetchone()
        if not row or row["account_status"] != "active":
            raise ValueError("invalid session token")
        expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
        if expires_at <= datetime.now(expires_at.tzinfo):
            raise ValueError("expired session token")
        if required_role and row["role"] != required_role:
            raise PermissionError("insufficient role")
        return dict(row)


def verify_admin_session(session_token: str) -> dict[str, Any]:
    return verify_local_session(session_token, "admin")


def get_teaching_knowledge_asset(conn: sqlite3.Connection, knowledge_id: str | None) -> dict[str, Any] | None:
    if not knowledge_id:
        return None
    row = conn.execute(
        """
        SELECT *
        FROM teaching_knowledge_assets
        WHERE knowledge_id = ? AND status = 'active'
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (knowledge_id,),
    ).fetchone()
    if not row:
        return None
    asset = dict(row)
    asset["content"] = safe_json_loads(asset.get("content_json"), {})
    return asset


def choose_next_route_item(context: dict[str, Any]) -> dict[str, Any]:
    route = context.get("route") or []
    for item in route:
        if item.get("knowledge_status") not in {"mastered", "completed"}:
            return item
        if item.get("scenario_status") not in {"mastered", "completed"}:
            return item
    return route[-1] if route else {}


def build_home_encouragement(lesson_date: str) -> dict[str, str]:
    quotes = [
        {
            "quote_en": "The journey of a thousand miles begins with one step.",
            "quote_zh": "千里之行，始于足下。",
        },
        {
            "quote_en": "Well begun is half done.",
            "quote_zh": "好的开始，就是成功的一半。",
        },
        {
            "quote_en": "Learning never exhausts the mind.",
            "quote_zh": "学习永远不会使心灵枯竭。",
        },
        {
            "quote_en": "Where there is a will, there is a way.",
            "quote_zh": "有志者，事竟成。",
        },
    ]
    try:
        index = date.fromisoformat(lesson_date).toordinal() % len(quotes)
    except ValueError:
        index = 0
    return quotes[index]


def build_completion_encouragement(template: dict[str, Any], lesson_date: str) -> dict[str, Any]:
    vocabulary = template.get("vocabulary") or []
    learned_word = (vocabulary[0] or {}).get("word") if vocabulary else "English"
    button_options = ["我真行", "真棒", "继续保持"]
    try:
        button_text = button_options[date.fromisoformat(lesson_date).toordinal() % len(button_options)]
    except ValueError:
        button_text = button_options[0]
    return {
        "learned_word": learned_word,
        "message_zh": f"今天你已经认识了 {learned_word}，这就是稳稳的一步。",
        "quote_en": "It always seems impossible until it's done.",
        "quote_zh": "在事情完成之前，一切都看似不可能。",
        "quote_author": "Nelson Mandela",
        "button_text": button_text,
    }


def build_template_plan(
    user_id: str,
    lesson_date: str,
    context: dict[str, Any],
    admin: dict[str, Any],
) -> dict[str, Any]:
    route_item = choose_next_route_item(context)
    route_id = route_item.get("route_item_id", "route_001")
    review_words = []
    seen_review_words = set()
    for item in context.get("review_queue", []):
        if item.get("item_type") != "word":
            continue
        word = item["item_id"].replace("word_", "")
        if word in seen_review_words:
            continue
        seen_review_words.add(word)
        review_words.append(word)
    review_text = f" 同时复习：{', '.join(review_words[:3])}。" if review_words else ""

    templates: dict[str, dict[str, Any]] = {
        "route_000": {
            "theme": "音标第一课：/iː/ 和 /ɪ/",
            "human_readable_text": "今天用 30 分钟学习第一组音标：长音 /iː/ 和短音 /ɪ/，理解音标、音节和单词拼读的关系。",
            "objectives": [
                "认识 /iː/ 和 /ɪ/ 的发音差别",
                "理解一个音节里元音是核心声音",
                "能读出 see /siː/、sit /sɪt/、seat /siːt/",
                "完成 4 道音标和课文测试题",
            ],
            "sections": [
                {
                    "type": "preview",
                    "title": "今日目标",
                    "content": "今天不急着背很多句子，只先把两个常见元音听清、读准。",
                },
                {
                    "type": "phonics",
                    "title": "音标和音节",
                    "content": "音标是发音的标记。音节是单词里一小段可以读出来的声音，元音通常是音节的中心。今天先听 /iː/ 和 /ɪ/ 的长短区别。",
                },
                {
                    "type": "system_knowledge",
                    "title": "知识讲解：长短元音",
                    "content": "/iː/ 是长音，嘴角向两边拉，声音拉长，例如 see /siː/。/ɪ/ 是短音，嘴巴放松，声音短促，例如 sit /sɪt/。读单词时先找元音，再把前后的辅音接上。",
                },
                {
                    "type": "summary_prompt",
                    "title": "今日总结",
                    "content": "完成后回忆：/iː/ 是长音还是短音？sit 里是哪一个音？",
                },
            ],
            "vocabulary": [
                {
                    "word": "see",
                    "phonetic": "/siː/",
                    "part_of_speech": "verb",
                    "meaning": "看见",
                    "needs_image": True,
                    "image_hint": "eyes seeing something",
                },
                {
                    "word": "sit",
                    "phonetic": "/sɪt/",
                    "part_of_speech": "verb",
                    "meaning": "坐",
                    "needs_image": True,
                    "image_hint": "sitting on a chair",
                },
                {
                    "word": "seat",
                    "phonetic": "/siːt/",
                    "part_of_speech": "noun",
                    "meaning": "座位",
                    "needs_image": True,
                    "image_hint": "a seat",
                },
                {
                    "word": "it",
                    "phonetic": "/ɪt/",
                    "part_of_speech": "pronoun",
                    "meaning": "它",
                    "needs_image": False,
                },
            ],
            "passage": {
                "title": "I see it",
                "english_text": "Teacher: See the seat.\nVi: I see it.\nTeacher: Sit on the seat.\nVi: I sit.",
                "chinese_support": "老师：看这个座位。\nVi：我看见了。\n老师：坐在座位上。\nVi：我坐下。",
                "lines": [
                    {"role": "Teacher", "text": "See the seat.", "translation": "看这个座位。"},
                    {"role": "Vi", "text": "I see it.", "translation": "我看见了。"},
                    {"role": "Teacher", "text": "Sit on the seat.", "translation": "坐在座位上。"},
                    {"role": "Vi", "text": "I sit.", "translation": "我坐下。"},
                ],
                "difficult_words": [
                    {"word": "the", "meaning": "这个；那个"},
                    {"word": "on", "meaning": "在……上"},
                ],
            },
            "knowledge_note": {
                "title": "知识讲解：音标、音节和拼读",
                "content": "1. 音标告诉我们怎么发音，不等于英文字母。\n2. 一个音节通常有一个核心元音。\n3. /iː/ 要拉长，像 see、seat；/ɪ/ 要短促，像 sit、it。\n4. 拼读时先读元音，再接前后的辅音：s + /iː/ = see，s + /ɪ/ + t = sit。",
            },
            "quiz": {
                "title": "音标小测试",
                "questions": [
                    {
                        "prompt": "/iː/ 是什么声音？",
                        "options": ["长音", "短音", "不发音"],
                        "answer": "长音",
                        "explanation": "/iː/ 后面的 ː 表示声音要拉长。",
                    },
                    {
                        "prompt": "sit /sɪt/ 里面的元音是？",
                        "options": ["/iː/", "/ɪ/", "/e/"],
                        "answer": "/ɪ/",
                        "explanation": "sit 的中间是短促的 /ɪ/。",
                    },
                    {
                        "prompt": "see /siː/ 的意思是？",
                        "options": ["看见", "坐", "座位"],
                        "answer": "看见",
                        "explanation": "see 是动词，核心意思是看见。",
                    },
                    {
                        "prompt": "音节里通常最核心的声音是？",
                        "options": ["元音", "标点", "中文意思"],
                        "answer": "元音",
                        "explanation": "今天先记住：元音通常是一个音节的中心。",
                    },
                ],
            },
            "teaching_knowledge_id": "kb_phonics_001_i_long_i_short",
        },
        "route_001": {
            "theme": "基础问候：第一次见面",
            "human_readable_text": f"今天用 15 分钟学习英语基础问候：hello、nice、meet，并学会 Nice to meet you。{review_text}",
            "objectives": ["认识 hello / nice / meet", "理解 Nice to meet you", "完成 3 道入门测试题"],
            "sections": [
                {
                    "type": "preview",
                    "title": "今日前瞻",
                    "content": "今天只学会一件事：见面时能说你好和很高兴见到你。",
                },
                {
                    "type": "knowledge",
                    "title": "知识讲解",
                    "content": "Nice to meet you 表示“很高兴见到你”。先整体记住，不拆复杂语法。",
                },
                {
                    "type": "summary_prompt",
                    "title": "今日总结",
                    "content": "完成后回忆：hello 是什么？meet 是什么？",
                },
            ],
            "vocabulary": [
                {
                    "word": "hello",
                    "phonetic": "/həˈloʊ/",
                    "part_of_speech": "interjection",
                    "meaning": "你好",
                    "needs_image": False,
                },
                {
                    "word": "nice",
                    "phonetic": "/naɪs/",
                    "part_of_speech": "adjective",
                    "meaning": "好的；令人愉快的",
                    "needs_image": False,
                },
                {
                    "word": "meet",
                    "phonetic": "/miːt/",
                    "part_of_speech": "verb",
                    "meaning": "遇见",
                    "needs_image": True,
                    "image_hint": "two people meeting",
                },
            ],
            "passage": {
                "title": "第一次见面",
                "english_text": "Hello. I am Momo. Nice to meet you.",
                "chinese_support": "你好。我是 Momo。很高兴见到你。",
            },
            "knowledge_note": {
                "title": "Nice to meet you",
                "content": "这是一句固定表达，见到别人时可以直接说。",
            },
            "quiz": {
                "title": "今日小测试",
                "questions": [
                    {
                        "prompt": "hello 的意思是？",
                        "options": ["你好", "谢谢", "再见"],
                        "answer": "你好",
                        "explanation": "hello 是最常见的问候。",
                    },
                    {
                        "prompt": "meet 的核心意思是？",
                        "options": ["学习", "遇见", "购买"],
                        "answer": "遇见",
                        "explanation": "meet 是动词，表示遇见。",
                    },
                    {
                        "prompt": "Nice to meet you. 可以怎么理解？",
                        "options": ["很高兴见到你", "我想喝水", "明天见"],
                        "answer": "很高兴见到你",
                        "explanation": "这是第一次见面常用表达。",
                    },
                ],
            },
        },
        "route_002": {
            "theme": "自我介绍：I am",
            "human_readable_text": f"今天学习 I am 句型，用一句话介绍自己。{review_text}",
            "objectives": ["认识 I / am / banker", "会说 I am Momo", "完成 3 道自我介绍测试"],
            "sections": [
                {
                    "type": "preview",
                    "title": "今日前瞻",
                    "content": "今天把“我是……”这句话学会，工作和生活里都能用。",
                },
                {
                    "type": "knowledge",
                    "title": "知识讲解",
                    "content": "I am 表示“我是”。后面可以接名字、身份或职业。",
                },
                {
                    "type": "summary_prompt",
                    "title": "今日总结",
                    "content": "完成后试着说：I am Momo. I am a banker.",
                },
            ],
            "vocabulary": [
                {
                    "word": "I",
                    "phonetic": "/aɪ/",
                    "part_of_speech": "pronoun",
                    "meaning": "我",
                    "needs_image": False,
                },
                {
                    "word": "am",
                    "phonetic": "/æm/",
                    "part_of_speech": "verb",
                    "meaning": "是",
                    "needs_image": True,
                    "image_hint": "simple self introduction",
                },
                {
                    "word": "banker",
                    "phonetic": "/ˈbæŋkər/",
                    "part_of_speech": "noun",
                    "meaning": "银行从业者",
                    "needs_image": True,
                    "image_hint": "bank professional",
                },
            ],
            "passage": {
                "title": "一句自我介绍",
                "english_text": "Hello. I am Momo. I am a banker.",
                "chinese_support": "你好。我是 Momo。我是银行从业者。",
            },
            "knowledge_note": {
                "title": "I am",
                "content": "I am 是最基础的自我介绍句型。先记整句，不需要展开语法。",
            },
            "quiz": {
                "title": "今日小测试",
                "questions": [
                    {
                        "prompt": "I 的意思是？",
                        "options": ["我", "你", "他"],
                        "answer": "我",
                        "explanation": "I 表示“我”。",
                    },
                    {
                        "prompt": "I am Momo. 的意思是？",
                        "options": ["我是 Momo", "我见到 Momo", "Momo 再见"],
                        "answer": "我是 Momo",
                        "explanation": "I am 表示“我是”。",
                    },
                    {
                        "prompt": "banker 的核心意思是？",
                        "options": ["医生", "银行从业者", "老师"],
                        "answer": "银行从业者",
                        "explanation": "banker 是名词，表示银行从业者。",
                    },
                ],
            },
        },
        "route_003": {
            "theme": "银行接待：Welcome",
            "human_readable_text": f"今天学习银行接待里的第一句 Welcome，并认识 bank 和 help。{review_text}",
            "objectives": ["认识 welcome / bank / help", "理解 How can I help?", "完成 3 道银行场景测试"],
            "sections": [
                {
                    "type": "preview",
                    "title": "今日前瞻",
                    "content": "今天进入一点银行场景，只学一句接待开场白。",
                },
                {
                    "type": "knowledge",
                    "title": "知识讲解",
                    "content": "How can I help? 表示“我能帮您什么？”，是服务场景常见表达。",
                },
                {
                    "type": "summary_prompt",
                    "title": "今日总结",
                    "content": "完成后回忆：welcome、bank、help 分别是什么意思？",
                },
            ],
            "vocabulary": [
                {
                    "word": "welcome",
                    "phonetic": "/ˈwelkəm/",
                    "part_of_speech": "verb",
                    "meaning": "欢迎",
                    "needs_image": True,
                    "image_hint": "welcoming a customer",
                },
                {
                    "word": "bank",
                    "phonetic": "/bæŋk/",
                    "part_of_speech": "noun",
                    "meaning": "银行",
                    "needs_image": True,
                    "image_hint": "bank counter",
                },
                {
                    "word": "help",
                    "phonetic": "/help/",
                    "part_of_speech": "verb",
                    "meaning": "帮助",
                    "needs_image": True,
                    "image_hint": "helping a customer",
                },
            ],
            "passage": {
                "title": "银行接待开场",
                "english_text": "Welcome to the bank. How can I help?",
                "chinese_support": "欢迎来到银行。我能帮您什么？",
            },
            "knowledge_note": {
                "title": "How can I help?",
                "content": "这是服务场景里很常用的一句话，先作为固定表达记住。",
            },
            "quiz": {
                "title": "今日小测试",
                "questions": [
                    {
                        "prompt": "bank 的意思是？",
                        "options": ["银行", "会议", "家庭"],
                        "answer": "银行",
                        "explanation": "bank 是名词，表示银行。",
                    },
                    {
                        "prompt": "help 的核心意思是？",
                        "options": ["帮助", "购买", "离开"],
                        "answer": "帮助",
                        "explanation": "help 是动词，表示帮助。",
                    },
                    {
                        "prompt": "How can I help? 可以怎么理解？",
                        "options": ["我能帮您什么？", "我今天休息", "我来自银行"],
                        "answer": "我能帮您什么？",
                        "explanation": "这是接待客户时的常用表达。",
                    },
                ],
            },
        },
    }

    content_route_item = pick_content_route_item(context)
    template = (
        build_kb_route_template(content_route_item, review_text)
        if content_route_item
        else templates.get(route_id, templates["route_001"])
    )
    template = {
        **template,
        "completion_encouragement": build_completion_encouragement(template, lesson_date),
        "home_encouragement": build_home_encouragement(lesson_date),
    }
    audio_assets = build_kb_audio_assets(template)
    estimated_minutes = (
        content_route_item.get("target_minutes")
        or (context.get("profile") or {}).get("daily_minutes")
        or route_item.get("target_minutes")
        or 30
    )
    route_module_label = content_route_item.get("route_module_label") or route_item.get("knowledge_name")
    main_knowledge_label = content_route_item.get("main_knowledge_label")
    passage_module_label = content_route_item.get("passage_module_label")
    plan = {
        "schema_version": "lesson_plan_json.v1",
        "user_id": user_id,
        "lesson_date": lesson_date,
        "provider": "template_provider",
        "admin_note": admin["admin_note"],
        "admin_instruction": admin["admin_instruction"],
        "admin_revision_note": admin["admin_revision_note"],
        "difficulty": content_route_item.get("difficulty") or "starter",
        "estimated_minutes": estimated_minutes,
        "route_basis": {
            "current_stage": (context.get("status") or {}).get("current_stage"),
            "route_item_id": route_item.get("route_item_id"),
            "knowledge_id": route_item.get("knowledge_id"),
            "knowledge_name": route_module_label,
            "scenario_level_id": route_item.get("scenario_level_id"),
            "scenario_id": route_item.get("scenario_id"),
            "scenario_name": passage_module_label or route_item.get("scenario_name"),
            "level_code": content_route_item.get("level_code") or route_item.get("level_code"),
            "review_items": review_words[:3],
            "teaching_knowledge_id": template.get("teaching_knowledge_id"),
            "content_route_item_id": content_route_item.get("route_item_id"),
            "content_route_day": content_route_item.get("day_number"),
            "content_route_schema_version": content_route_item.get("route_schema_version"),
            "main_knowledge_label": main_knowledge_label,
            "passage_module_label": passage_module_label,
            "source_basis": content_route_item.get("source_basis") or [],
        },
        "asset_requirements": [
            {"type": "image", "target": item["word"], "required": True}
            for item in template["vocabulary"]
            if item.get("needs_image")
        ] + [{"type": "audio", "target": item["target_ref"], "required": False} for item in audio_assets],
        "audio_assets": audio_assets,
        **template,
    }
    plan["progress_summary"] = template.get("progress_summary") or build_progress_summary(
        {
            **plan,
            "route_basis": plan["route_basis"],
            "passage": plan.get("passage"),
        }
    )
    return plan


def generate_lesson_plan_json(
    user_id: str,
    lesson_date: str | None = None,
    admin_override: dict[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    lesson_date = lesson_date or today_iso()
    start = time.perf_counter()
    with connect() as conn:
        context = build_generation_context(conn, user_id)
        admin = get_admin_note(conn, user_id, "lesson_plan", lesson_date)
        if admin_override:
            admin = {**admin, **admin_override}
        run_id = new_id("gen")
        plan = build_template_plan(user_id, lesson_date, context, admin)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_DIR / f"{user_id}_{lesson_date}_lesson_plan.json"
        raw_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        duration_ms = int((time.perf_counter() - start) * 1000)
        input_summary = {
            "user_id": user_id,
            "lesson_date": lesson_date,
            "profile": context.get("profile"),
            "status": context.get("status"),
            "route_item": choose_next_route_item(context),
            "content_route_item": pick_content_route_item(context),
            "review_queue": context.get("review_queue"),
            "recent_errors": context.get("recent_errors"),
            "recent_difficulties": context.get("recent_difficulties"),
            "admin": admin,
        }
        conn.execute(
            """
            INSERT OR REPLACE INTO content_generation_runs (
              generation_run_id, task_type, provider, model_or_template, template_version,
              input_summary, output_path, status, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                "lesson_plan",
                "template_provider",
                "starter_lesson_plan_template",
                "1.1.0",
                json.dumps(input_summary, ensure_ascii=False),
                path_for_record(raw_path),
                "success",
                duration_ms,
            ),
        )
        log_debug(conn, "generation", "info", "lesson_plan_json generated", {"run_id": run_id})
        conn.commit()
        return run_id, plan


def normalize_lesson_plan(run_id: str, plan: dict[str, Any]) -> dict[str, Any]:
    required = ["schema_version", "user_id", "lesson_date", "theme", "objectives", "sections", "vocabulary", "quiz"]
    missing = [key for key in required if key not in plan]
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    lesson_asset_id = f"lesson_{plan['user_id']}_{plan['lesson_date'].replace('-', '')}_v1"
    lesson_json = {
        "schema_version": "lesson_json.v1",
        "lesson_asset_id": lesson_asset_id,
        "source_generation_run_id": run_id,
        "user_id": plan["user_id"],
        "lesson_date": plan["lesson_date"],
        "theme": plan["theme"],
        "human_readable_summary": plan["human_readable_text"],
        "admin_note": plan.get("admin_note"),
        "admin_instruction": plan.get("admin_instruction"),
        "admin_revision_note": plan.get("admin_revision_note"),
        "objectives": plan["objectives"],
        "difficulty": plan.get("difficulty", "starter"),
        "estimated_minutes": plan.get("estimated_minutes", 15),
        "route_basis": plan.get("route_basis", {}),
        "sections": plan["sections"],
        "vocabulary": plan["vocabulary"],
        "passage": plan.get("passage"),
        "knowledge_note": plan.get("knowledge_note"),
        "quiz": plan["quiz"],
        "completion_encouragement": plan.get("completion_encouragement"),
        "home_encouragement": plan.get("home_encouragement"),
        "progress_summary": plan.get("progress_summary"),
        "asset_requirements": plan.get("asset_requirements", []),
        "audio_assets": plan.get("audio_assets", []),
        "teaching_knowledge_id": plan.get("teaching_knowledge_id"),
        "source_basis": (plan.get("route_basis") or {}).get("source_basis", []),
    }
    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = NORMALIZED_DIR / f"{lesson_asset_id}.json"
    out_path.write_text(json.dumps(lesson_json, ensure_ascii=False, indent=2), encoding="utf-8")
    return lesson_json


def draft_id_for(user_id: str, lesson_date: str) -> str:
    return f"draft_{user_id}_{lesson_date.replace('-', '')}"


def parse_lesson_draft(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if not row:
        return None
    draft = dict(row)
    draft["draft_json"] = safe_json_loads(draft.get("draft_json"), {})
    return draft


def snapshot_lesson_draft(
    conn: sqlite3.Connection,
    draft_id: str,
    action: str,
    admin_id: str,
) -> None:
    current = conn.execute(
        "SELECT draft_json, admin_note, admin_instruction FROM lesson_draft_workspaces WHERE draft_id = ?",
        (draft_id,),
    ).fetchone()
    if not current:
        return
    conn.execute(
        """
        INSERT INTO lesson_draft_snapshots (
          snapshot_id, draft_id, action, admin_id, draft_json, admin_note, admin_instruction
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("snap"),
            draft_id,
            action,
            admin_id,
            current["draft_json"],
            current["admin_note"],
            current["admin_instruction"],
        ),
    )


def save_lesson_draft_workspace(
    lesson_json: dict[str, Any],
    admin_id: str = "admin_xly",
    action: str = "save_draft",
    snapshot_existing: bool = True,
) -> str:
    user_id = lesson_json["user_id"]
    lesson_date = lesson_json["lesson_date"]
    draft_id = draft_id_for(user_id, lesson_date)
    text = json.dumps(lesson_json, ensure_ascii=False, sort_keys=True)
    with connect() as conn:
        if snapshot_existing:
            snapshot_lesson_draft(conn, draft_id, action, admin_id)
        conn.execute(
            """
            INSERT INTO lesson_draft_workspaces (
              draft_id, user_id, lesson_date, source_generation_run_id, status,
              validation_status, human_readable_summary, admin_note,
              admin_instruction, draft_json, publish_after, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(draft_id) DO UPDATE SET
              source_generation_run_id = excluded.source_generation_run_id,
              status = excluded.status,
              validation_status = excluded.validation_status,
              human_readable_summary = excluded.human_readable_summary,
              admin_note = excluded.admin_note,
              admin_instruction = excluded.admin_instruction,
              draft_json = excluded.draft_json,
              publish_after = excluded.publish_after,
              published_lesson_asset_id = NULL,
              updated_at = CURRENT_TIMESTAMP
            """,
            (
                draft_id,
                user_id,
                lesson_date,
                lesson_json.get("source_generation_run_id"),
                "pending_publish",
                "passed",
                lesson_json.get("human_readable_summary"),
                lesson_json.get("admin_note"),
                lesson_json.get("admin_instruction"),
                text,
                f"{lesson_date}T00:00:00+08:00",
            ),
        )
        log_admin_adjustment(
            conn,
            admin_id,
            "lesson_draft",
            draft_id,
            action,
            {
                "lesson_asset_id": lesson_json.get("lesson_asset_id"),
                "lesson_date": lesson_date,
                "source_generation_run_id": lesson_json.get("source_generation_run_id"),
            },
        )
        log_debug(conn, "lesson_draft", "info", "lesson draft workspace saved", {"draft_id": draft_id})
        conn.commit()
    return draft_id


def generate_lesson_draft_workspace(
    user_id: str = "user_mom",
    lesson_date: str | None = None,
    admin_instruction: str | None = None,
    admin_note: str | None = None,
    admin_id: str = "admin_xly",
    action: str = "generate_draft",
) -> str:
    lesson_date = lesson_date or today_iso()
    admin_override = {
        "admin_note": admin_note,
        "admin_instruction": admin_instruction,
        "admin_revision_note": None,
    }
    run_id, plan = generate_lesson_plan_json(user_id, lesson_date, admin_override)
    lesson_json = normalize_lesson_plan(run_id, plan)
    if admin_note is not None:
        lesson_json["admin_note"] = admin_note or None
    if admin_instruction is not None:
        lesson_json["admin_instruction"] = admin_instruction or None
    return save_lesson_draft_workspace(lesson_json, admin_id=admin_id, action=action)


def get_lesson_draft(draft_id: str) -> dict[str, Any] | None:
    init_db()
    with connect() as conn:
        return parse_lesson_draft(
            conn.execute("SELECT * FROM lesson_draft_workspaces WHERE draft_id = ?", (draft_id,)).fetchone()
        )


def get_latest_lesson_draft(user_id: str, lesson_date: str | None = None) -> dict[str, Any] | None:
    init_db()
    with connect() as conn:
        if lesson_date:
            row = conn.execute(
                """
                SELECT *
                FROM lesson_draft_workspaces
                WHERE user_id = ? AND lesson_date = ? AND status = 'pending_publish'
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (user_id, lesson_date),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT *
                FROM lesson_draft_workspaces
                WHERE user_id = ? AND status = 'pending_publish'
                ORDER BY lesson_date DESC, updated_at DESC
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()
        return parse_lesson_draft(row)


def update_lesson_draft_note(
    draft_id: str,
    admin_note: str | None,
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        draft = parse_lesson_draft(
            conn.execute("SELECT * FROM lesson_draft_workspaces WHERE draft_id = ?", (draft_id,)).fetchone()
        )
        if not draft:
            raise ValueError(f"lesson draft not found: {draft_id}")
        snapshot_lesson_draft(conn, draft_id, "update_admin_note", admin_id)
        lesson_json = draft["draft_json"]
        lesson_json["admin_note"] = admin_note or None
        text = json.dumps(lesson_json, ensure_ascii=False, sort_keys=True)
        conn.execute(
            """
            UPDATE lesson_draft_workspaces
            SET admin_note = ?, draft_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE draft_id = ?
            """,
            (admin_note or None, text, draft_id),
        )
        log_admin_adjustment(
            conn,
            admin_id,
            "lesson_draft",
            draft_id,
            "update_admin_note",
            {"admin_note": admin_note},
        )
        conn.commit()
    return get_lesson_draft(draft_id) or {}


def manually_update_lesson_draft(
    draft_id: str,
    lesson_json: dict[str, Any],
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    required = ["schema_version", "lesson_asset_id", "user_id", "lesson_date", "theme", "sections", "vocabulary", "quiz"]
    missing = [key for key in required if key not in lesson_json]
    if missing:
        raise ValueError(f"missing required fields: {missing}")
    with connect() as conn:
        current = conn.execute("SELECT * FROM lesson_draft_workspaces WHERE draft_id = ?", (draft_id,)).fetchone()
        if not current:
            raise ValueError(f"lesson draft not found: {draft_id}")
        snapshot_lesson_draft(conn, draft_id, "manual_save", admin_id)
        text = json.dumps(lesson_json, ensure_ascii=False, sort_keys=True)
        conn.execute(
            """
            UPDATE lesson_draft_workspaces
            SET
              user_id = ?,
              lesson_date = ?,
              source_generation_run_id = ?,
              human_readable_summary = ?,
              admin_note = ?,
              admin_instruction = ?,
              draft_json = ?,
              updated_at = CURRENT_TIMESTAMP
            WHERE draft_id = ?
            """,
            (
                lesson_json["user_id"],
                lesson_json["lesson_date"],
                lesson_json.get("source_generation_run_id"),
                lesson_json.get("human_readable_summary"),
                lesson_json.get("admin_note"),
                lesson_json.get("admin_instruction"),
                text,
                draft_id,
            ),
        )
        log_admin_adjustment(
            conn,
            admin_id,
            "lesson_draft",
            draft_id,
            "manual_save",
            {"lesson_asset_id": lesson_json.get("lesson_asset_id")},
        )
        conn.commit()
    return get_lesson_draft(draft_id) or {}


def regenerate_lesson_draft_from_instruction(
    draft_id: str,
    admin_instruction: str,
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    draft = get_lesson_draft(draft_id)
    if not draft:
        raise ValueError(f"lesson draft not found: {draft_id}")
    draft_id = generate_lesson_draft_workspace(
        user_id=draft["user_id"],
        lesson_date=draft["lesson_date"],
        admin_instruction=admin_instruction,
        admin_note=draft.get("admin_note"),
        admin_id=admin_id,
        action="ai_adjust",
    )
    return get_lesson_draft(draft_id) or {}


def undo_lesson_draft(draft_id: str, admin_id: str = "admin_xly") -> dict[str, Any]:
    init_db()
    with connect() as conn:
        snapshot = conn.execute(
            """
            SELECT *
            FROM lesson_draft_snapshots
            WHERE draft_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (draft_id,),
        ).fetchone()
        if not snapshot:
            raise ValueError("没有可还原的上一步")
        lesson_json = safe_json_loads(snapshot["draft_json"], {})
        conn.execute(
            """
            UPDATE lesson_draft_workspaces
            SET
              user_id = ?,
              lesson_date = ?,
              source_generation_run_id = ?,
              human_readable_summary = ?,
              admin_note = ?,
              admin_instruction = ?,
              draft_json = ?,
              updated_at = CURRENT_TIMESTAMP
            WHERE draft_id = ?
            """,
            (
                lesson_json.get("user_id"),
                lesson_json.get("lesson_date"),
                lesson_json.get("source_generation_run_id"),
                lesson_json.get("human_readable_summary"),
                snapshot["admin_note"],
                snapshot["admin_instruction"],
                snapshot["draft_json"],
                draft_id,
            ),
        )
        conn.execute("DELETE FROM lesson_draft_snapshots WHERE snapshot_id = ?", (snapshot["snapshot_id"],))
        log_admin_adjustment(
            conn,
            admin_id,
            "lesson_draft",
            draft_id,
            "undo",
            {"snapshot_id": snapshot["snapshot_id"], "snapshot_action": snapshot["action"]},
        )
        conn.commit()
    return get_lesson_draft(draft_id) or {}


def next_lesson_version_no(conn: sqlite3.Connection, lesson_asset_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(version_no), 0) + 1 AS next_no FROM lesson_json_versions WHERE lesson_asset_id = ?",
        (lesson_asset_id,),
    ).fetchone()
    return int(row["next_no"])


def derive_structured_lesson(conn: sqlite3.Connection, lesson_json: dict[str, Any]) -> None:
    lesson_asset_id = lesson_json["lesson_asset_id"]
    conn.execute("DELETE FROM lesson_sections WHERE lesson_asset_id = ?", (lesson_asset_id,))
    conn.execute("DELETE FROM lesson_vocabulary WHERE lesson_asset_id = ?", (lesson_asset_id,))
    conn.execute("DELETE FROM text_passages WHERE lesson_asset_id = ?", (lesson_asset_id,))
    conn.execute("DELETE FROM knowledge_notes WHERE lesson_asset_id = ?", (lesson_asset_id,))

    conn.execute(
        """
        INSERT INTO daily_plans (
          plan_id, lesson_asset_id, user_id, plan_date, theme, objective,
          estimated_minutes, difficulty, status, published_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(plan_id) DO UPDATE SET
          lesson_asset_id = excluded.lesson_asset_id,
          user_id = excluded.user_id,
          plan_date = excluded.plan_date,
          theme = excluded.theme,
          objective = excluded.objective,
          estimated_minutes = excluded.estimated_minutes,
          difficulty = excluded.difficulty,
          status = excluded.status,
          published_at = CURRENT_TIMESTAMP
        """,
        (
            f"plan_{lesson_asset_id}",
            lesson_asset_id,
            lesson_json["user_id"],
            lesson_json["lesson_date"],
            lesson_json["theme"],
            "；".join(lesson_json["objectives"]),
            lesson_json["estimated_minutes"],
            lesson_json["difficulty"],
            "published",
        ),
    )
    for idx, section in enumerate(lesson_json["sections"], start=1):
        conn.execute(
            """
            INSERT OR REPLACE INTO lesson_sections (
              section_id, lesson_asset_id, section_type, title, content, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                f"{lesson_asset_id}_sec_{idx}",
                lesson_asset_id,
                section["type"],
                section["title"],
                section.get("content"),
                idx,
            ),
        )
    for idx, item in enumerate(lesson_json["vocabulary"], start=1):
        ensure_word_image_asset(conn, item)
        word_id = f"word_{item['word'].lower()}"
        conn.execute(
            """
            INSERT INTO vocabulary_items (
              word_id, word, phonetic, part_of_speech, core_meaning, difficulty, needs_image
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(word_id) DO UPDATE SET
              word = excluded.word,
              phonetic = excluded.phonetic,
              part_of_speech = excluded.part_of_speech,
              core_meaning = excluded.core_meaning,
              difficulty = excluded.difficulty,
              needs_image = excluded.needs_image
            """,
            (
                word_id,
                item["word"],
                item.get("phonetic"),
                item.get("part_of_speech"),
                item.get("meaning"),
                lesson_json["difficulty"],
                int(bool(item.get("needs_image"))),
            ),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO lesson_vocabulary (
              lesson_asset_id, word_id, sort_order, example_sentence, audio_url, image_url
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (lesson_asset_id, word_id, idx, None, None, item.get("image_url")),
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO vocabulary_mastery (
              user_id, word_id, first_seen_date, mastery_status
            ) VALUES (?, ?, ?, ?)
            """,
            (lesson_json["user_id"], word_id, lesson_json["lesson_date"], "new"),
        )
    passage = lesson_json.get("passage") or {}
    conn.execute(
        """
        INSERT OR REPLACE INTO text_passages (
          passage_id, lesson_asset_id, title, english_text, chinese_support, difficulty, source_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            f"passage_{lesson_asset_id}",
            lesson_asset_id,
            passage.get("title"),
            passage.get("english_text"),
            passage.get("chinese_support"),
            lesson_json["difficulty"],
            "template_provider",
        ),
    )
    note = lesson_json.get("knowledge_note") or {}
    conn.execute(
        """
        INSERT OR REPLACE INTO knowledge_notes (
          note_id, lesson_asset_id, title, content, related_knowledge_id
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            f"note_{lesson_asset_id}",
            lesson_asset_id,
            note.get("title", "知识讲解"),
            note.get("content", ""),
            lesson_json.get("route_basis", {}).get("knowledge_id"),
        ),
    )
    quiz_id = f"quiz_{lesson_asset_id}"
    conn.execute(
        """
        INSERT INTO quizzes (
          quiz_id, lesson_asset_id, title, difficulty, pass_score
        ) VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(quiz_id) DO UPDATE SET
          lesson_asset_id = excluded.lesson_asset_id,
          title = excluded.title,
          difficulty = excluded.difficulty,
          pass_score = excluded.pass_score
        """,
        (
            quiz_id,
            lesson_asset_id,
            lesson_json.get("quiz", {}).get("title", "今日小测试"),
            lesson_json["difficulty"],
            0.8,
        ),
    )
    for idx, question in enumerate(lesson_json.get("quiz", {}).get("questions", []), start=1):
        conn.execute(
            """
            INSERT INTO quiz_questions (
              question_id, quiz_id, prompt, options_json, answer, explanation,
              related_word_id, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(question_id) DO UPDATE SET
              quiz_id = excluded.quiz_id,
              prompt = excluded.prompt,
              options_json = excluded.options_json,
              answer = excluded.answer,
              explanation = excluded.explanation,
              related_word_id = excluded.related_word_id,
              sort_order = excluded.sort_order
            """,
            (
                f"{quiz_id}_q_{idx}",
                quiz_id,
                question["prompt"],
                json.dumps(question["options"], ensure_ascii=False),
                question["answer"],
                question.get("explanation"),
                question.get("related_word_id"),
                idx,
            ),
        )


def save_lesson_json(
    lesson_json: dict[str, Any],
    status: str = "published",
    admin_id: str = "admin_xly",
    revision_reason: str = "generated",
) -> str:
    lesson_asset_id = lesson_json["lesson_asset_id"]
    with connect() as conn:
        ensure_lesson_runtime_assets(conn, lesson_json)
        text = json.dumps(lesson_json, ensure_ascii=False, sort_keys=True)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        previous = conn.execute(
            "SELECT lesson_json FROM lesson_json_assets WHERE lesson_asset_id = ?",
            (lesson_asset_id,),
        ).fetchone()
        published_at = datetime.now().isoformat(timespec="seconds") if status == "published" else None
        conn.execute(
            """
            INSERT INTO lesson_json_assets (
              lesson_asset_id, user_id, lesson_date, schema_version, source_provider,
              generation_run_id, status, validation_status, human_readable_summary,
              admin_note, content_hash, lesson_json, published_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(lesson_asset_id) DO UPDATE SET
              user_id = excluded.user_id,
              lesson_date = excluded.lesson_date,
              schema_version = excluded.schema_version,
              source_provider = excluded.source_provider,
              generation_run_id = excluded.generation_run_id,
              status = excluded.status,
              validation_status = excluded.validation_status,
              human_readable_summary = excluded.human_readable_summary,
              admin_note = excluded.admin_note,
              content_hash = excluded.content_hash,
              lesson_json = excluded.lesson_json,
              published_at = excluded.published_at
            """,
            (
                lesson_asset_id,
                lesson_json["user_id"],
                lesson_json["lesson_date"],
                lesson_json["schema_version"],
                "template_provider",
                lesson_json["source_generation_run_id"],
                status,
                "passed",
                lesson_json["human_readable_summary"],
                lesson_json.get("admin_note"),
                content_hash,
                text,
                published_at,
            ),
        )
        version_no = next_lesson_version_no(conn, lesson_asset_id)
        conn.execute(
            """
            INSERT INTO lesson_json_versions (
              version_id, lesson_asset_id, version_no, status, lesson_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (f"{lesson_asset_id}_ver_{version_no}", lesson_asset_id, version_no, status, text),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO lesson_json_validation_results (
              validation_id, lesson_asset_id, schema_version, status, warnings_json, errors_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id("val"), lesson_asset_id, lesson_json["schema_version"], "passed", "[]", "[]"),
        )
        if previous and previous["lesson_json"] != text:
            conn.execute(
                """
                INSERT INTO content_revisions (
                  revision_id, target_type, target_id, original_text, human_readable_text,
                  revised_text, admin_note, reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("rev"),
                    "lesson_json",
                    lesson_asset_id,
                    previous["lesson_json"],
                    lesson_json.get("human_readable_summary"),
                    text,
                    lesson_json.get("admin_note"),
                    revision_reason,
                ),
            )
        if status == "published":
            derive_structured_lesson(conn, lesson_json)
            VALIDATED_DIR.mkdir(parents=True, exist_ok=True)
            (VALIDATED_DIR / f"{lesson_asset_id}.json").write_text(
                json.dumps(lesson_json, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        log_admin_adjustment(
            conn,
            admin_id,
            "lesson_json",
            lesson_asset_id,
            f"save_{status}",
            {"reason": revision_reason, "content_hash": content_hash},
        )
        log_debug(
            conn,
            "lesson_json",
            "info",
            f"lesson_json saved as {status}",
            {"lesson_asset_id": lesson_asset_id},
        )
        conn.commit()
    return lesson_asset_id


def publish_lesson_draft_workspace(
    draft_id: str,
    admin_id: str = "admin_xly",
    reason: str = "publish_draft",
) -> dict[str, Any]:
    init_db()
    draft = get_lesson_draft(draft_id)
    if not draft:
        raise ValueError(f"lesson draft not found: {draft_id}")
    lesson_json = draft["draft_json"]
    lesson_asset_id = save_lesson_json(
        lesson_json,
        status="published",
        admin_id=admin_id,
        revision_reason=reason,
    )
    with connect() as conn:
        conn.execute(
            """
            UPDATE lesson_draft_workspaces
            SET status = 'published',
                published_lesson_asset_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE draft_id = ?
            """,
            (lesson_asset_id, draft_id),
        )
        log_admin_adjustment(
            conn,
            admin_id,
            "lesson_draft",
            draft_id,
            "publish",
            {"lesson_asset_id": lesson_asset_id, "reason": reason},
        )
        conn.commit()
    return {"draft_id": draft_id, "lesson_asset_id": lesson_asset_id, "status": "published"}


def get_existing_published_lesson_asset_id(user_id: str, lesson_date: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT lesson_asset_id
            FROM lesson_json_assets
            WHERE user_id = ? AND lesson_date = ? AND status = 'published'
            ORDER BY published_at DESC, created_at DESC
            LIMIT 1
            """,
            (user_id, lesson_date),
        ).fetchone()
        if row:
            return str(row["lesson_asset_id"])
        version_row = conn.execute(
            """
            SELECT lja.lesson_asset_id
            FROM lesson_json_versions ljv
            JOIN lesson_json_assets lja ON lja.lesson_asset_id = ljv.lesson_asset_id
            WHERE lja.user_id = ? AND lja.lesson_date = ? AND ljv.status IN ('published', 'rollback_published')
            ORDER BY ljv.created_at DESC, ljv.version_no DESC
            LIMIT 1
            """,
            (user_id, lesson_date),
        ).fetchone()
        return str(version_row["lesson_asset_id"]) if version_row else None


def generate_and_save_today(user_id: str = "user_mom", lesson_date: str | None = None) -> str:
    lesson_date = lesson_date or today_iso()
    init_db()
    existing = get_existing_published_lesson_asset_id(user_id, lesson_date)
    if existing:
        return existing
    draft = get_latest_lesson_draft(user_id, lesson_date)
    if not draft:
        draft_id = generate_lesson_draft_workspace(
            user_id,
            lesson_date,
            action="auto_generate_before_publish",
        )
    else:
        draft_id = draft["draft_id"]
    return publish_lesson_draft_workspace(
        draft_id,
        admin_id="admin_xly",
        reason="system_auto_publish_due_lesson",
    )["lesson_asset_id"]


def generate_lesson_draft_today(user_id: str = "user_mom", lesson_date: str | None = None) -> str:
    init_db()
    return generate_lesson_draft_workspace(user_id, lesson_date, action="admin_generate_draft")


def fetch_lesson_asset(conn: sqlite3.Connection, lesson_asset_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM lesson_json_assets WHERE lesson_asset_id = ?",
        (lesson_asset_id,),
    ).fetchone()
    if not row:
        return None
    asset = dict(row)
    asset["lesson_json"] = safe_json_loads(asset.get("lesson_json"), {})
    return asset


def get_published_lesson_from_versions(
    conn: sqlite3.Connection,
    user_id: str,
    lesson_date: str,
) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT ljv.lesson_json
        FROM lesson_json_versions ljv
        JOIN lesson_json_assets lja ON lja.lesson_asset_id = ljv.lesson_asset_id
        WHERE lja.user_id = ? AND lja.lesson_date = ? AND ljv.status IN ('published', 'rollback_published')
        ORDER BY ljv.created_at DESC, ljv.version_no DESC
        LIMIT 1
        """,
        (user_id, lesson_date),
    ).fetchone()
    if not row:
        return None
    lesson = safe_json_loads(row["lesson_json"], None)
    if lesson:
        ensure_lesson_runtime_assets(conn, lesson)
    return lesson


def get_today_lesson(user_id: str = "user_mom", lesson_date: str | None = None) -> dict[str, Any]:
    lesson_date = lesson_date or today_iso()
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT lesson_json FROM lesson_json_assets
            WHERE user_id = ? AND lesson_date = ? AND status = 'published'
            ORDER BY published_at DESC, created_at DESC
            LIMIT 1
            """,
            (user_id, lesson_date),
        ).fetchone()
        if row:
            lesson = json.loads(row["lesson_json"])
            ensure_lesson_runtime_assets(conn, lesson)
            conn.commit()
            return lesson
        version_lesson = get_published_lesson_from_versions(conn, user_id, lesson_date)
        if version_lesson:
            conn.commit()
            return version_lesson
    lesson_asset_id = generate_and_save_today(user_id, lesson_date)
    with connect() as conn:
        row = conn.execute(
            "SELECT lesson_json FROM lesson_json_assets WHERE lesson_asset_id = ?",
            (lesson_asset_id,),
        ).fetchone()
        lesson = json.loads(row["lesson_json"])
        ensure_lesson_runtime_assets(conn, lesson)
        conn.commit()
        return lesson


def get_admin_dashboard(user_id: str = "user_mom", lesson_date: str | None = None) -> dict[str, Any]:
    lesson_date = lesson_date or today_iso()
    init_db()
    with connect() as conn:
        user = row_to_dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone())
        login_accounts = rows_to_dicts(
            conn.execute(
                """
                SELECT
                  username AS login_account,
                  role,
                  remember_enabled,
                  status,
                  created_at,
                  last_login_at
                FROM local_login_accounts
                WHERE user_id = ?
                ORDER BY created_at
                """,
                (user_id,),
            ).fetchall()
        )
        profile = row_to_dict(
            conn.execute("SELECT * FROM learning_profiles WHERE user_id = ?", (user_id,)).fetchone()
        )
        status = row_to_dict(
            conn.execute("SELECT * FROM learning_status WHERE user_id = ?", (user_id,)).fetchone()
        )
        latest_asset_row = conn.execute(
            """
            SELECT *
            FROM lesson_json_assets
            WHERE user_id = ? AND lesson_date = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, lesson_date),
        ).fetchone()
        lesson_asset = dict(latest_asset_row) if latest_asset_row else None
        if lesson_asset:
            lesson_asset["lesson_json"] = safe_json_loads(lesson_asset.get("lesson_json"), {})
        versions = []
        if lesson_asset:
            versions = rows_to_dicts(
                conn.execute(
                    """
                    SELECT version_id, version_no, status, created_at
                    FROM lesson_json_versions
                    WHERE lesson_asset_id = ?
                    ORDER BY version_no DESC
                    """,
                    (lesson_asset["lesson_asset_id"],),
                ).fetchall()
            )
        notes = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM admin_notes
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 12
                """,
                (user_id,),
            ).fetchall()
        )
        adjustments = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM admin_adjustments
                ORDER BY created_at DESC
                LIMIT 20
                """
            ).fetchall()
        )
        reviews = rows_to_dicts(
            conn.execute(
                """
                SELECT review_asset_id, lesson_asset_id, review_date, status,
                       validation_status, human_readable_summary, created_at
                FROM learning_review_assets
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (user_id,),
            ).fetchall()
        )
        progress = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM daily_progress
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (user_id,),
            ).fetchall()
        )
        errors = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM error_records
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 12
                """,
                (user_id,),
            ).fetchall()
        )
        difficulties = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM difficulty_records
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 12
                """,
                (user_id,),
            ).fetchall()
        )
    return {
        "user": user,
        "login_accounts": login_accounts,
        "profile": profile,
        "status": status,
        "lesson_asset": lesson_asset,
        "versions": versions,
        "notes": notes,
        "adjustments": adjustments,
        "recent_reviews": reviews,
        "recent_progress": progress,
        "recent_errors": errors,
        "recent_difficulties": difficulties,
    }


def get_admin_user_directory() -> dict[str, Any]:
    init_db()
    with connect() as conn:
        users = rows_to_dicts(
            conn.execute(
                """
                SELECT
                  u.user_id,
                  u.nickname,
                  u.role,
                  u.status,
                  lp.occupation,
                  lp.english_foundation,
                  ls.learning_days,
                  ls.current_stage,
                  ls.last_learning_date,
                  la.username AS login_account,
                  (
                    SELECT COUNT(*)
                    FROM lesson_draft_workspaces ldw
                    WHERE ldw.user_id = u.user_id AND ldw.status = 'pending_publish'
                  ) AS pending_draft_count
                FROM users u
                LEFT JOIN learning_profiles lp ON lp.user_id = u.user_id
                LEFT JOIN learning_status ls ON ls.user_id = u.user_id
                LEFT JOIN local_login_accounts la ON la.user_id = u.user_id
                WHERE u.role = 'learner'
                ORDER BY u.created_at DESC
                """
            ).fetchall()
        )
    return {"users": users}


def get_learning_overview(user_id: str = "user_mom") -> dict[str, Any]:
    init_db()
    with connect() as conn:
        status = row_to_dict(
            conn.execute("SELECT * FROM learning_status WHERE user_id = ?", (user_id,)).fetchone()
        ) or {}
        vocab = conn.execute(
            """
            SELECT
              COUNT(*) AS total_seen,
              SUM(CASE WHEN mastery_status = 'mastered' THEN 1 ELSE 0 END) AS mastered,
              SUM(CASE WHEN mastery_status IN ('reviewing', 'weak') THEN 1 ELSE 0 END) AS needs_review
            FROM vocabulary_mastery
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        review_rows = rows_to_dicts(
            conn.execute(
                """
                SELECT review_asset_id, review_date, human_readable_summary, review_json, created_at
                FROM learning_review_assets
                WHERE user_id = ?
                ORDER BY review_date DESC, created_at DESC
                LIMIT 5
                """,
                (user_id,),
            ).fetchall()
        )
        for item in review_rows:
            review_json = safe_json_loads(item.get("review_json"), {})
            item["quiz_score"] = review_json.get("quiz_score")
            item["weak_words"] = review_json.get("weak_words", [])
            item.pop("review_json", None)
        knowledge = rows_to_dicts(
            conn.execute(
                """
                SELECT kp.name, ukp.status, ukp.mastery_score
                FROM user_knowledge_progress ukp
                JOIN knowledge_points kp ON kp.knowledge_id = ukp.knowledge_id
                WHERE ukp.user_id = ?
                ORDER BY kp.sort_order
                """,
                (user_id,),
            ).fetchall()
        )
    return {
        "learning_days": status.get("learning_days", 0),
        "streak_days": status.get("streak_days", 0),
        "current_stage": status.get("current_stage"),
        "overall_level": status.get("overall_level"),
        "last_learning_date": status.get("last_learning_date"),
        "weak_summary": status.get("weak_summary"),
        "next_suggestion": status.get("next_suggestion"),
        "vocabulary_estimate": int((vocab or {})["total_seen"] or 0),
        "mastered_vocabulary": int((vocab or {})["mastered"] or 0),
        "needs_review_vocabulary": int((vocab or {})["needs_review"] or 0),
        "recent_reviews": review_rows,
        "knowledge_progress": knowledge,
    }


def get_learning_route_map(user_id: str = "user_mom") -> dict[str, Any]:
    init_db()
    with connect() as conn:
        status = row_to_dict(
            conn.execute("SELECT * FROM learning_status WHERE user_id = ?", (user_id,)).fetchone()
        ) or {}
        lesson_row = conn.execute(
            """
            SELECT lesson_json
            FROM lesson_json_assets
            WHERE user_id = ? AND lesson_date = ? AND status = 'published'
            ORDER BY published_at DESC, created_at DESC
            LIMIT 1
            """,
            (user_id, today_iso()),
        ).fetchone()
        version_lesson = None if lesson_row else get_published_lesson_from_versions(conn, user_id, today_iso())
        user_route = load_user_learning_route(user_id)
        if user_route:
            items = []
            for index, route_item in enumerate(user_route.get("route_items") or [], start=1):
                item = dict(route_item)
                item["day_number"] = int(item.get("day_number") or index)
                item["recommended_order"] = item["day_number"]
                item["theme"] = item.get("theme") or item.get("main_knowledge_label") or f"第 {index} 天"
                item["knowledge_name"] = item.get("route_module_label") or item.get("knowledge_name") or item["theme"]
                item["scenario_name"] = item.get("passage_module_label") or item.get("scenario_name") or "日常对话"
                item["level_code"] = item.get("level_code") or user_route.get("stage", {}).get("name")
                item["target_minutes"] = item.get("target_minutes") or user_route.get("daily_constraints", {}).get("target_minutes") or 30
                item["mastery_score"] = 0
                items.append(item)
        else:
            items = rows_to_dicts(
                conn.execute(
                    """
                    SELECT
                      cri.route_item_id,
                      cri.recommended_order,
                      cri.target_minutes,
                      cri.objective,
                      kp.name AS knowledge_name,
                      kp.category AS knowledge_category,
                      kp.description AS knowledge_description,
                      sm.name AS scenario_name,
                      sl.level_code,
                      sl.goal AS scenario_goal,
                      sl.vocabulary_scope,
                      sl.sentence_scope,
                      COALESCE(ukp.status, 'not_started') AS knowledge_status,
                      COALESCE(ukp.mastery_score, 0) AS mastery_score,
                      COALESCE(usp.status, 'not_started') AS scenario_status
                    FROM curriculum_route_items cri
                    LEFT JOIN knowledge_points kp ON kp.knowledge_id = cri.knowledge_id
                    LEFT JOIN scenario_levels sl ON sl.scenario_level_id = cri.scenario_level_id
                    LEFT JOIN scenario_modules sm ON sm.scenario_id = sl.scenario_id
                    LEFT JOIN user_knowledge_progress ukp
                      ON ukp.user_id = ? AND ukp.knowledge_id = cri.knowledge_id
                    LEFT JOIN user_scenario_progress usp
                      ON usp.user_id = ? AND usp.scenario_id = sm.scenario_id
                    ORDER BY cri.recommended_order
                    """,
                    (user_id, user_id),
                ).fetchall()
            )
    active_route_id = None
    active_summary = None
    if lesson_row:
        lesson = safe_json_loads(lesson_row["lesson_json"], {})
        route_basis = lesson.get("route_basis") or {}
        active_route_id = route_basis.get("content_route_item_id") or route_basis.get("route_item_id")
        active_summary = lesson.get("progress_summary") or build_progress_summary(lesson)
    elif version_lesson:
        route_basis = version_lesson.get("route_basis") or {}
        active_route_id = route_basis.get("content_route_item_id") or route_basis.get("route_item_id")
        active_summary = version_lesson.get("progress_summary") or build_progress_summary(version_lesson)
    active_index = next(
        (index for index, item in enumerate(items, start=1) if item.get("route_item_id") == active_route_id),
        None,
    )
    if active_index is None:
        active_index = min(max(1, int(status.get("learning_days") or 0) + 1), max(1, len(items)))
    for index, item in enumerate(items, start=1):
        item["day_number"] = index
        item["theme"] = item.get("theme") or item.get("knowledge_name") or item.get("scenario_name") or f"第 {index} 天"
        summary = active_summary if item.get("route_item_id") == active_route_id and active_summary else build_route_progress_summary(item)
        item.update(summary)
        if index < active_index:
            item["status"] = "completed"
        elif index == active_index:
            item["status"] = "active"
        else:
            item["status"] = "next" if index == active_index + 1 else "locked"
    return {"route_map": items, "status": status}


def get_admin_user_workspace(user_id: str = "user_mom", lesson_date: str | None = None) -> dict[str, Any]:
    lesson_date = lesson_date or today_iso()
    init_db()
    draft = get_latest_lesson_draft(user_id, lesson_date) or get_latest_lesson_draft(user_id)
    with connect() as conn:
        user = row_to_dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone())
        profile = row_to_dict(
            conn.execute("SELECT * FROM learning_profiles WHERE user_id = ?", (user_id,)).fetchone()
        )
        login_accounts = rows_to_dicts(
            conn.execute(
                """
                SELECT username AS login_account, role, status, last_login_at
                FROM local_login_accounts
                WHERE user_id = ?
                ORDER BY created_at
                """,
                (user_id,),
            ).fetchall()
        )
        published = row_to_dict(
            conn.execute(
                """
                SELECT lesson_asset_id, lesson_date, status, human_readable_summary, published_at
                FROM lesson_json_assets
                WHERE user_id = ? AND lesson_date = ? AND status = 'published'
                ORDER BY published_at DESC, created_at DESC
                LIMIT 1
                """,
                (user_id, lesson_date),
            ).fetchone()
        )
        feedback = rows_to_dicts(
            conn.execute(
                """
                SELECT feedback_id, target_type, target_id, feedback_text, created_at
                FROM admin_feedback_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (user_id,),
            ).fetchall()
        )
    return {
        "user": user,
        "profile": profile,
        "login_accounts": login_accounts,
        "latest_draft": draft,
        "published_today": published,
        "learning_overview": get_learning_overview(user_id),
        "feedback_logs": feedback,
    }


def get_user_state(user_id: str = "user_mom") -> dict[str, Any]:
    init_db()
    with connect() as conn:
        completed_quiz_questions = conn.execute(
            """
            SELECT COUNT(DISTINCT qa.question_id) AS completed_count
            FROM question_answers qa
            JOIN quiz_attempts qat ON qat.attempt_id = qa.attempt_id
            WHERE qat.user_id = ?
              AND COALESCE(qa.selected_answer, '') <> ''
            """,
            (user_id,),
        ).fetchone()
        return {
            "user": row_to_dict(conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()),
            "profile": row_to_dict(
                conn.execute("SELECT * FROM learning_profiles WHERE user_id = ?", (user_id,)).fetchone()
            ),
            "status": row_to_dict(
                conn.execute("SELECT * FROM learning_status WHERE user_id = ?", (user_id,)).fetchone()
            ),
            "knowledge_progress": rows_to_dicts(
                conn.execute(
                    """
                    SELECT ukp.*, kp.name, kp.category
                    FROM user_knowledge_progress ukp
                    JOIN knowledge_points kp ON kp.knowledge_id = ukp.knowledge_id
                    WHERE ukp.user_id = ?
                    ORDER BY kp.sort_order
                    """,
                    (user_id,),
                ).fetchall()
            ),
            "scenario_progress": rows_to_dicts(
                conn.execute(
                    """
                    SELECT usp.*, sm.name
                    FROM user_scenario_progress usp
                    JOIN scenario_modules sm ON sm.scenario_id = usp.scenario_id
                    WHERE usp.user_id = ?
                    ORDER BY sm.priority
                    """,
                    (user_id,),
                ).fetchall()
            ),
            "vocabulary_mastery": rows_to_dicts(
                conn.execute(
                    """
                    SELECT vm.*, vi.word, vi.core_meaning, vi.part_of_speech
                    FROM vocabulary_mastery vm
                    JOIN vocabulary_items vi ON vi.word_id = vm.word_id
                    WHERE vm.user_id = ?
                    ORDER BY vm.first_seen_date DESC, vi.word
                    """,
                    (user_id,),
                ).fetchall()
            ),
            "completed_quiz_questions": int(
                completed_quiz_questions["completed_count"] if completed_quiz_questions else 0
            ),
            "review_queue": rows_to_dicts(
                conn.execute(
                    """
                    SELECT *
                    FROM review_queue
                    WHERE user_id = ? AND status = 'pending'
                    ORDER BY priority DESC, created_at DESC
                    """,
                    (user_id,),
                ).fetchall()
            ),
        }


def update_user_profile(
    user_id: str,
    payload: dict[str, Any],
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    updates = {key: payload[key] for key in ADMIN_FIELDS if key in payload}
    display_username_input = payload.get("username", payload.get("display_username"))
    display_username = None
    if display_username_input is not None:
        display_username = str(display_username_input).strip()
    if not updates and not display_username:
        return get_user_state(user_id)["profile"] or {}
    with connect() as conn:
        adjustment_detail: dict[str, Any] = {}
        if updates:
            fields = ", ".join([f"{key} = ?" for key in updates])
            params = list(updates.values()) + [user_id]
            conn.execute(
                f"UPDATE learning_profiles SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                params,
            )
            adjustment_detail["learning_profile"] = updates
        if display_username:
            conn.execute(
                "UPDATE users SET nickname = ? WHERE user_id = ?",
                (display_username, user_id),
            )
            adjustment_detail["username"] = display_username
        log_admin_adjustment(conn, admin_id, "user_profile", user_id, "update_profile", adjustment_detail)
        log_debug(
            conn,
            "admin",
            "info",
            "user profile updated",
            {"user_id": user_id, "fields": sorted(adjustment_detail.keys())},
        )
        conn.commit()
        row = conn.execute("SELECT * FROM learning_profiles WHERE user_id = ?", (user_id,)).fetchone()
        return dict(row)


def update_account_display_name(session_token: str, display_name: str) -> dict[str, Any]:
    session = verify_local_session(session_token)
    user_id = session.get("user_id")
    nickname = display_name.strip()
    if not user_id:
        raise ValueError("当前账号没有可修改的学习者资料")
    if not nickname:
        raise ValueError("用户名不能为空")
    if len(nickname) > 24:
        raise ValueError("用户名不能超过 24 个字符")
    with connect() as conn:
        conn.execute("UPDATE users SET nickname = ? WHERE user_id = ?", (nickname, user_id))
        if session.get("role") == "admin":
            conn.execute(
                "UPDATE admin_users SET nickname = ? WHERE admin_id = ?",
                (nickname, session["login_account"]),
            )
        log_debug(conn, "account", "info", "display name updated", {"user_id": user_id})
        conn.commit()
    return {
        "login_account": session["login_account"],
        "username": nickname,
        "user_id": user_id,
        "role": session["role"],
        "nickname": nickname,
        "remember": True,
        "session_token": session["session_token"],
        "expires_at": session["expires_at"],
    }


def update_account_password(session_token: str, current_password: str, new_password: str) -> dict[str, str]:
    session = verify_local_session(session_token)
    current_hash = hashlib.sha256(current_password.encode("utf-8")).hexdigest()
    next_password = new_password.strip()
    if len(next_password) < 8:
        raise ValueError("新密码至少 8 位")
    next_hash = hashlib.sha256(next_password.encode("utf-8")).hexdigest()
    with connect() as conn:
        row = conn.execute(
            "SELECT password_sha256 FROM local_login_accounts WHERE username = ? AND status = 'active'",
            (session["login_account"],),
        ).fetchone()
        if not row or row["password_sha256"] != current_hash:
            raise ValueError("当前密码不正确")
        conn.execute(
            "UPDATE local_login_accounts SET password_sha256 = ? WHERE username = ?",
            (next_hash, session["login_account"]),
        )
        log_debug(conn, "account", "info", "password updated", {"login_account": session["login_account"]})
        conn.commit()
    return {"status": "ok"}


def save_admin_note(payload: dict[str, Any], admin_id: str = "admin_xly") -> dict[str, str]:
    init_db()
    user_id = payload.get("user_id", "user_mom")
    target_type = payload.get("target_type", "lesson_plan")
    target_id = payload.get("target_id") or today_iso()
    with connect() as conn:
        note_id = new_id("note")
        conn.execute(
            """
            INSERT INTO admin_notes (
              note_id, admin_id, user_id, target_type, target_id,
              admin_note, admin_instruction, admin_revision_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                note_id,
                admin_id,
                user_id,
                target_type,
                target_id,
                payload.get("admin_note"),
                payload.get("admin_instruction"),
                payload.get("admin_revision_note"),
            ),
        )
        log_admin_adjustment(
            conn,
            admin_id,
            target_type,
            target_id,
            "save_admin_note",
            {
                "admin_note": payload.get("admin_note"),
                "admin_instruction": payload.get("admin_instruction"),
                "admin_revision_note": payload.get("admin_revision_note"),
            },
        )
        conn.commit()
    return {"note_id": note_id, "target_type": target_type, "target_id": target_id}


def save_admin_feedback(payload: dict[str, Any], admin_id: str = "admin_xly") -> dict[str, str]:
    init_db()
    user_id = payload.get("user_id", "user_mom")
    target_type = payload.get("target_type", "lesson_draft")
    target_id = payload.get("target_id") or payload.get("draft_id") or today_iso()
    feedback_text = str(payload.get("feedback_text") or "").strip()
    if not feedback_text:
        raise ValueError("feedback_text is required")
    with connect() as conn:
        feedback_id = new_id("feedback")
        conn.execute(
            """
            INSERT INTO admin_feedback_logs (
              feedback_id, admin_id, user_id, target_type, target_id, feedback_text
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (feedback_id, admin_id, user_id, target_type, target_id, feedback_text),
        )
        log_admin_adjustment(
            conn,
            admin_id,
            target_type,
            target_id,
            "save_feedback",
            {"feedback_text": feedback_text},
        )
        conn.commit()
    return {"feedback_id": feedback_id}


def update_lesson_draft(
    lesson_asset_id: str,
    payload: dict[str, Any],
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    lesson_json = payload.get("lesson_json") or payload
    if not isinstance(lesson_json, dict):
        raise ValueError("lesson_json must be an object")
    lesson_json["lesson_asset_id"] = lesson_asset_id
    lesson_json.setdefault("schema_version", "lesson_json.v1")
    lesson_json.setdefault("source_generation_run_id", new_id("manual"))
    lesson_json.setdefault("human_readable_summary", lesson_json.get("theme", "管理员草稿"))
    return {
        "lesson_asset_id": save_lesson_json(
            lesson_json,
            status="draft",
            admin_id=admin_id,
            revision_reason=payload.get("reason", "admin_edit_draft"),
        ),
        "status": "draft",
    }


def publish_lesson_asset(
    lesson_asset_id: str,
    payload: dict[str, Any] | None = None,
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    payload = payload or {}
    with connect() as conn:
        asset = fetch_lesson_asset(conn, lesson_asset_id)
        if not asset:
            raise ValueError(f"lesson asset not found: {lesson_asset_id}")
    lesson_json = asset["lesson_json"]
    if payload.get("admin_note") is not None:
        lesson_json["admin_note"] = payload.get("admin_note")
    if payload.get("admin_instruction") is not None:
        lesson_json["admin_instruction"] = payload.get("admin_instruction")
    if payload.get("admin_revision_note") is not None:
        lesson_json["admin_revision_note"] = payload.get("admin_revision_note")
    save_lesson_json(
        lesson_json,
        status="published",
        admin_id=admin_id,
        revision_reason=payload.get("reason", "admin_publish"),
    )
    return {"lesson_asset_id": lesson_asset_id, "status": "published"}


def rollback_lesson_asset(
    lesson_asset_id: str,
    version_id: str,
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT lesson_json
            FROM lesson_json_versions
            WHERE lesson_asset_id = ? AND version_id = ?
            """,
            (lesson_asset_id, version_id),
        ).fetchone()
        if not row:
            raise ValueError(f"version not found: {version_id}")
        lesson_json = safe_json_loads(row["lesson_json"], {})
    save_lesson_json(
        lesson_json,
        status="published",
        admin_id=admin_id,
        revision_reason=f"rollback_to_{version_id}",
    )
    return {"lesson_asset_id": lesson_asset_id, "status": "published", "rolled_back_to": version_id}


def update_route_priority(
    route_item_id: str,
    payload: dict[str, Any],
    admin_id: str = "admin_xly",
) -> dict[str, Any]:
    init_db()
    with connect() as conn:
        conn.execute(
            """
            UPDATE curriculum_route_items
            SET recommended_order = ?, target_minutes = COALESCE(?, target_minutes)
            WHERE route_item_id = ?
            """,
            (payload.get("recommended_order"), payload.get("target_minutes"), route_item_id),
        )
        log_admin_adjustment(conn, admin_id, "curriculum_route_item", route_item_id, "update_route_priority", payload)
        conn.commit()
        row = conn.execute("SELECT * FROM curriculum_route_items WHERE route_item_id = ?", (route_item_id,)).fetchone()
        return dict(row)


def normalize_word_mastery_payload(payload: Any) -> dict[str, str]:
    if isinstance(payload, dict):
        return {str(key).lower(): str(value) for key, value in payload.items()}
    if isinstance(payload, list):
        result = {}
        for item in payload:
            if isinstance(item, dict) and item.get("word"):
                result[str(item["word"]).lower()] = str(item.get("status", "fuzzy"))
        return result
    return {}


def normalize_quiz_answers_payload(payload: Any) -> dict[str, str]:
    if isinstance(payload, dict):
        return {str(key): str(value) for key, value in payload.items()}
    if isinstance(payload, list):
        result = {}
        for item in payload:
            if isinstance(item, dict) and item.get("prompt"):
                result[str(item["prompt"])] = str(item.get("selected_answer", ""))
        return result
    return {}


def compute_learning_counters(conn: sqlite3.Connection, user_id: str) -> tuple[int, int, str | None]:
    rows = conn.execute(
        """
        SELECT DISTINCT progress_date
        FROM daily_progress
        WHERE user_id = ?
        ORDER BY progress_date
        """,
        (user_id,),
    ).fetchall()
    dates = [date.fromisoformat(row["progress_date"]) for row in rows if row["progress_date"]]
    if not dates:
        return 0, 0, None
    learning_days = len(dates)
    last_date = dates[-1]
    streak_days = 1
    expected = last_date - timedelta(days=1)
    for day in reversed(dates[:-1]):
        if day != expected:
            break
        streak_days += 1
        expected = day - timedelta(days=1)
    return learning_days, streak_days, last_date.isoformat()


def submit_learning_progress(
    user_id: str = "user_mom",
    payload: dict[str, Any] | None = None,
    lesson_date: str | None = None,
) -> dict[str, Any]:
    init_db()
    payload = payload or {}
    lesson_asset_id = payload.get("lesson_asset_id")
    if lesson_asset_id:
        with connect() as conn:
            asset = fetch_lesson_asset(conn, lesson_asset_id)
            if not asset:
                raise ValueError(f"lesson asset not found: {lesson_asset_id}")
            lesson = asset["lesson_json"]
    else:
        lesson = get_today_lesson(user_id, lesson_date or payload.get("lesson_date") or today_iso())
        lesson_asset_id = lesson["lesson_asset_id"]

    lesson_date = lesson["lesson_date"]
    completed_sections = payload.get("completed_sections") or [
        "preview",
        "vocabulary",
        "passage",
        "knowledge",
        "quiz",
        "summary",
    ]
    word_mastery = normalize_word_mastery_payload(payload.get("word_mastery"))
    quiz_answers = normalize_quiz_answers_payload(payload.get("quiz_answers"))
    quiz_mistakes = payload.get("quiz_mistakes") or []
    difficulty_notes = payload.get("difficulty_notes") or []
    if isinstance(difficulty_notes, str):
        difficulty_notes = [line.strip() for line in difficulty_notes.splitlines() if line.strip()]

    mastered_words: list[str] = []
    weak_words: list[str] = []
    incorrect_answers: list[dict[str, Any]] = []
    correct_count = 0
    questions = lesson.get("quiz", {}).get("questions", [])
    total_questions = len(questions)

    with connect() as conn:
        quiz_id = f"quiz_{lesson_asset_id}"
        attempt_id = new_id("attempt")
        answer_rows = []
        error_rows = []
        error_keys = set()
        for idx, question in enumerate(questions, start=1):
            selected = quiz_answers.get(question["prompt"], "")
            is_correct = selected == question.get("answer")
            correct_count += int(is_correct)
            question_id = f"{quiz_id}_q_{idx}"
            error_type = None if is_correct else payload.get("default_error_type", "记忆不牢")
            answer_rows.append(
                (new_id("answer"), attempt_id, question_id, selected, int(is_correct), error_type)
            )
            if not is_correct:
                incorrect = {
                    "prompt": question["prompt"],
                    "selected_answer": selected,
                    "answer": question.get("answer"),
                    "explanation": question.get("explanation"),
                }
                incorrect_answers.append(incorrect)
                error_keys.add((question["prompt"], selected))
                error_rows.append(
                    (
                        new_id("err"),
                        user_id,
                        lesson_asset_id,
                        "quiz_question",
                        question_id,
                        error_type,
                        json.dumps(incorrect, ensure_ascii=False),
                        "下次学习前先复习本题相关单词和句子。",
                    )
                )
        prompt_to_question_id = {
            question["prompt"]: f"{quiz_id}_q_{idx}"
            for idx, question in enumerate(questions, start=1)
        }
        for item in (quiz_mistakes if isinstance(quiz_mistakes, list) else []):
            if not isinstance(item, dict) or not item.get("prompt"):
                continue
            selected = str(item.get("selected_answer") or "")
            key = (str(item["prompt"]), selected)
            if key in error_keys:
                continue
            error_keys.add(key)
            incorrect = {
                "prompt": str(item["prompt"]),
                "selected_answer": selected,
                "answer": item.get("answer"),
                "explanation": item.get("explanation"),
            }
            incorrect_answers.append(incorrect)
            error_rows.append(
                (
                    new_id("err"),
                    user_id,
                    lesson_asset_id,
                    "quiz_question",
                    prompt_to_question_id.get(str(item["prompt"]), new_id("quiz_question")),
                    payload.get("default_error_type", "记忆不牢"),
                    json.dumps(incorrect, ensure_ascii=False),
                    "下次学习前先复习本题相关单词和句子。",
                )
            )
        score = correct_count / total_questions if total_questions else 0
        conn.execute(
            """
            INSERT INTO quiz_attempts (
              attempt_id, quiz_id, user_id, score, duration_seconds
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (attempt_id, quiz_id, user_id, score, int(payload.get("duration_seconds") or 0)),
        )
        conn.executemany(
            """
            INSERT INTO question_answers (
              answer_id, attempt_id, question_id, selected_answer, is_correct, error_type
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            answer_rows,
        )
        conn.executemany(
            """
            INSERT INTO error_records (
              error_id, user_id, lesson_asset_id, item_type, item_id,
              error_type, context, next_review_plan
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            error_rows,
        )

        for item in lesson.get("vocabulary", []):
            word = str(item["word"]).lower()
            word_id = f"word_{word}"
            status = word_mastery.get(word, "fuzzy")
            previous_row = conn.execute(
                """
                SELECT mastery_status
                FROM vocabulary_mastery
                WHERE user_id = ? AND word_id = ?
                """,
                (user_id, word_id),
            ).fetchone()
            previous_status = previous_row["mastery_status"] if previous_row else None
            if status in {"known", "mastered", "会了"}:
                mastery_status = "mastered"
                mastered_words.append(item["word"])
                recent_error = None
            elif status in {"unknown", "不会"}:
                mastery_status = "weak"
                weak_words.append(item["word"])
                recent_error = "学习者标记为不会"
            else:
                mastery_status = "reviewing"
                weak_words.append(item["word"])
                recent_error = "学习者标记为模糊"
            conn.execute(
                """
                INSERT INTO vocabulary_mastery_events (
                  event_id, user_id, lesson_asset_id, word_id,
                  previous_status, selected_status, resulting_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id("wordevt"),
                    user_id,
                    lesson_asset_id,
                    word_id,
                    previous_status,
                    status,
                    mastery_status,
                ),
            )
            conn.execute(
                """
                UPDATE vocabulary_mastery
                SET review_count = review_count + 1,
                    mastery_status = ?,
                    recent_error = ?,
                    next_review_date = ?
                WHERE user_id = ? AND word_id = ?
                """,
                (
                    mastery_status,
                    recent_error,
                    (datetime.fromisoformat(lesson_date) + timedelta(days=1)).date().isoformat(),
                    user_id,
                    word_id,
                ),
            )
            if mastery_status == "mastered":
                conn.execute(
                    """
                    UPDATE review_queue
                    SET status = 'completed'
                    WHERE user_id = ? AND item_type = 'word' AND item_id = ? AND status = 'pending'
                    """,
                    (user_id, word_id),
                )
            elif mastery_status in {"weak", "reviewing"}:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO review_queue (
                      review_id, user_id, item_type, item_id, reason,
                      priority, planned_review_date, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"review_{lesson_asset_id}_{word_id}",
                        user_id,
                        "word",
                        word_id,
                        recent_error or "需要复习",
                        85 if mastery_status == "weak" else 65,
                        (datetime.fromisoformat(lesson_date) + timedelta(days=1)).date().isoformat(),
                        "pending",
                    ),
                )
        for note in difficulty_notes:
            conn.execute(
                """
                INSERT INTO difficulty_records (
                  difficulty_id, user_id, lesson_asset_id, module_type,
                  description, system_label
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (new_id("diff"), user_id, lesson_asset_id, "daily_learning", note, "user_reported"),
            )

        generated_summary = build_daily_summary(score, mastered_words, weak_words, difficulty_notes)
        progress_id = f"progress_{lesson_asset_id}"
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_progress (
              progress_id, user_id, lesson_asset_id, progress_date,
              completed_sections_json, learning_minutes, self_rating, generated_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                progress_id,
                user_id,
                lesson_asset_id,
                lesson_date,
                json.dumps(completed_sections, ensure_ascii=False),
                int(payload.get("learning_minutes") or lesson.get("estimated_minutes") or 0),
                payload.get("self_rating", "刚好"),
                generated_summary,
            ),
        )

        route_basis = lesson.get("route_basis", {})
        knowledge_status = "mastered" if score >= 0.8 and len(weak_words) <= 1 else "learning"
        mastery_score = max(0.3, min(1.0, score if score else 0.5))
        if route_basis.get("knowledge_id"):
            conn.execute(
                """
                UPDATE user_knowledge_progress
                SET status = ?, last_studied_at = ?, mastery_score = ?
                WHERE user_id = ? AND knowledge_id = ?
                """,
                (knowledge_status, lesson_date, mastery_score, user_id, route_basis.get("knowledge_id")),
            )
        if route_basis.get("scenario_id"):
            conn.execute(
                """
                UPDATE user_scenario_progress
                SET status = ?, last_studied_at = ?
                WHERE user_id = ? AND scenario_id = ?
                """,
                (
                    "completed" if knowledge_status == "mastered" else "learning",
                    lesson_date,
                    user_id,
                    route_basis.get("scenario_id"),
                ),
            )

        learning_days, streak_days, last_learning_date = compute_learning_counters(conn, user_id)
        conn.execute(
            """
            UPDATE learning_status
            SET learning_days = ?,
                streak_days = ?,
                last_learning_date = ?,
                weak_summary = ?,
                next_suggestion = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                learning_days,
                streak_days,
                last_learning_date or lesson_date,
                "、".join(weak_words[:4]) if weak_words else "今日没有明显薄弱单词",
                build_next_day_adjustment(lesson, weak_words, difficulty_notes),
                user_id,
            ),
        )

        review = {
            "schema_version": "learning_review_json.v1",
            "user_id": user_id,
            "lesson_asset_id": lesson_asset_id,
            "review_date": lesson_date,
            "human_readable_summary": generated_summary,
            "admin_note": payload.get("admin_note"),
            "completed_sections": completed_sections,
            "mastered_words": mastered_words,
            "weak_words": weak_words,
            "difficulty_points": difficulty_notes,
            "quiz_score": round(score, 2),
            "incorrect_answers": incorrect_answers,
            "self_rating": payload.get("self_rating", "刚好"),
            "next_day_adjustment": build_next_day_adjustment(lesson, weak_words, difficulty_notes),
        }
        review_id = f"review_asset_{lesson_asset_id}"
        review_text = json.dumps(review, ensure_ascii=False, sort_keys=True)
        conn.execute(
            """
            INSERT INTO learning_review_assets (
              review_asset_id, user_id, lesson_asset_id, review_date, schema_version,
              status, validation_status, human_readable_summary, admin_note, review_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(review_asset_id) DO UPDATE SET
              user_id = excluded.user_id,
              lesson_asset_id = excluded.lesson_asset_id,
              review_date = excluded.review_date,
              schema_version = excluded.schema_version,
              status = excluded.status,
              validation_status = excluded.validation_status,
              human_readable_summary = excluded.human_readable_summary,
              admin_note = excluded.admin_note,
              review_json = excluded.review_json
            """,
            (
                review_id,
                user_id,
                lesson_asset_id,
                lesson_date,
                review["schema_version"],
                "published",
                "passed",
                review["human_readable_summary"],
                payload.get("admin_note"),
                review_text,
            ),
        )
        version_no = conn.execute(
            "SELECT COALESCE(MAX(version_no), 0) + 1 AS next_no FROM learning_review_versions WHERE review_asset_id = ?",
            (review_id,),
        ).fetchone()["next_no"]
        conn.execute(
            """
            INSERT INTO learning_review_versions (
              version_id, review_asset_id, version_no, status, review_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (f"{review_id}_ver_{version_no}", review_id, version_no, "published", review_text),
        )
        conn.execute(
            """
            INSERT OR REPLACE INTO learning_review_validation_results (
              validation_id, review_asset_id, schema_version, status, warnings_json, errors_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (new_id("val"), review_id, review["schema_version"], "passed", "[]", "[]"),
        )
        doc_id = f"rag_doc_{review_id}"
        rag_content = (
            f"{lesson_date} 学习复盘：{generated_summary}\n"
            f"掌握：{', '.join(mastered_words) or '无'}\n"
            f"薄弱：{', '.join(weak_words) or '无'}\n"
            f"难点：{'; '.join(difficulty_notes) or '无'}\n"
            f"明日建议：{review['next_day_adjustment']}"
        )
        conn.execute(
            """
            INSERT INTO rag_documents (
              document_id, user_id, source_table, source_id, title, content
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
              user_id = excluded.user_id,
              source_table = excluded.source_table,
              source_id = excluded.source_id,
              title = excluded.title,
              content = excluded.content
            """,
            (doc_id, user_id, "learning_review_assets", review_id, f"{lesson_date} 学习复盘", rag_content),
        )
        conn.execute(
            """
            INSERT INTO rag_chunks (
              chunk_id, document_id, chunk_text, tags_json
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(chunk_id) DO UPDATE SET
              document_id = excluded.document_id,
              chunk_text = excluded.chunk_text,
              tags_json = excluded.tags_json
            """,
            (
                f"rag_chunk_{review_id}",
                doc_id,
                rag_content,
                json.dumps(["daily_review", lesson.get("theme")], ensure_ascii=False),
            ),
        )
        log_debug(conn, "learning_review", "info", "learning progress submitted", {"review_asset_id": review_id})
        conn.commit()
        result = {
            "status": "ok",
            "review_asset_id": review_id,
            "review_json": review,
            "quiz_score": round(score, 2),
        }
    try:
        result["next_draft_id"] = generate_lesson_draft_workspace(
            user_id=user_id,
            lesson_date=next_day_iso(lesson_date),
            admin_id="admin_xly",
            action="post_review_generate_next_draft",
        )
    except Exception as exc:
        with connect() as conn:
            log_debug(
                conn,
                "lesson_draft",
                "error",
                "failed to generate next lesson draft after review",
                {"user_id": user_id, "lesson_date": lesson_date, "error": str(exc)},
            )
            conn.commit()
    return result


def build_daily_summary(
    score: float,
    mastered_words: list[str],
    weak_words: list[str],
    difficulty_notes: list[str],
) -> str:
    score_text = f"测试正确率 {round(score * 100)}%"
    mastered_text = f"掌握了 {', '.join(mastered_words)}" if mastered_words else "掌握项还需要继续观察"
    weak_text = f"需要复习 {', '.join(weak_words)}" if weak_words else "今天没有明显薄弱词"
    difficulty_text = f"学习者反馈难点：{'；'.join(difficulty_notes)}" if difficulty_notes else "没有额外难点反馈"
    return f"{score_text}，{mastered_text}，{weak_text}。{difficulty_text}。"


def build_next_day_adjustment(
    lesson: dict[str, Any],
    weak_words: list[str],
    difficulty_notes: list[str],
) -> str:
    route_basis = lesson.get("route_basis", {})
    if weak_words:
        return f"明天开头先复习 {', '.join(weak_words[:3])}，再推进下一小步。"
    if difficulty_notes:
        return "明天降低一点速度，用更多中文支撑解释今天反馈的难点。"
    next_hint = route_basis.get("scenario_name") or route_basis.get("knowledge_name") or "下一阶段"
    return f"明天可以继续推进 {next_hint}，保持 15 分钟以内。"


def submit_sample_progress(user_id: str = "user_mom", lesson_date: str | None = None) -> str:
    lesson = get_today_lesson(user_id, lesson_date)
    payload = {
        "lesson_asset_id": lesson["lesson_asset_id"],
        "completed_sections": ["preview", "vocabulary", "passage", "knowledge", "quiz", "summary"],
        "learning_minutes": 12,
        "self_rating": "刚好",
        "word_mastery": [
            {"word": item["word"], "status": "known" if idx < 2 else "fuzzy"}
            for idx, item in enumerate(lesson.get("vocabulary", []))
        ],
        "quiz_answers": [
            {"prompt": q["prompt"], "selected_answer": q["answer"]}
            for q in lesson.get("quiz", {}).get("questions", [])
        ],
        "difficulty_notes": ["最后一个重点词需要复习"],
    }
    result = submit_learning_progress(user_id, payload, lesson_date)
    return result["review_asset_id"]


def get_learning_review(user_id: str = "user_mom", lesson_date: str | None = None) -> dict[str, Any] | None:
    lesson_date = lesson_date or today_iso()
    init_db()
    with connect() as conn:
        row = conn.execute(
            """
            SELECT review_json
            FROM learning_review_assets
            WHERE user_id = ? AND review_date = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (user_id, lesson_date),
        ).fetchone()
        if not row:
            return None
        return safe_json_loads(row["review_json"], None)


def get_weekly_summary(user_id: str = "user_mom", end_date: str | None = None) -> dict[str, Any]:
    init_db()
    end = datetime.fromisoformat(end_date or today_iso()).date()
    start = end - timedelta(days=6)
    with connect() as conn:
        progress = rows_to_dicts(
            conn.execute(
                """
                SELECT *
                FROM daily_progress
                WHERE user_id = ? AND progress_date BETWEEN ? AND ?
                ORDER BY progress_date
                """,
                (user_id, start.isoformat(), end.isoformat()),
            ).fetchall()
        )
        reviews = rows_to_dicts(
            conn.execute(
                """
                SELECT review_json
                FROM learning_review_assets
                WHERE user_id = ? AND review_date BETWEEN ? AND ?
                ORDER BY review_date
                """,
                (user_id, start.isoformat(), end.isoformat()),
            ).fetchall()
        )
        parsed_reviews = [safe_json_loads(row["review_json"], {}) for row in reviews]
        mastered = sorted({word for review in parsed_reviews for word in review.get("mastered_words", [])})
        weak = sorted({word for review in parsed_reviews for word in review.get("weak_words", [])})
        difficulty_points = [
            point for review in parsed_reviews for point in review.get("difficulty_points", [])
        ]
        total_minutes = sum(int(row.get("learning_minutes") or 0) for row in progress)
        summary = {
            "user_id": user_id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "learning_days": len(progress),
            "total_minutes": total_minutes,
            "mastered_words": mastered,
            "weak_words": weak,
            "difficulty_points": difficulty_points[-8:],
            "human_readable_summary": (
                f"最近 7 天完成 {len(progress)} 天学习，共 {total_minutes} 分钟。"
                f"新掌握：{', '.join(mastered) or '暂无'}。"
                f"持续薄弱：{', '.join(weak) or '暂无'}。"
            ),
            "next_week_suggestion": (
                f"下周先复习 {', '.join(weak[:3])}，再推进下一课。"
                if weak
                else "下周可以按路线图继续推进下一课，保持低负担节奏。"
            ),
        }
        doc_id = f"rag_doc_weekly_{user_id}_{end.strftime('%Y%m%d')}"
        conn.execute(
            """
            INSERT INTO rag_documents (
              document_id, user_id, source_table, source_id, title, content
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
              user_id = excluded.user_id,
              source_table = excluded.source_table,
              source_id = excluded.source_id,
              title = excluded.title,
              content = excluded.content
            """,
            (
                doc_id,
                user_id,
                "weekly_summary",
                f"{user_id}_{end.isoformat()}",
                f"{start.isoformat()} 至 {end.isoformat()} 周报",
                json.dumps(summary, ensure_ascii=False),
            ),
        )
        conn.commit()
        return summary


def export_learning_log(
    user_id: str = "user_mom",
    lesson_date: str | None = None,
    export_format: str = "markdown",
) -> dict[str, Any]:
    lesson_date = lesson_date or today_iso()
    init_db()
    lesson = get_today_lesson(user_id, lesson_date)
    review = get_learning_review(user_id, lesson_date)
    state = get_user_state(user_id)
    with connect() as conn:
        progress = row_to_dict(
            conn.execute(
                """
                SELECT *
                FROM daily_progress
                WHERE user_id = ? AND lesson_asset_id = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user_id, lesson["lesson_asset_id"]),
            ).fetchone()
        )
        errors = rows_to_dicts(
            conn.execute(
                "SELECT * FROM error_records WHERE user_id = ? AND lesson_asset_id = ? ORDER BY created_at",
                (user_id, lesson["lesson_asset_id"]),
            ).fetchall()
        )
        difficulties = rows_to_dicts(
            conn.execute(
                "SELECT * FROM difficulty_records WHERE user_id = ? AND lesson_asset_id = ? ORDER BY created_at",
                (user_id, lesson["lesson_asset_id"]),
            ).fetchall()
        )

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    if export_format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["section", "key", "value"])
        writer.writerow(["lesson", "date", lesson_date])
        writer.writerow(["lesson", "theme", lesson.get("theme")])
        writer.writerow(["lesson", "objectives", "；".join(lesson.get("objectives", []))])
        writer.writerow(["progress", "summary", (progress or {}).get("generated_summary")])
        writer.writerow(["review", "summary", (review or {}).get("human_readable_summary")])
        for item in lesson.get("vocabulary", []):
            writer.writerow(["word", item.get("word"), item.get("meaning")])
        for error in errors:
            writer.writerow(["error", error.get("item_id"), error.get("context")])
        for difficulty in difficulties:
            writer.writerow(["difficulty", difficulty.get("module_type"), difficulty.get("description")])
        content = buffer.getvalue()
        file_path = EXPORT_DIR / f"{user_id}_{lesson_date}_learning_log.csv"
    else:
        content = "\n".join(
            [
                f"# {lesson_date} 学习记录",
                "",
                f"- 用户：{(state.get('user') or {}).get('nickname', user_id)}",
                f"- 主题：{lesson.get('theme')}",
                f"- 学习目标：{'；'.join(lesson.get('objectives', []))}",
                f"- 学习总结：{(progress or {}).get('generated_summary') or '尚未完成'}",
                f"- 复盘：{(review or {}).get('human_readable_summary') or '尚未生成'}",
                "",
                "## 单词",
                *[f"- {item.get('word')} {item.get('phonetic', '')}：{item.get('meaning')}" for item in lesson.get("vocabulary", [])],
                "",
                "## 错题",
                *([f"- {error.get('context')}" for error in errors] or ["- 无"]),
                "",
                "## 难点",
                *([f"- {difficulty.get('description')}" for difficulty in difficulties] or ["- 无"]),
            ]
        )
        file_path = EXPORT_DIR / f"{user_id}_{lesson_date}_learning_log.md"
    file_path.write_text(content, encoding="utf-8")
    return {
        "status": "ok",
        "format": export_format,
        "path": path_for_record(file_path),
        "content": content,
    }


def debug_modules() -> dict[str, Any]:
    init_db()
    lesson_asset_id = generate_and_save_today("user_mom", today_iso())
    lesson = get_today_lesson("user_mom", today_iso())
    with connect() as conn:
        tables = [
            "users",
            "local_login_accounts",
            "learning_profiles",
            "learning_status",
            "curriculum_route_items",
            "teaching_knowledge_assets",
            "lesson_draft_workspaces",
            "lesson_draft_snapshots",
            "lesson_json_assets",
            "learning_review_assets",
            "admin_feedback_logs",
            "daily_progress",
            "error_records",
            "difficulty_records",
            "rag_documents",
            "debug_events",
        ]
        counts = {
            table: conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
            for table in tables
        }
        log_debug(conn, "debug", "info", "module debug completed", {"lesson_asset_id": lesson_asset_id})
        conn.commit()
    return {
        "status": "passed",
        "db_path": str(DB_PATH),
        "lesson_asset_id": lesson_asset_id,
        "lesson_theme": lesson.get("theme"),
        "counts": counts,
    }
