PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  user_id TEXT PRIMARY KEY,
  nickname TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'learner',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_users (
  admin_id TEXT PRIMARY KEY,
  nickname TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS local_login_accounts (
  username TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(user_id),
  role TEXT NOT NULL DEFAULT 'learner',
  password_sha256 TEXT NOT NULL,
  remember_enabled INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at TEXT
);

CREATE TABLE IF NOT EXISTS local_auth_sessions (
  session_token TEXT PRIMARY KEY,
  login_account TEXT NOT NULL REFERENCES local_login_accounts(username),
  role TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT NOT NULL,
  revoked_at TEXT
);

CREATE TABLE IF NOT EXISTS learning_profiles (
  user_id TEXT PRIMARY KEY REFERENCES users(user_id),
  age_band TEXT,
  occupation TEXT,
  english_foundation TEXT,
  goal TEXT,
  daily_minutes INTEGER,
  interest_preferences TEXT,
  scenario_preferences TEXT,
  visual_preferences TEXT,
  pronunciation_preference TEXT,
  cefr_stage TEXT,
  admin_note TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_status (
  user_id TEXT PRIMARY KEY REFERENCES users(user_id),
  learning_days INTEGER NOT NULL DEFAULT 0,
  current_stage TEXT NOT NULL DEFAULT 'starter',
  overall_level TEXT NOT NULL DEFAULT 'zero_base',
  streak_days INTEGER NOT NULL DEFAULT 0,
  last_learning_date TEXT,
  weak_summary TEXT,
  next_suggestion TEXT,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS curriculum_stages (
  stage_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  goal TEXT,
  pass_criteria TEXT,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_points (
  knowledge_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  description TEXT,
  stage_id TEXT REFERENCES curriculum_stages(stage_id),
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS scenario_modules (
  scenario_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  priority INTEGER NOT NULL DEFAULT 100
);

CREATE TABLE IF NOT EXISTS scenario_levels (
  scenario_level_id TEXT PRIMARY KEY,
  scenario_id TEXT NOT NULL REFERENCES scenario_modules(scenario_id),
  level_code TEXT NOT NULL,
  goal TEXT,
  vocabulary_scope TEXT,
  sentence_scope TEXT,
  pass_criteria TEXT,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS curriculum_route_items (
  route_item_id TEXT PRIMARY KEY,
  stage_id TEXT NOT NULL REFERENCES curriculum_stages(stage_id),
  knowledge_id TEXT REFERENCES knowledge_points(knowledge_id),
  scenario_level_id TEXT REFERENCES scenario_levels(scenario_level_id),
  prerequisite_item_id TEXT,
  recommended_order INTEGER NOT NULL,
  target_minutes INTEGER NOT NULL DEFAULT 10,
  objective TEXT
);

CREATE TABLE IF NOT EXISTS user_knowledge_progress (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  knowledge_id TEXT NOT NULL REFERENCES knowledge_points(knowledge_id),
  status TEXT NOT NULL DEFAULT 'not_started',
  last_studied_at TEXT,
  mastery_score REAL NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, knowledge_id)
);

CREATE TABLE IF NOT EXISTS user_scenario_progress (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  scenario_id TEXT NOT NULL REFERENCES scenario_modules(scenario_id),
  current_level_code TEXT NOT NULL DEFAULT 'intro',
  status TEXT NOT NULL DEFAULT 'not_started',
  last_studied_at TEXT,
  next_level_code TEXT,
  PRIMARY KEY (user_id, scenario_id)
);

CREATE TABLE IF NOT EXISTS vocabulary_items (
  word_id TEXT PRIMARY KEY,
  word TEXT NOT NULL,
  phonetic TEXT,
  part_of_speech TEXT,
  core_meaning TEXT,
  difficulty TEXT,
  needs_image INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS vocabulary_mastery (
  user_id TEXT NOT NULL REFERENCES users(user_id),
  word_id TEXT NOT NULL REFERENCES vocabulary_items(word_id),
  first_seen_date TEXT,
  review_count INTEGER NOT NULL DEFAULT 0,
  mastery_status TEXT NOT NULL DEFAULT 'new',
  recent_error TEXT,
  next_review_date TEXT,
  PRIMARY KEY (user_id, word_id)
);

CREATE TABLE IF NOT EXISTS vocabulary_mastery_events (
  event_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_asset_id TEXT REFERENCES lesson_json_assets(lesson_asset_id),
  word_id TEXT NOT NULL REFERENCES vocabulary_items(word_id),
  previous_status TEXT,
  selected_status TEXT NOT NULL,
  resulting_status TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS review_queue (
  review_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  item_type TEXT NOT NULL,
  item_id TEXT NOT NULL,
  reason TEXT,
  priority INTEGER NOT NULL DEFAULT 50,
  planned_review_date TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lesson_json_assets (
  lesson_asset_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_date TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  source_provider TEXT NOT NULL,
  generation_run_id TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  validation_status TEXT NOT NULL DEFAULT 'pending',
  human_readable_summary TEXT,
  admin_note TEXT,
  content_hash TEXT NOT NULL,
  lesson_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  published_at TEXT
);

CREATE TABLE IF NOT EXISTS lesson_draft_workspaces (
  draft_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_date TEXT NOT NULL,
  source_generation_run_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending_publish',
  validation_status TEXT NOT NULL DEFAULT 'passed',
  human_readable_summary TEXT,
  admin_note TEXT,
  admin_instruction TEXT,
  draft_json TEXT NOT NULL,
  publish_after TEXT,
  published_lesson_asset_id TEXT REFERENCES lesson_json_assets(lesson_asset_id),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lesson_draft_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  draft_id TEXT NOT NULL REFERENCES lesson_draft_workspaces(draft_id),
  action TEXT NOT NULL,
  admin_id TEXT REFERENCES admin_users(admin_id),
  draft_json TEXT NOT NULL,
  admin_note TEXT,
  admin_instruction TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lesson_json_versions (
  version_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  version_no INTEGER NOT NULL,
  status TEXT NOT NULL,
  lesson_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_plans (
  plan_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  user_id TEXT NOT NULL REFERENCES users(user_id),
  plan_date TEXT NOT NULL,
  theme TEXT NOT NULL,
  objective TEXT,
  estimated_minutes INTEGER,
  difficulty TEXT,
  status TEXT NOT NULL DEFAULT 'draft',
  published_at TEXT
);

CREATE TABLE IF NOT EXISTS lesson_sections (
  section_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  section_type TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lesson_vocabulary (
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  word_id TEXT NOT NULL REFERENCES vocabulary_items(word_id),
  sort_order INTEGER NOT NULL,
  example_sentence TEXT,
  audio_url TEXT,
  image_url TEXT,
  PRIMARY KEY (lesson_asset_id, word_id)
);

CREATE TABLE IF NOT EXISTS text_passages (
  passage_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  title TEXT,
  english_text TEXT,
  chinese_support TEXT,
  difficulty TEXT,
  source_type TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_notes (
  note_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  related_knowledge_id TEXT
);

CREATE TABLE IF NOT EXISTS teaching_knowledge_assets (
  knowledge_asset_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  stage_id TEXT REFERENCES curriculum_stages(stage_id),
  knowledge_id TEXT REFERENCES knowledge_points(knowledge_id),
  asset_type TEXT NOT NULL,
  content_json TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'manual_seed',
  version TEXT NOT NULL DEFAULT '1.0.0',
  status TEXT NOT NULL DEFAULT 'active',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quizzes (
  quiz_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  title TEXT,
  difficulty TEXT,
  pass_score REAL NOT NULL DEFAULT 0.8
);

CREATE TABLE IF NOT EXISTS quiz_questions (
  question_id TEXT PRIMARY KEY,
  quiz_id TEXT NOT NULL REFERENCES quizzes(quiz_id),
  prompt TEXT NOT NULL,
  options_json TEXT NOT NULL,
  answer TEXT NOT NULL,
  explanation TEXT,
  related_word_id TEXT,
  sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS quiz_attempts (
  attempt_id TEXT PRIMARY KEY,
  quiz_id TEXT NOT NULL REFERENCES quizzes(quiz_id),
  user_id TEXT NOT NULL REFERENCES users(user_id),
  score REAL NOT NULL,
  duration_seconds INTEGER,
  completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question_answers (
  answer_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL REFERENCES quiz_attempts(attempt_id),
  question_id TEXT NOT NULL REFERENCES quiz_questions(question_id),
  selected_answer TEXT,
  is_correct INTEGER NOT NULL,
  error_type TEXT
);

CREATE TABLE IF NOT EXISTS daily_progress (
  progress_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  progress_date TEXT NOT NULL,
  completed_sections_json TEXT,
  learning_minutes INTEGER,
  self_rating TEXT,
  generated_summary TEXT,
  admin_note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS difficulty_records (
  difficulty_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_asset_id TEXT,
  module_type TEXT,
  description TEXT,
  system_label TEXT,
  admin_label TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS error_records (
  error_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_asset_id TEXT,
  item_type TEXT,
  item_id TEXT,
  error_type TEXT,
  context TEXT,
  next_review_plan TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_review_assets (
  review_asset_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES users(user_id),
  lesson_asset_id TEXT NOT NULL REFERENCES lesson_json_assets(lesson_asset_id),
  review_date TEXT NOT NULL,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  validation_status TEXT NOT NULL DEFAULT 'pending',
  human_readable_summary TEXT,
  admin_note TEXT,
  review_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_review_versions (
  version_id TEXT PRIMARY KEY,
  review_asset_id TEXT NOT NULL REFERENCES learning_review_assets(review_asset_id),
  version_no INTEGER NOT NULL,
  status TEXT NOT NULL,
  review_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_generation_runs (
  generation_run_id TEXT PRIMARY KEY,
  task_type TEXT NOT NULL,
  provider TEXT NOT NULL,
  model_or_template TEXT NOT NULL,
  template_version TEXT NOT NULL,
  input_summary TEXT,
  output_path TEXT,
  status TEXT NOT NULL,
  duration_ms INTEGER,
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_templates (
  template_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  version TEXT NOT NULL,
  task_type TEXT NOT NULL,
  schema_name TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS lesson_json_validation_results (
  validation_id TEXT PRIMARY KEY,
  lesson_asset_id TEXT,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL,
  warnings_json TEXT,
  errors_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS learning_review_validation_results (
  validation_id TEXT PRIMARY KEY,
  review_asset_id TEXT,
  schema_version TEXT NOT NULL,
  status TEXT NOT NULL,
  warnings_json TEXT,
  errors_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS content_revisions (
  revision_id TEXT PRIMARY KEY,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  original_text TEXT,
  human_readable_text TEXT,
  revised_text TEXT,
  admin_note TEXT,
  reason TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_adjustments (
  adjustment_id TEXT PRIMARY KEY,
  admin_id TEXT NOT NULL REFERENCES admin_users(admin_id),
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  action TEXT NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_notes (
  note_id TEXT PRIMARY KEY,
  admin_id TEXT NOT NULL REFERENCES admin_users(admin_id),
  user_id TEXT REFERENCES users(user_id),
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  admin_note TEXT,
  admin_instruction TEXT,
  admin_revision_note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_feedback_logs (
  feedback_id TEXT PRIMARY KEY,
  admin_id TEXT NOT NULL REFERENCES admin_users(admin_id),
  user_id TEXT REFERENCES users(user_id),
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  feedback_text TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS asset_sources (
  asset_id TEXT PRIMARY KEY,
  asset_type TEXT NOT NULL,
  local_path TEXT,
  source_name TEXT,
  author TEXT,
  source_url TEXT,
  license TEXT,
  generation_params_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS debug_events (
  event_id TEXT PRIMARY KEY,
  module TEXT NOT NULL,
  level TEXT NOT NULL,
  message TEXT NOT NULL,
  detail_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_documents (
  document_id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(user_id),
  source_table TEXT NOT NULL,
  source_id TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_chunks (
  chunk_id TEXT PRIMARY KEY,
  document_id TEXT NOT NULL REFERENCES rag_documents(document_id),
  chunk_text TEXT NOT NULL,
  tags_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rag_embeddings (
  embedding_id TEXT PRIMARY KEY,
  chunk_id TEXT NOT NULL REFERENCES rag_chunks(chunk_id),
  model TEXT,
  dimensions INTEGER,
  embedding_json TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
