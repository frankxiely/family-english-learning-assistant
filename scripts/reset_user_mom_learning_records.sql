PRAGMA foreign_keys = ON;

BEGIN TRANSACTION;

CREATE TEMP TABLE reset_lesson_ids AS
SELECT lesson_asset_id
FROM lesson_json_assets
WHERE user_id = 'user_mom';

CREATE TEMP TABLE reset_draft_ids AS
SELECT draft_id
FROM lesson_draft_workspaces
WHERE user_id = 'user_mom';

CREATE TEMP TABLE reset_review_ids AS
SELECT review_asset_id
FROM learning_review_assets
WHERE user_id = 'user_mom';

CREATE TEMP TABLE reset_generation_ids AS
SELECT generation_run_id AS generation_run_id
FROM lesson_json_assets
WHERE user_id = 'user_mom' AND generation_run_id IS NOT NULL
UNION
SELECT source_generation_run_id
FROM lesson_draft_workspaces
WHERE user_id = 'user_mom' AND source_generation_run_id IS NOT NULL;

CREATE TEMP TABLE reset_quiz_ids AS
SELECT quiz_id
FROM quizzes
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);

CREATE TEMP TABLE reset_attempt_ids AS
SELECT attempt_id
FROM quiz_attempts
WHERE user_id = 'user_mom'
   OR quiz_id IN (SELECT quiz_id FROM reset_quiz_ids);

CREATE TEMP TABLE reset_rag_doc_ids AS
SELECT document_id
FROM rag_documents
WHERE user_id = 'user_mom';

DELETE FROM local_auth_sessions
WHERE login_account IN (
  SELECT username FROM local_login_accounts WHERE user_id = 'user_mom'
);

DELETE FROM rag_embeddings
WHERE chunk_id IN (
  SELECT chunk_id FROM rag_chunks WHERE document_id IN (SELECT document_id FROM reset_rag_doc_ids)
);
DELETE FROM rag_chunks
WHERE document_id IN (SELECT document_id FROM reset_rag_doc_ids);
DELETE FROM rag_documents
WHERE document_id IN (SELECT document_id FROM reset_rag_doc_ids);

DELETE FROM learning_review_validation_results
WHERE review_asset_id IN (SELECT review_asset_id FROM reset_review_ids);
DELETE FROM learning_review_versions
WHERE review_asset_id IN (SELECT review_asset_id FROM reset_review_ids);
DELETE FROM learning_review_assets
WHERE review_asset_id IN (SELECT review_asset_id FROM reset_review_ids);

DELETE FROM question_answers
WHERE attempt_id IN (SELECT attempt_id FROM reset_attempt_ids)
   OR question_id IN (
      SELECT question_id FROM quiz_questions WHERE quiz_id IN (SELECT quiz_id FROM reset_quiz_ids)
   );
DELETE FROM quiz_attempts
WHERE attempt_id IN (SELECT attempt_id FROM reset_attempt_ids);
DELETE FROM quiz_questions
WHERE quiz_id IN (SELECT quiz_id FROM reset_quiz_ids);
DELETE FROM quizzes
WHERE quiz_id IN (SELECT quiz_id FROM reset_quiz_ids);

DELETE FROM lesson_json_validation_results
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM daily_progress
WHERE user_id = 'user_mom'
   OR lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM difficulty_records
WHERE user_id = 'user_mom'
   OR lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM error_records
WHERE user_id = 'user_mom'
   OR lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);

DELETE FROM vocabulary_mastery_events
WHERE user_id = 'user_mom'
   OR lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM review_queue
WHERE user_id = 'user_mom';
DELETE FROM vocabulary_mastery
WHERE user_id = 'user_mom';

DELETE FROM lesson_draft_snapshots
WHERE draft_id IN (SELECT draft_id FROM reset_draft_ids);
DELETE FROM admin_notes
WHERE user_id = 'user_mom'
   OR target_id IN (SELECT draft_id FROM reset_draft_ids)
   OR target_id IN (SELECT lesson_asset_id FROM reset_lesson_ids)
   OR target_id IN (SELECT review_asset_id FROM reset_review_ids);
DELETE FROM admin_feedback_logs
WHERE user_id = 'user_mom'
   OR target_id IN (SELECT draft_id FROM reset_draft_ids)
   OR target_id IN (SELECT lesson_asset_id FROM reset_lesson_ids)
   OR target_id IN (SELECT review_asset_id FROM reset_review_ids);
DELETE FROM admin_adjustments
WHERE target_id IN (SELECT draft_id FROM reset_draft_ids)
   OR target_id IN (SELECT lesson_asset_id FROM reset_lesson_ids)
   OR target_id IN (SELECT review_asset_id FROM reset_review_ids);
DELETE FROM content_revisions
WHERE target_id IN (SELECT draft_id FROM reset_draft_ids)
   OR target_id IN (SELECT lesson_asset_id FROM reset_lesson_ids)
   OR target_id IN (SELECT review_asset_id FROM reset_review_ids);

DELETE FROM daily_plans
WHERE user_id = 'user_mom'
   OR lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM lesson_sections
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM lesson_vocabulary
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM text_passages
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM knowledge_notes
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);
DELETE FROM lesson_json_versions
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);

DELETE FROM lesson_draft_workspaces
WHERE draft_id IN (SELECT draft_id FROM reset_draft_ids);
DELETE FROM lesson_json_assets
WHERE lesson_asset_id IN (SELECT lesson_asset_id FROM reset_lesson_ids);

DELETE FROM content_generation_runs
WHERE generation_run_id IN (SELECT generation_run_id FROM reset_generation_ids);

DELETE FROM debug_events
WHERE detail_json LIKE '%user_mom%'
   OR detail_json LIKE '%lesson_user_mom%';

UPDATE learning_status
SET learning_days = 0,
    streak_days = 0,
    last_learning_date = NULL,
    weak_summary = '尚未开始系统学习',
    next_suggestion = '从音标和基础拼读开始，控制在 30 分钟。',
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 'user_mom';

UPDATE user_knowledge_progress
SET status = 'not_started',
    last_studied_at = NULL,
    mastery_score = 0
WHERE user_id = 'user_mom';

UPDATE user_scenario_progress
SET status = 'not_started',
    last_studied_at = NULL,
    current_level_code = 'intro',
    next_level_code = 'intro'
WHERE user_id = 'user_mom';

COMMIT;
