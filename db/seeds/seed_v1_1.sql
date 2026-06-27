-- v1.1 test/demo seed data only. Production/local-use initialization must run schema only.

INSERT OR IGNORE INTO users (user_id, nickname, role, status)
VALUES ('user_mom', 'Vi', 'learner', 'active');

INSERT OR IGNORE INTO users (user_id, nickname, role, status)
VALUES ('user_admin_1', 'Admin_1', 'learner', 'active');

UPDATE users
SET role = 'learner', status = 'active'
WHERE user_id = 'user_admin_1';

INSERT OR IGNORE INTO admin_users (admin_id, nickname, status)
VALUES ('admin_xly', '管理员', 'active');

INSERT OR IGNORE INTO admin_users (admin_id, nickname, status)
VALUES ('AdminXLY', 'Admin_1', 'active');

INSERT OR IGNORE INTO local_login_accounts (
  username, user_id, role, password_sha256, remember_enabled, status
) VALUES (
  'admin_xly',
  NULL,
  'admin',
  'dbee4affba20964d8700d6aa66c1c8356c7b08ed2b2852744318474d8e0148f7',
  1,
  'active'
);

INSERT OR IGNORE INTO local_login_accounts (
  username, user_id, role, password_sha256, remember_enabled, status
) VALUES (
  'AdminXLY',
  'user_admin_1',
  'admin',
  '84d1f39e22ed5d1dda6a3d87029f32a6671f6d40b33f3f3ab255c04fdbe8aa92',
  1,
  'active'
);

UPDATE local_login_accounts
SET user_id = 'user_admin_1',
    role = 'admin',
    remember_enabled = 1,
    status = 'active'
WHERE username = 'AdminXLY';

INSERT OR IGNORE INTO local_login_accounts (
  username, user_id, role, password_sha256, remember_enabled, status
) VALUES (
  'ViZhang',
  'user_mom',
  'learner',
  '84d1f39e22ed5d1dda6a3d87029f32a6671f6d40b33f3f3ab255c04fdbe8aa92',
  1,
  'active'
);

INSERT OR IGNORE INTO learning_profiles (
  user_id, age_band, occupation, english_foundation, goal, daily_minutes,
  interest_preferences, scenario_preferences, visual_preferences,
  pronunciation_preference, cefr_stage, admin_note
) VALUES (
  'user_mom', 'middle_age', 'bank_leader', 'near_zero',
  '从零开始建立英语发音、音标、音节和基础拼读能力，再进入问候、自我介绍和银行常用表达。',
  30,
  '潮流玩具感、精致、轻松、不幼稚',
  '问候,自我介绍,银行接待,会议表达,日常购物',
  '青绿色主色、珊瑚强调、暖黄色徽章',
  'american',
  'pre_a1',
  '首位用户，先以低负担和稳定完成为目标。'
);

INSERT OR IGNORE INTO learning_profiles (
  user_id, age_band, occupation, english_foundation, goal, daily_minutes,
  interest_preferences, scenario_preferences, visual_preferences,
  pronunciation_preference, cefr_stage, admin_note
) VALUES (
  'user_admin_1', '25', 'master_student', 'ielts_7_0',
  '以雅思 7.0 为基础，继续提升学术表达、职场沟通、复杂阅读和高质量口语输出。',
  30,
  '学术英语,职场表达,科技与商业话题,高效复盘',
  '学术讨论,面试表达,会议表达,银行业务,跨文化沟通',
  '清爽、专业、低噪音、适合高阶学习者',
  'american',
  'b2_c1',
  '测试管理员账号的学习者画像：25 岁，硕士研究生，雅思 7.0 水平。'
);

INSERT OR IGNORE INTO learning_status (
  user_id, learning_days, current_stage, overall_level, streak_days,
  last_learning_date, weak_summary, next_suggestion
) VALUES (
  'user_mom', 0, 'starter', 'zero_base', 0, NULL,
  '尚未开始系统学习',
  '从音标和基础拼读开始，控制在 30 分钟。'
);

INSERT OR IGNORE INTO learning_status (
  user_id, learning_days, current_stage, overall_level, streak_days,
  last_learning_date, weak_summary, next_suggestion
) VALUES (
  'user_admin_1', 0, 'advanced', 'ielts_7_0', 0, NULL,
  '尚未开始本系统内学习',
  '从高阶表达、复杂阅读和口语输出诊断开始。'
);

INSERT OR IGNORE INTO curriculum_stages (stage_id, name, goal, pass_criteria, sort_order)
VALUES
  ('stage_starter', '入门阶段', '建立英语学习信心，掌握最基础问候和自我介绍。', '能完成 3 个基础场景的入门表达。', 1),
  ('stage_basic', '初级阶段', '能用简单句完成日常生活和部分工作场景表达。', '能完成 5 个场景的初级表达。', 2);

INSERT OR IGNORE INTO knowledge_points (knowledge_id, name, category, description, stage_id, sort_order)
VALUES
  ('kp_phonics_intro', '音标和音节入门', 'phonics', '认识 /iː/ 和 /ɪ/，建立音标、音节和拼读意识。', 'stage_starter', 0),
  ('kp_greeting_words', '基础问候词', 'vocabulary', 'hello, hi, nice 等问候词。', 'stage_starter', 1),
  ('kp_i_am', 'I am 句型', 'sentence_pattern', '用 I am 介绍自己。', 'stage_starter', 2),
  ('kp_be_verb_intro', 'be 动词入门', 'grammar', '认识 am/is/are 的最基础用法。', 'stage_starter', 3);

INSERT OR IGNORE INTO scenario_modules (scenario_id, name, description, priority)
VALUES
  ('scenario_phonics', '音标拼读', '音标、音节和基础拼读。', 0),
  ('scenario_greeting', '问候', '见面、打招呼、简单寒暄。', 1),
  ('scenario_self_intro', '自我介绍', '介绍自己的姓名、职业和身份。', 2),
  ('scenario_bank_reception', '银行接待', '银行场景中的基础接待表达。', 3);

INSERT OR IGNORE INTO scenario_levels (
  scenario_level_id, scenario_id, level_code, goal, vocabulary_scope,
  sentence_scope, pass_criteria, sort_order
) VALUES
  ('sl_phonics_intro', 'scenario_phonics', 'intro', '认识 /iː/ 和 /ɪ/，能听和读出 seat / sit 的差别。', '/iː/, /ɪ/, see, sit, seat', '音标 -> 音节 -> 单词。', '能区分长短元音并完成 3 道基础题。', 1),
  ('sl_greeting_intro', 'scenario_greeting', 'intro', '会说你好和很高兴见到你。', 'hello, nice, meet', 'Hello. Nice to meet you.', '能看懂并选对 2 个问候表达。', 1),
  ('sl_self_intro_intro', 'scenario_self_intro', 'intro', '会用 I am 介绍姓名和职业。', 'I, am, banker', 'I am ...', '能完成一句自我介绍。', 1),
  ('sl_bank_intro', 'scenario_bank_reception', 'intro', '认识银行接待基础问候。', 'welcome, bank, help', 'Welcome. How can I help?', '能识别银行接待问候句。', 1);

INSERT OR IGNORE INTO curriculum_route_items (
  route_item_id, stage_id, knowledge_id, scenario_level_id,
  prerequisite_item_id, recommended_order, target_minutes, objective
) VALUES
  ('route_000', 'stage_starter', 'kp_phonics_intro', 'sl_phonics_intro', NULL, 0, 30, '认识第一组音标和音节。'),
  ('route_001', 'stage_starter', 'kp_greeting_words', 'sl_greeting_intro', 'route_000', 1, 30, '学会基础问候。'),
  ('route_002', 'stage_starter', 'kp_i_am', 'sl_self_intro_intro', 'route_001', 2, 30, '学会用 I am 介绍自己。'),
  ('route_003', 'stage_starter', 'kp_be_verb_intro', 'sl_bank_intro', 'route_002', 3, 30, '认识银行接待中的基础句。');

INSERT OR IGNORE INTO user_knowledge_progress (user_id, knowledge_id, status, mastery_score)
VALUES
  ('user_mom', 'kp_phonics_intro', 'not_started', 0),
  ('user_mom', 'kp_greeting_words', 'not_started', 0),
  ('user_mom', 'kp_i_am', 'not_started', 0),
  ('user_mom', 'kp_be_verb_intro', 'not_started', 0),
  ('user_admin_1', 'kp_phonics_intro', 'not_started', 0),
  ('user_admin_1', 'kp_greeting_words', 'not_started', 0),
  ('user_admin_1', 'kp_i_am', 'not_started', 0),
  ('user_admin_1', 'kp_be_verb_intro', 'not_started', 0);

INSERT OR IGNORE INTO user_scenario_progress (user_id, scenario_id, current_level_code, status, next_level_code)
VALUES
  ('user_mom', 'scenario_phonics', 'intro', 'not_started', 'intro'),
  ('user_mom', 'scenario_greeting', 'intro', 'not_started', 'intro'),
  ('user_mom', 'scenario_self_intro', 'intro', 'not_started', 'intro'),
  ('user_mom', 'scenario_bank_reception', 'intro', 'not_started', 'intro'),
  ('user_admin_1', 'scenario_phonics', 'intro', 'not_started', 'intro'),
  ('user_admin_1', 'scenario_greeting', 'intro', 'not_started', 'intro'),
  ('user_admin_1', 'scenario_self_intro', 'intro', 'not_started', 'intro'),
  ('user_admin_1', 'scenario_bank_reception', 'intro', 'not_started', 'intro');

INSERT OR IGNORE INTO content_templates (template_id, name, version, task_type, schema_name, enabled)
VALUES
  ('tpl_lesson_plan_v1', 'starter_lesson_plan_template', '1.0.0', 'lesson_plan', 'lesson_plan_json', 1),
  ('tpl_learning_review_v1', 'starter_learning_review_template', '1.0.0', 'learning_review', 'learning_review_json', 1);

INSERT OR IGNORE INTO teaching_knowledge_assets (
  knowledge_asset_id, title, stage_id, knowledge_id, asset_type, content_json, source_type, version, status
) VALUES (
  'kb_phonics_001_i_long_i_short',
  '音标第一课：/iː/ 和 /ɪ/',
  'stage_starter',
  'kp_phonics_intro',
  'phonics_lesson',
  '{"phonemes":[{"symbol":"/iː/","name":"长衣音","mouth_shape":"嘴角向两边拉，声音拉长，像中文的衣但更长。","examples":["see","seat","tea"]},{"symbol":"/ɪ/","name":"短衣音","mouth_shape":"嘴巴放松，声音短促，不要拖长。","examples":["sit","it","this"]}],"syllable_note":"一个英语单词通常由一个或多个音节组成。今天先听一个音节里的元音长短差别。","teaching_steps":["先听 /iː/ 和 /ɪ/ 的长短区别。","再读 see /siː/ 和 sit /sɪt/。","最后用短对话练习 I see it."]}',
  'manual_seed',
  '1.0.0',
  'active'
);
