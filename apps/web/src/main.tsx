import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Button,
  Card,
  Col,
  ConfigProvider,
  Input as AntInput,
  Layout,
  List,
  Row,
  Space,
  Statistic,
  Tag,
  Typography
} from "antd";
import {
  Button as MobileButton,
  Checkbox as MobileCheckbox,
  Input as MobileInput,
  TextArea as MobileTextArea
} from "antd-mobile";
import "antd/dist/reset.css";
import "./styles.css";

type WordStatus = "known" | "fuzzy" | "unknown";

type Session = {
  login_account: string;
  username: string;
  user_id: string;
  role: string;
  nickname?: string;
  remember: boolean;
  session_token?: string;
  expires_at?: string;
};

type WordItem = {
  word: string;
  phonetic?: string;
  part_of_speech?: string;
  meaning?: string;
  needs_image?: boolean;
  image_hint?: string;
  image_url?: string;
  learning_role?: "new" | "review";
  is_review?: boolean;
  review_reason?: string;
};

type QuizQuestion = {
  question_id?: string;
  question_type?: string;
  prompt: string;
  options: string[];
  answer: string;
  explanation?: string;
  audio_text?: string;
  audio_ref?: string;
};

type AudioAsset = {
  audio_id: string;
  target_type?: string;
  target_ref?: string;
  text?: string;
  provider?: string;
  local_url?: string | null;
  rate?: number;
  pitch?: number;
  style?: string;
  emphasis_words?: string[];
  pause_after_ms?: number | null;
};

type Lesson = {
  lesson_asset_id?: string;
  lesson_date?: string;
  theme?: string;
  human_readable_summary?: string;
  admin_note?: string | null;
  objectives?: string[];
  estimated_minutes?: number;
  sections?: Array<{ type: string; title: string; content?: string }>;
  vocabulary?: WordItem[];
  passage?: {
    title?: string;
    english_text?: string;
    chinese_support?: string;
    lines?: Array<{ role?: string; text: string; translation?: string; audio_ref?: string; slow_audio_ref?: string }>;
    difficult_words?: Array<{ word: string; meaning: string }>;
  };
  knowledge_note?: { title?: string; content?: string };
  quiz?: { title?: string; questions: QuizQuestion[] };
  completion_encouragement?: {
    learned_word?: string;
    message_zh?: string;
    quote_en?: string;
    quote_zh?: string;
    quote_author?: string;
    button_text?: string;
  };
  home_encouragement?: {
    quote_en?: string;
    quote_zh?: string;
  };
  progress_summary?: {
    route_module_label?: string;
    main_knowledge_label?: string;
    passage_module_label?: string;
  };
  audio_assets?: AudioAsset[];
  teaching_knowledge_id?: string;
};

type Review = {
  human_readable_summary?: string;
  mastered_words?: string[];
  weak_words?: string[];
  difficulty_points?: string[];
  next_day_adjustment?: string;
  quiz_score?: number;
};

type LearningState = {
  user?: { nickname?: string };
  status?: { learning_days?: number; streak_days?: number; weak_summary?: string; next_suggestion?: string };
  vocabulary_mastery?: Array<{ word?: string; mastery_status?: string }>;
  completed_quiz_questions?: number;
};

type RouteMapItem = {
  route_item_id?: string;
  day_number?: number;
  theme?: string;
  knowledge_name?: string;
  scenario_name?: string;
  level_code?: string;
  target_minutes?: number;
  status?: "completed" | "active" | "next" | "locked";
  mastery_score?: number;
  route_module_label?: string;
  main_knowledge_label?: string;
  passage_module_label?: string;
};

type LessonProgress = {
  lesson_asset_id?: string;
  lesson_date?: string;
  lessonStep: number;
  passagePage: 0 | 1;
  passageCardPage: number;
  knowledgePage: number;
  wordIndex: number;
  quizIndex: number;
  hasStarted: boolean;
  completed?: boolean;
  updated_at?: string;
};

type AdminUser = {
  user_id: string;
  nickname?: string;
  login_account?: string;
  occupation?: string;
  english_foundation?: string;
  learning_days?: number;
  current_stage?: string;
  last_learning_date?: string;
  pending_draft_count?: number;
};

type DraftWorkspace = {
  draft_id: string;
  user_id: string;
  lesson_date: string;
  status: string;
  admin_note?: string | null;
  admin_instruction?: string | null;
  human_readable_summary?: string;
  draft_json: Lesson;
  updated_at?: string;
};

type LearningOverview = {
  learning_days?: number;
  streak_days?: number;
  current_stage?: string;
  overall_level?: string;
  last_learning_date?: string | null;
  weak_summary?: string | null;
  next_suggestion?: string | null;
  vocabulary_estimate?: number;
  mastered_vocabulary?: number;
  needs_review_vocabulary?: number;
  recent_reviews?: Array<{
    review_asset_id?: string;
    review_date?: string;
    human_readable_summary?: string;
    quiz_score?: number;
    weak_words?: string[];
  }>;
  knowledge_progress?: Array<{ name?: string; status?: string; mastery_score?: number }>;
};

type UserWorkspace = {
  user?: { user_id?: string; nickname?: string; role?: string; status?: string };
  profile?: Record<string, string | number | null>;
  login_accounts?: Array<{ login_account?: string; role?: string; status?: string; last_login_at?: string | null }>;
  latest_draft?: DraftWorkspace | null;
  published_today?: { lesson_asset_id?: string; lesson_date?: string; status?: string; published_at?: string } | null;
  learning_overview?: LearningOverview;
  feedback_logs?: Array<{ feedback_id?: string; feedback_text?: string; created_at?: string }>;
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");

function normalizeBasePath(rawBase: string) {
  const base = rawBase.trim();
  if (!base || base === "/") return "";
  return `/${base.replace(/^\/+|\/+$/g, "")}`;
}

const APP_BASE_PATH = normalizeBasePath(import.meta.env.BASE_URL ?? "/");

function apiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

function frontendAssetUrl(path: string) {
  if (/^(https?:)?\/\//i.test(path) || path.startsWith("data:") || path.startsWith("blob:")) {
    return path;
  }
  const base = import.meta.env.BASE_URL ?? "/";
  return `${base.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

function runtimeAssetUrl(path?: string | null) {
  if (!path) return "";
  if (/^(https?:)?\/\//i.test(path) || path.startsWith("data:") || path.startsWith("blob:")) {
    return path;
  }
  if (path.startsWith("/generated/") && API_BASE_URL) {
    return `${API_BASE_URL}${path}`;
  }
  return frontendAssetUrl(path);
}

function appPathFromLocation() {
  const pathname = window.location.pathname;
  if (APP_BASE_PATH && pathname === APP_BASE_PATH) return "/";
  if (APP_BASE_PATH && pathname.startsWith(`${APP_BASE_PATH}/`)) {
    return pathname.slice(APP_BASE_PATH.length) || "/";
  }
  return pathname;
}

function browserPathForAppPath(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${APP_BASE_PATH}${normalizedPath}`;
}

const fallbackLesson: Lesson = {
  theme: "音标第一课：/iː/ 和 /ɪ/",
  human_readable_summary: "今天用 30 分钟学习第一组音标，先把长音和短音听清、读准。",
  estimated_minutes: 30,
  objectives: ["认识 /iː/ 和 /ɪ/", "读出 see / sit / seat", "完成 4 道小测试"],
  sections: [
    { type: "preview", title: "今日目标", content: "今天只学一组声音：长 /iː/ 和短 /ɪ/。" },
    { type: "system_knowledge", title: "知识讲解", content: "/iː/ 要拉长，/ɪ/ 要短促。先听差别，再拼单词。" }
  ],
  vocabulary: [
    { word: "see", phonetic: "/siː/", part_of_speech: "verb", meaning: "看见", needs_image: true },
    { word: "sit", phonetic: "/sɪt/", part_of_speech: "verb", meaning: "坐", needs_image: true }
  ],
  passage: {
    title: "I see it",
    english_text: "Teacher: See the seat.\nVi: I see it.\nTeacher: Sit on the seat.\nVi: I sit.",
    chinese_support: "老师：看这个座位。\nVi：我看见了。\n老师：坐在座位上。\nVi：我坐下。",
    lines: [
      { role: "Teacher", text: "See the seat.", translation: "看这个座位。" },
      { role: "Vi", text: "I see it.", translation: "我看见了。" },
      { role: "Teacher", text: "Sit on the seat.", translation: "坐在座位上。" },
      { role: "Vi", text: "I sit.", translation: "我坐下。" }
    ],
    difficult_words: [
      { word: "the", meaning: "这个；那个" },
      { word: "on", meaning: "在……上" }
    ]
  },
  knowledge_note: {
    title: "知识讲解：音标、音节和拼读",
    content: "/iː/ 是长音，see /siː/；/ɪ/ 是短音，sit /sɪt/。一个音节通常有一个核心元音。"
  },
  quiz: {
    title: "音标小测试",
    questions: [{ prompt: "/iː/ 是什么声音？", options: ["长音", "短音", "不发音"], answer: "长音" }]
  },
  completion_encouragement: {
    learned_word: "see",
    message_zh: "今天你已经认识了 see，这就是稳稳的一步。",
    quote_en: "It always seems impossible until it's done.",
    quote_zh: "在事情完成之前，一切都看似不可能。",
    quote_author: "Nelson Mandela",
    button_text: "我真行"
  },
  home_encouragement: {
    quote_en: "The journey of a thousand miles begins with one step.",
    quote_zh: "千里之行，始于足下。"
  },
  progress_summary: {
    route_module_label: "音标和音节入门",
    main_knowledge_label: "/iː/ 和 /ɪ/",
    passage_module_label: "日常对话"
  }
};

const ADMIN_AVATAR_PATH = frontendAssetUrl("/assets/avatars/roles/admin-male.png");

function readStoredSession(key: string): Session | null {
  const raw = localStorage.getItem(key);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<Session>;
    const displayUsername = parsed.nickname || parsed.username || "Vi";
    return {
      login_account: parsed.login_account || parsed.username || "",
      username: displayUsername,
      user_id: parsed.user_id || "user_mom",
      role: parsed.role || "learner",
      nickname: displayUsername,
      remember: parsed.remember ?? true,
      session_token: parsed.session_token,
      expires_at: parsed.expires_at
    };
  } catch {
    return null;
  }
}

function readSession(): Session | null {
  return readStoredSession("momo_session");
}

function go(path: string) {
  window.history.pushState({}, "", browserPathForAppPath(path));
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function MomoLineLogo() {
  return (
    <svg className="line-logo" aria-hidden="true" viewBox="0 0 64 64">
      <path className="line-logo-page" d="M14 20c8 0 14 3 18 8 4-5 10-8 18-8v27c-8 0-14 2-18 6-4-4-10-6-18-6V20Z" />
      <path className="line-logo-bubble" d="M20 14h24c5 0 9 4 9 9v8c0 5-4 9-9 9h-9l-8 7 1-7h-8c-5 0-9-4-9-9v-8c0-5 4-9 9-9Z" />
      <path className="line-logo-m" d="M20 35V23l8 9 8-9v12" />
      <path className="line-logo-star" d="M50 8l2 4 4 2-4 2-2 4-2-4-4-2 4-2 2-4Z" />
    </svg>
  );
}

function App() {
  const [path, setPath] = useState(appPathFromLocation());
  const [session, setSession] = useState<Session | null>(readSession());
  const [adminSession, setAdminSession] = useState<Session | null>(readStoredSession("momo_admin_session"));

  useEffect(() => {
    const listener = () => setPath(appPathFromLocation());
    window.addEventListener("popstate", listener);
    return () => window.removeEventListener("popstate", listener);
  }, []);

  if (path === "/admin") {
    if (!adminSession || adminSession.role !== "admin" || !adminSession.session_token) {
      return (
        <AdminLoginPage
          onLogin={(nextSession) => {
            localStorage.setItem("momo_admin_session", JSON.stringify(nextSession));
            setAdminSession(nextSession);
            if (nextSession.user_id) {
              localStorage.setItem("momo_session", JSON.stringify(nextSession));
              setSession(nextSession);
            }
            go("/admin");
          }}
        />
      );
    }
    return (
      <AdminPage
        session={adminSession}
        onLogout={() => {
          localStorage.removeItem("momo_admin_session");
          setAdminSession(null);
          go("/admin");
        }}
      />
    );
  }

  if (!session) {
    return (
      <LoginPage
        onLogin={(nextSession) => {
          if (nextSession.role === "admin" && !nextSession.user_id) {
            localStorage.removeItem("momo_session");
            localStorage.setItem("momo_admin_session", JSON.stringify(nextSession));
            setAdminSession(nextSession);
            go("/admin");
            return;
          }
          if (nextSession.role === "admin") {
            localStorage.setItem("momo_admin_session", JSON.stringify(nextSession));
            setAdminSession(nextSession);
          }
          localStorage.setItem("momo_session", JSON.stringify(nextSession));
          setSession(nextSession);
          go("/learn");
        }}
      />
    );
  }

  return (
    <LearnPage
      session={session}
      onSessionUpdate={(nextSession) => {
        const mergedSession = { ...session, ...nextSession };
        localStorage.setItem("momo_session", JSON.stringify(mergedSession));
        setSession(mergedSession);
        if (mergedSession.role === "admin") {
          localStorage.setItem("momo_admin_session", JSON.stringify(mergedSession));
          setAdminSession(mergedSession);
        }
      }}
      onLogout={() => {
        localStorage.removeItem("momo_session");
        setSession(null);
        go("/login");
      }}
    />
  );
}

function LoginPage(props: { onLogin: (session: Session) => void }) {
  const remembered = useMemo(() => {
    const raw = localStorage.getItem("momo_login_remember");
    if (!raw) return { login_account: "ViZhang", password: "", remember: true };
    try {
      const parsed = JSON.parse(raw) as { login_account?: string; username?: string; password?: string; remember?: boolean };
      return {
        login_account: parsed.login_account || parsed.username || "ViZhang",
        password: parsed.password || "",
        remember: parsed.remember ?? true
      };
    } catch {
      return { login_account: "ViZhang", password: "", remember: true };
    }
  }, []);
  const [loginAccount, setLoginAccount] = useState(remembered.login_account);
  const [password, setPassword] = useState(remembered.password);
  const [remember, setRemember] = useState(remembered.remember);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    const res = await fetch(apiUrl("/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login_account: loginAccount, password, remember })
    });
    if (!res.ok) {
      setError("账号或密码不正确");
      return;
    }
    const data = await res.json();
    const nextSession = data.session as Session;
    localStorage.setItem("momo_session", JSON.stringify(nextSession));
    if (remember) {
      localStorage.setItem("momo_login_remember", JSON.stringify({ login_account: loginAccount, password, remember }));
    } else {
      localStorage.removeItem("momo_login_remember");
    }
    props.onLogin(nextSession);
  }

  return (
    <main className="auth-shell learner-auth">
      <section className="auth-panel">
        <div className="brand-mark line-brand-mark"><MomoLineLogo /></div>
        <p className="eyebrow">MomoLingo</p>
        <h1>今天继续学一点</h1>
        <p className="muted">登录后开始今天的轻量学习。</p>
        <form onSubmit={submit} className="login-form">
          <label className="mobile-field">
            登录账号
            <MobileInput data-testid="learner-login-account" value={loginAccount} onChange={setLoginAccount} autoComplete="username" />
          </label>
          <label className="mobile-field">
            密码
            <MobileInput
              data-testid="learner-login-password"
              value={password}
              type="password"
              onChange={setPassword}
              autoComplete="current-password"
            />
          </label>
          <label className="check-row">
            <MobileCheckbox checked={remember} onChange={setRemember} />
            记住账号和密码
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <MobileButton data-testid="learner-login-submit" block color="primary" size="large" type="submit">开始学习</MobileButton>
        </form>
        <button className="admin-login-shortcut utility-button" type="button" onClick={() => go("/admin")}>
          管理员登录
        </button>
      </section>
    </main>
  );
}

function AdminLoginPage(props: { onLogin: (session: Session) => void }) {
  const remembered = useMemo(() => {
    const raw = localStorage.getItem("momo_admin_remember");
    if (!raw) return { login_account: "AdminXLY", password: "", remember: true };
    try {
      const parsed = JSON.parse(raw) as { login_account?: string; password?: string; remember?: boolean };
      return {
        login_account: parsed.login_account || "AdminXLY",
        password: "",
        remember: parsed.remember ?? true
      };
    } catch {
      return { login_account: "AdminXLY", password: "", remember: true };
    }
  }, []);
  const [loginAccount, setLoginAccount] = useState(remembered.login_account);
  const [password, setPassword] = useState(remembered.password);
  const [remember, setRemember] = useState(remembered.remember);
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    const res = await fetch(apiUrl("/api/auth/login"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login_account: loginAccount, password, remember })
    });
    if (!res.ok) {
      setError("管理员账号或密码不正确");
      return;
    }
    const data = await res.json();
    const nextSession = data.session as Session;
    if (nextSession.role !== "admin" || !nextSession.session_token) {
      setError("当前账号没有管理员权限");
      return;
    }
    if (remember) {
      localStorage.setItem("momo_admin_remember", JSON.stringify({ login_account: loginAccount, remember }));
    } else {
      localStorage.removeItem("momo_admin_remember");
    }
    props.onLogin(nextSession);
  }

  return (
    <main className="auth-shell admin-auth">
      <section className="auth-panel admin-auth-panel">
        <div className="brand-mark line-brand-mark admin-mark"><MomoLineLogo /></div>
        <p className="eyebrow">Admin</p>
        <h1>管理员登录</h1>
        <p className="muted">后台只允许管理员账号进入。</p>
        <form onSubmit={submit} className="login-form">
          <label className="mobile-field">
            管理员账号
            <MobileInput value={loginAccount} onChange={setLoginAccount} autoComplete="username" />
          </label>
          <label className="mobile-field">
            密码
            <MobileInput
              value={password}
              type="password"
              onChange={setPassword}
              autoComplete="current-password"
            />
          </label>
          <label className="check-row">
            <MobileCheckbox checked={remember} onChange={setRemember} />
            记住管理员账号
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <MobileButton block color="primary" size="large" type="submit">进入后台</MobileButton>
        </form>
      </section>
    </main>
  );
}

function LearnPage(props: { session: Session; onLogout: () => void; onSessionUpdate: (session: Session) => void }) {
  const [lesson, setLesson] = useState<Lesson>(fallbackLesson);
  const [learningState, setLearningState] = useState<LearningState | null>(null);
  const [routeMap, setRouteMap] = useState<RouteMapItem[]>([]);
  const [wordMastery, setWordMastery] = useState<Record<string, WordStatus>>({});
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [selfRating, setSelfRating] = useState("刚好");
  const [difficultyText, setDifficultyText] = useState("");
  const [review, setReview] = useState<Review | null>(null);
  const [notice, setNotice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [learnView, setLearnView] = useState<"home" | "map" | "lesson" | "celebration" | "profile" | "settings">("home");
  const [lessonStep, setLessonStep] = useState(0);
  const [passagePage, setPassagePage] = useState<0 | 1>(0);
  const [passageCardPage, setPassageCardPage] = useState(0);
  const [knowledgePage, setKnowledgePage] = useState(0);
  const [wordIndex, setWordIndex] = useState(0);
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizWrongSelections, setQuizWrongSelections] = useState<Record<string, string>>({});
  const [quizMistakes, setQuizMistakes] = useState<Array<{ prompt: string; selected_answer: string; answer: string; explanation?: string }>>([]);
  const [selectedGloss, setSelectedGloss] = useState<{ word: string; meaning: string } | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [lessonProgress, setLessonProgress] = useState<LessonProgress | null>(null);
  const [displayNameDraft, setDisplayNameDraft] = useState(props.session.nickname || props.session.username || "Vi");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [accountNotice, setAccountNotice] = useState("");
  const [isSavingAccount, setIsSavingAccount] = useState(false);
  const [speakingText, setSpeakingText] = useState("");

  const questions = lesson.quiz?.questions ?? [];
  const quizScorePreview = useMemo(() => {
    if (!questions.length) return 0;
    const correct = questions.filter((q) => answers[q.prompt] === q.answer).length;
    return Math.round((correct / questions.length) * 100);
  }, [answers, questions]);

  useEffect(() => {
    void refreshLearning();
  }, []);

  useEffect(() => {
    setDisplayNameDraft(props.session.nickname || props.session.username || "Vi");
  }, [props.session.nickname, props.session.username]);

  useEffect(() => {
    const next: Record<string, WordStatus> = {};
    (lesson.vocabulary ?? []).forEach((item) => {
      const previous = wordMastery[item.word.toLowerCase()];
      if (previous) next[item.word.toLowerCase()] = previous;
    });
    setWordMastery(next);
  }, [lesson.lesson_asset_id]);

  useEffect(() => {
    const raw = localStorage.getItem(progressStorageKey());
    if (!raw || !lesson.lesson_asset_id) {
      setLessonProgress(null);
      return;
    }
    try {
      const parsed = JSON.parse(raw) as LessonProgress;
      setLessonProgress(parsed.lesson_asset_id === lesson.lesson_asset_id ? parsed : null);
    } catch {
      setLessonProgress(null);
    }
  }, [lesson.lesson_asset_id, props.session.user_id]);

  useEffect(() => {
    if (learnView !== "lesson") return;
    saveLessonProgress();
  }, [learnView, lessonStep, passagePage, passageCardPage, knowledgePage, wordIndex, quizIndex, lesson.lesson_asset_id]);

  async function refreshLearning() {
    const [lessonRes, stateRes, reviewRes, routeRes] = await Promise.all([
      fetch(apiUrl(`/api/learning/today?user_id=${encodeURIComponent(props.session.user_id)}`)),
      fetch(apiUrl(`/api/learning/state?user_id=${encodeURIComponent(props.session.user_id)}`)),
      fetch(apiUrl(`/api/learning/review?user_id=${encodeURIComponent(props.session.user_id)}`)),
      fetch(apiUrl(`/api/learning/route-map?user_id=${encodeURIComponent(props.session.user_id)}`))
    ]);
    if (lessonRes.ok) {
      const data = await lessonRes.json();
      setLesson(data.lesson_json ?? data);
    }
    if (stateRes.ok) setLearningState(await stateRes.json());
    if (reviewRes.ok) {
      const data = await reviewRes.json();
      setReview(data.review_json);
    }
    if (routeRes.ok) {
      const data = await routeRes.json();
      setRouteMap(data.route_map ?? []);
    }
  }

  function speak(text: string, options: { rate?: number; pitch?: number } = {}) {
    if (!("speechSynthesis" in window)) {
      setNotice("当前浏览器没有可用的发音能力。");
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = options.rate ?? 0.86;
    utterance.pitch = options.pitch ?? 1.05;
    setSpeakingText(text);
    utterance.onend = () => setSpeakingText("");
    utterance.onerror = () => setSpeakingText("");
    window.speechSynthesis.speak(utterance);
  }

  function findAudioAssetById(audioId?: string) {
    if (!audioId) return undefined;
    return lesson.audio_assets?.find((asset) => asset.audio_id === audioId);
  }

  function findAudioAsset(targetType: string, targetRef: string) {
    return lesson.audio_assets?.find((asset) => asset.target_type === targetType && asset.target_ref === targetRef);
  }

  function playAudioAssetOrSpeak(
    asset: AudioAsset | undefined,
    fallbackText: string,
    options: { rate?: number; pitch?: number } = {},
  ) {
    const audioUrl = runtimeAssetUrl(asset?.local_url);
    if (audioUrl) {
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
      const audio = new Audio(audioUrl);
      setSpeakingText(asset.text ?? fallbackText);
      audio.onended = () => setSpeakingText("");
      audio.onerror = () => {
        setSpeakingText("");
        speak(fallbackText, options);
      };
      void audio.play().catch(() => speak(fallbackText, options));
      return;
    }
    speak(fallbackText, {
      rate: asset?.rate ?? options.rate,
      pitch: asset?.pitch ?? options.pitch,
    });
  }

  async function playAudioAssetsSequentially(assets: AudioAsset[], fallbackText: string, options: { rate?: number; pitch?: number } = {}) {
    const playableAssets = assets.filter((asset) => runtimeAssetUrl(asset.local_url));
    if (!playableAssets.length || playableAssets.length !== assets.length) {
      speak(fallbackText, options);
      return;
    }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    for (const asset of playableAssets) {
      await new Promise<void>((resolve) => {
        const audio = new Audio(runtimeAssetUrl(asset.local_url));
        setSpeakingText(asset.text ?? fallbackText);
        audio.onended = () => {
          const pauseMs = Number(asset.pause_after_ms ?? 120);
          window.setTimeout(resolve, Number.isFinite(pauseMs) ? pauseMs : 120);
        };
        audio.onerror = () => resolve();
        void audio.play().catch(() => resolve());
      });
    }
    setSpeakingText("");
  }

  async function completeToday() {
    setIsSubmitting(true);
    setNotice("");
    try {
      const payload = {
        lesson_asset_id: lesson.lesson_asset_id,
        completed_sections: ["goal", "phonics", "passage_original", "passage_translation", "knowledge", "quiz", "summary"],
        learning_minutes: lesson.estimated_minutes ?? 30,
        self_rating: selfRating,
        word_mastery: Object.entries(wordMastery).map(([word, status]) => ({ word, status })),
        quiz_answers: questions.map((q) => ({
          prompt: q.prompt,
          selected_answer: answers[q.prompt] ?? quizWrongSelections[q.prompt] ?? "",
        })),
        quiz_mistakes: quizMistakes,
        difficulty_notes: difficultyText.split("\n").map((item) => item.trim()).filter(Boolean)
      };
      const res = await fetch(apiUrl(`/api/learning/complete?user_id=${encodeURIComponent(props.session.user_id)}`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setReview(data.review_json);
      saveLessonProgress({ completed: true, lessonStep: stepLabels.length - 1 });
      setLearnView("celebration");
      await refreshLearning();
    } catch (err) {
      setNotice(`提交失败：${err instanceof Error ? err.message : "未知错误"}`);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function saveDisplayName() {
    if (!props.session.session_token) {
      setAccountNotice("当前登录状态已失效，请重新登录。");
      return;
    }
    setIsSavingAccount(true);
    setAccountNotice("");
    try {
      const res = await fetch(apiUrl("/api/account/display-name"), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${props.session.session_token}`
        },
        body: JSON.stringify({ username: displayNameDraft })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "保存失败");
      props.onSessionUpdate(data.session as Session);
      setAccountNotice("用户名已更新。");
    } catch (err) {
      setAccountNotice(`保存失败：${err instanceof Error ? err.message : "未知错误"}`);
    } finally {
      setIsSavingAccount(false);
    }
  }

  async function savePassword() {
    if (!props.session.session_token) {
      setAccountNotice("当前登录状态已失效，请重新登录。");
      return;
    }
    if (newPassword !== confirmPassword) {
      setAccountNotice("两次输入的新密码不一致。");
      return;
    }
    setIsSavingAccount(true);
    setAccountNotice("");
    try {
      const res = await fetch(apiUrl("/api/account/password"), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${props.session.session_token}`
        },
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "保存失败");
      const rememberedRaw = localStorage.getItem("momo_login_remember");
      if (rememberedRaw) {
        const remembered = JSON.parse(rememberedRaw) as { login_account?: string; password?: string; remember?: boolean };
        if (remembered.login_account === props.session.login_account) {
          localStorage.setItem("momo_login_remember", JSON.stringify({ ...remembered, password: newPassword }));
        }
      }
      const adminRememberedRaw = localStorage.getItem("momo_admin_remember");
      if (adminRememberedRaw) {
        const remembered = JSON.parse(adminRememberedRaw) as { login_account?: string; password?: string; remember?: boolean };
        if (remembered.login_account === props.session.login_account && remembered.password) {
          localStorage.setItem("momo_admin_remember", JSON.stringify({ ...remembered, password: newPassword }));
        }
      }
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setAccountNotice("密码已更新。");
    } catch (err) {
      setAccountNotice(`保存失败：${err instanceof Error ? err.message : "未知错误"}`);
    } finally {
      setIsSavingAccount(false);
    }
  }

  const day = Math.max(1, Number(learningState?.status?.learning_days ?? 0) + (review ? 0 : 1));
  const displayUsername = props.session.username || props.session.nickname || "Vi";
  const userAvatarPath = getCurrentUserAvatarPath();
  const currentRoute = routeMap.find((item) => item.status === "active" || item.status === "next") ?? routeMap[0];
  const selectedRoute = routeMap.find((item) => item.route_item_id === selectedRouteId) ?? currentRoute;
  const currentModuleIndex = Math.max(
    1,
    routeMap.findIndex((item) => item.route_item_id === currentRoute?.route_item_id) + 1 || 1,
  );
  const completedModuleCount = routeMap.filter((item) => item.status === "completed").length;
  const stepLabels = ["目标", "单词", "课文", "讲解", "测试", "总结"];
  const currentWord = (lesson.vocabulary ?? [])[wordIndex];
  const currentQuestion = questions[quizIndex];
  const learnedWordCount = learningState?.vocabulary_mastery?.length ?? (lesson.vocabulary?.length ?? 0);
  const completedQuizQuestionCount = learningState?.completed_quiz_questions ?? 0;
  const passageLines = getPassageLines();
  const passageSpeechText = passageLines.map((line) => line.text).join(". ");
  const wordRoleMap = new Map(
    (lesson.vocabulary ?? []).map((item) => [
      item.word.toLowerCase(),
      item.is_review || item.learning_role === "review" ? "review" : "new"
    ])
  );
  const difficultWordMap = new Map(
    (lesson.passage?.difficult_words ?? [
      { word: "the", meaning: "这个；那个" },
      { word: "on", meaning: "在……上" }
    ]).map((item) => [item.word.toLowerCase(), item.meaning])
  );
  const completion = lesson.completion_encouragement ?? fallbackLesson.completion_encouragement;
  const homeEncouragement = lesson.home_encouragement ?? fallbackLesson.home_encouragement;
  const hasCompletedToday = Boolean(review) || Boolean(lessonProgress?.completed);
  const hasStartedToday = Boolean(lessonProgress?.hasStarted && !hasCompletedToday);
  const primaryLessonActionLabel = hasCompletedToday
    ? "复习今天的学习"
    : hasStartedToday
      ? "继续今天的学习"
      : "开始今天的学习";
  const stageEncouragement = getStageEncouragement();
  const routeSummary = progressSummary(selectedRoute);

  useEffect(() => {
    if (learnView !== "lesson" || lessonStep !== 1 || !currentWord) return;
    const timer = window.setTimeout(() => {
      playAudioAssetOrSpeak(
        findAudioAsset("word", `word_${currentWord.word.toLowerCase()}`),
        currentWord.word,
        { rate: 0.82, pitch: 1.05 },
      );
    }, 280);
    return () => window.clearTimeout(timer);
  }, [learnView, lessonStep, wordIndex, lesson.lesson_asset_id]);

  function startLesson() {
    openLessonAt(0, { reset: true });
  }

  function resumeLesson() {
    if (hasCompletedToday || !lessonProgress?.hasStarted) {
      openLessonAt(0, { reset: true });
      return;
    }
    openLessonAt(lessonProgress.lessonStep, {
      passagePage: lessonProgress.passagePage,
      passageCardPage: lessonProgress.passageCardPage,
      knowledgePage: lessonProgress.knowledgePage,
      wordIndex: lessonProgress.wordIndex,
      quizIndex: lessonProgress.quizIndex,
    });
  }

  function openLessonAt(
    step: number,
    options: { reset?: boolean; passagePage?: 0 | 1; passageCardPage?: number; knowledgePage?: number; wordIndex?: number; quizIndex?: number } = {},
  ) {
    const nextStep = Math.max(0, Math.min(step, stepLabels.length - 1));
    const nextPassagePage = options.reset ? 0 : (options.passagePage ?? 0);
    const nextPassageCardPage = options.reset ? 0 : (options.passageCardPage ?? 0);
    const nextKnowledgePage = options.reset ? 0 : (options.knowledgePage ?? 0);
    const nextWordIndex = options.reset ? 0 : (options.wordIndex ?? 0);
    const nextQuizIndex = options.reset ? 0 : (options.quizIndex ?? 0);
    setLessonStep(nextStep);
    setPassagePage(nextPassagePage);
    setPassageCardPage(nextPassageCardPage);
    setKnowledgePage(nextKnowledgePage);
    setWordIndex(nextWordIndex);
    setQuizIndex(nextQuizIndex);
    setSelectedGloss(null);
    saveLessonProgress({
      lessonStep: nextStep,
      passagePage: nextPassagePage,
      passageCardPage: nextPassageCardPage,
      knowledgePage: nextKnowledgePage,
      wordIndex: nextWordIndex,
      quizIndex: nextQuizIndex,
      completed: false,
    });
    setLearnView("lesson");
  }

  function nextModule() {
    setPassagePage(0);
    setPassageCardPage(0);
    setKnowledgePage(0);
    setLessonStep((prev) => Math.min(prev + 1, stepLabels.length - 1));
  }

  function previousModule() {
    setPassagePage(0);
    setPassageCardPage(0);
    setKnowledgePage(0);
    setLessonStep((prev) => Math.max(prev - 1, 0));
  }

  function goToLessonStep(index: number) {
    setLessonStep(index);
    setPassagePage(0);
    setPassageCardPage(0);
    setKnowledgePage(0);
    setSelectedGloss(null);
  }

  function returnHomeFromLesson() {
    saveLessonProgress();
    setLearnView("home");
  }

  function markWordAndContinue(status: WordStatus) {
    if (!currentWord) return;
    setWordMastery((prev) => ({ ...prev, [currentWord.word.toLowerCase()]: status }));
    window.setTimeout(() => {
      if (wordIndex < (lesson.vocabulary?.length ?? 1) - 1) {
        setWordIndex((prev) => prev + 1);
      } else {
        nextModule();
      }
    }, 120);
  }

  function handleQuizAnswer(question: QuizQuestion, option: string) {
    if (option === question.answer) {
      setAnswers((prev) => ({ ...prev, [question.prompt]: option }));
      setQuizWrongSelections((prev) => {
        const next = { ...prev };
        delete next[question.prompt];
        return next;
      });
      window.setTimeout(() => {
        if (quizIndex < questions.length - 1) {
          setQuizIndex((prev) => prev + 1);
        } else {
          nextModule();
        }
      }, 280);
      return;
    }
    setQuizWrongSelections((prev) => ({ ...prev, [question.prompt]: option }));
    setQuizMistakes((prev) => {
      const exists = prev.some((item) => item.prompt === question.prompt && item.selected_answer === option);
      if (exists) return prev;
      return [
        ...prev,
        {
          prompt: question.prompt,
          selected_answer: option,
          answer: question.answer,
          explanation: question.explanation,
        },
      ];
    });
  }

  function chunkItems<T>(items: T[], size: number) {
    const chunks: T[][] = [];
    for (let index = 0; index < items.length; index += size) {
      chunks.push(items.slice(index, index + size));
    }
    return chunks.length ? chunks : [[]];
  }

  function getPassagePageLines() {
    return chunkItems(passageLines, 2);
  }

  function getTranslationPageLines() {
    return chunkItems(passageLines, 2);
  }

  function getKnowledgeCards() {
    const content = lesson.knowledge_note?.content ?? "";
    const lines = content
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean);
    if (!lines.length && content.trim()) return [content.trim()];
    if (!lines.length) return ["今天先把这个知识点听懂、读顺，后面会继续复习。"];
    return lines;
  }

  function renderCardPager(
    currentPage: number,
    totalPages: number,
    setPage: React.Dispatch<React.SetStateAction<number>>,
  ) {
    if (totalPages <= 1) return null;
    return (
      <div className="card-pager">
        {currentPage > 0 ? (
          <button
            className="card-page-button"
            type="button"
            onClick={() => setPage((prev) => Math.max(prev - 1, 0))}
          >
            上一页
          </button>
        ) : null}
        {currentPage < totalPages - 1 ? (
          <button
            className="card-page-button"
            type="button"
            onClick={() => setPage((prev) => Math.min(prev + 1, totalPages - 1))}
          >
            下一页
          </button>
        ) : null}
      </div>
    );
  }

  function progressSummary(routeItem?: RouteMapItem) {
    const isTodayRoute = !routeItem
      || routeItem.route_item_id === currentRoute?.route_item_id
      || routeItem.status === "active";
    return {
      route_module_label: routeItem?.route_module_label
        ?? (isTodayRoute ? lesson.progress_summary?.route_module_label : undefined)
        ?? routeItem?.knowledge_name
        ?? currentRoute?.knowledge_name
        ?? "音标和音节入门",
      main_knowledge_label: routeItem?.main_knowledge_label
        ?? (isTodayRoute ? lesson.progress_summary?.main_knowledge_label : undefined)
        ?? extractMainKnowledgeLabel()
        ?? "今日知识点",
      passage_module_label: routeItem?.passage_module_label
        ?? (isTodayRoute ? lesson.progress_summary?.passage_module_label : undefined)
        ?? routeItem?.scenario_name
        ?? inferPassageModuleLabel()
        ?? "日常对话",
    };
  }

  function extractMainKnowledgeLabel() {
    const text = `${lesson.theme ?? ""} ${(lesson.objectives ?? []).join(" ")}`;
    const phonics = text.match(/\/[^/]+\/\s*和\s*\/[^/]+\//);
    if (phonics) return phonics[0];
    return lesson.objectives?.[0] ?? currentRoute?.knowledge_name;
  }

  function inferPassageModuleLabel() {
    const title = lesson.passage?.title ?? "";
    if (title.toLowerCase().includes("bank")) return "银行对话";
    if (title.includes("见面") || title.toLowerCase().includes("hello")) return "日常问候";
    return "日常对话";
  }

  function progressStorageKey() {
    return `momo_lesson_progress_${props.session.user_id}`;
  }

  function saveLessonProgress(overrides: Partial<LessonProgress> = {}) {
    if (!lesson.lesson_asset_id) return;
    const next: LessonProgress = {
      lesson_asset_id: lesson.lesson_asset_id,
      lesson_date: lesson.lesson_date,
      lessonStep,
      passagePage,
      passageCardPage,
      knowledgePage,
      wordIndex,
      quizIndex,
      hasStarted: true,
      completed: false,
      ...overrides,
      updated_at: new Date().toISOString(),
    };
    setLessonProgress(next);
    localStorage.setItem(progressStorageKey(), JSON.stringify(next));
  }

  function getStageEncouragement() {
    const text = `${currentRoute?.knowledge_name ?? ""} ${currentRoute?.scenario_name ?? ""}`;
    if (text.includes("音标") || text.includes("拼读")) {
      return "每天一点点，先把音标和基础拼读打稳。";
    }
    if (text.includes("问候")) {
      return "把第一句问候说顺，英语就会慢慢亲近起来。";
    }
    if (text.includes("银行")) {
      return "把银行场景一句句练熟，工作里也能更从容。";
    }
    return "每天一点点，稳稳往前走。";
  }

  function getCurrentUserAvatarPath() {
    const identity = `${props.session.login_account} ${props.session.user_id} ${props.session.username} ${props.session.nickname}`.toLowerCase();
    if (identity.includes("adminxly") || identity.includes("admin_1") || identity.includes("user_admin_1")) {
      return ADMIN_AVATAR_PATH;
    }
    return frontendAssetUrl("/assets/avatar-vi.png");
  }

  function getSpeakerAvatarUrl(role?: string) {
    const normalized = (role ?? "").toLowerCase().trim();
    if (!normalized) return "";
    if (["vi", "vizhang"].includes(normalized)) return frontendAssetUrl("/assets/avatar-vi.png");
    if (["mom", "mother", "mum", "mama", "妈妈"].includes(normalized)) {
      return frontendAssetUrl("/assets/avatars/roles/mom2.png");
    }
    if (["admin", "administrator", "admin_1", "adminxly", "管理员"].includes(normalized)) {
      return ADMIN_AVATAR_PATH;
    }
    if (normalized.includes("teacher") || normalized.includes("老师")) {
      return frontendAssetUrl("/assets/avatars/roles/teacher-female.png");
    }
    if (normalized.includes("doctor") || normalized.includes("医生")) {
      return normalized.includes("male") || normalized.includes("男")
        ? frontendAssetUrl("/assets/avatars/roles/doctor-male.png")
        : frontendAssetUrl("/assets/avatars/roles/doctor-female.png");
    }
    return "";
  }

  function SpeakerIcon() {
    return (
      <svg aria-hidden="true" viewBox="0 0 24 24">
        <path d="M4 9v6h4l5 4V5L8 9H4Z" />
        <path d="M16 8.5a4.5 4.5 0 0 1 0 7" />
        <path d="M18.5 6a8 8 0 0 1 0 12" />
      </svg>
    );
  }

  function translatePartOfSpeech(part?: string) {
    const normalized = (part ?? "").toLowerCase();
    const map: Record<string, string> = {
      verb: "动词",
      noun: "名词",
      pronoun: "代词",
      adjective: "形容词",
      adverb: "副词",
      preposition: "介词",
      interjection: "感叹词",
      conjunction: "连词",
      determiner: "限定词"
    };
    return map[normalized] ?? part ?? "词汇";
  }

  function stripRole(line: string) {
    return line.replace(/^[^:：]+[:：]\s*/, "").trim();
  }

  function parsePassageLine(line: string, translation?: string) {
    const roleMatch = line.match(/^([^:：]+)[:：]\s*(.+)$/);
    const translated = translation ? stripRole(translation) : undefined;
    if (!roleMatch) return { text: line.trim(), translation: translated };
    return { role: roleMatch[1].trim(), text: roleMatch[2].trim(), translation: translated };
  }

  function roleLabel(role?: string) {
    if (!role) return "";
    const normalized = role.toLowerCase();
    if (normalized === "teacher") return "老师";
    if (normalized === "vi") return "Vi";
    return role;
  }

  function cleanPassageTitle(title?: string) {
    return (title || "课文").replace(/^课堂对话[:：]\s*/, "").replace(/[。.]$/, "");
  }

  function getPassageLines() {
    const passage = lesson.passage;
    if (!passage) return [];
    if (passage.lines?.length) {
      const sourceLines = (passage.english_text ?? "").split(/\n+/).filter((line) => line.trim()).map((line) => parsePassageLine(line));
      return passage.lines.map((line, index) => {
        const sourceRole = sourceLines[index]?.role;
        if (line.role || sourceRole) {
          return {
            ...line,
            role: line.role ?? sourceRole,
            text: stripRole(line.text),
            translation: line.translation ? stripRole(line.translation) : undefined
          };
        }
        return parsePassageLine(line.text, line.translation);
      });
    }
    const englishLines = (passage.english_text ?? "").split(/\n+/).filter((line) => line.trim());
    const chineseLines = (passage.chinese_support ?? "").split(/\n+/).filter((line) => line.trim());
    return englishLines.map((line, index) => parsePassageLine(line, chineseLines[index]));
  }

  function playPassage(rate: number) {
    const useSlowAudio = rate < 0.8;
    const lineAssets = passageLines.map((line) => (
      findAudioAssetById(useSlowAudio ? line.slow_audio_ref : line.audio_ref)
    )).filter((asset): asset is AudioAsset => Boolean(asset));
    if (lineAssets.length !== passageLines.length) {
      speak(passageSpeechText, { rate, pitch: rate < 0.8 ? 1 : 1.06 });
      return;
    }
    void playAudioAssetsSequentially(lineAssets, passageSpeechText, { rate, pitch: rate < 0.8 ? 1 : 1.06 });
  }

  function renderDialogueText(text: string) {
    return text.split(/(\b[A-Za-z']+\b)/g).map((part, index) => {
      const key = `${part}-${index}`;
      const normalized = part.toLowerCase();
      const learningRole = wordRoleMap.get(normalized);
      if (learningRole) {
        return <span className={learningRole === "review" ? "review-word" : "today-word"} key={key}>{part}</span>;
      }
      const meaning = difficultWordMap.get(normalized);
      if (meaning) {
        return (
          <button
            className="gloss-word"
            key={key}
            onClick={(event) => {
              event.stopPropagation();
              setSelectedGloss({ word: part, meaning });
            }}
            type="button"
          >
            {part}
          </button>
        );
      }
      return <React.Fragment key={key}>{part}</React.Fragment>;
    });
  }

  function renderLessonStep() {
    if (lessonStep === 0) {
      return (
        <section className="lesson-panel">
          <p className="eyebrow">今日目标</p>
          <h2>{lesson.theme}</h2>
          <p>{lesson.human_readable_summary}</p>
          <div className="objective-list">
            {(lesson.objectives ?? []).map((item) => <span key={item}>{item}</span>)}
          </div>
        </section>
      );
    }
    if (lessonStep === 1 && currentWord) {
      const isReviewWord = Boolean(currentWord.is_review || currentWord.learning_role === "review");
      const imagePath = currentWord.image_url
        ?? (currentWord.needs_image ? `/generated/word_images/${currentWord.word.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.svg` : "");
      const imageUrl = runtimeAssetUrl(imagePath);
      return (
        <section className="lesson-panel word-focus">
          <p className="eyebrow">{isReviewWord ? "复习词" : "新词"} {wordIndex + 1}/{lesson.vocabulary?.length ?? 0}</p>
          <div className="word-hero">
            <h2>{currentWord.word}</h2>
            <p className="phonetic-line">{currentWord.phonetic}</p>
            {imageUrl ? (
              <img className="word-image" src={imageUrl} alt={currentWord.meaning ?? currentWord.word} />
            ) : (
              <div className="word-picture">{currentWord.word.slice(0, 1).toUpperCase()}</div>
            )}
            <p className="word-part-line">{translatePartOfSpeech(currentWord.part_of_speech)}</p>
            {isReviewWord ? <p className="word-review-line">上次内容回顾</p> : null}
            <p className="word-meaning-line">{currentWord.meaning}</p>
            <MobileButton
              className={`audio-pill ${speakingText === currentWord.word ? "playing" : ""}`}
              color="primary"
              fill="outline"
              onClick={() => playAudioAssetOrSpeak(
                findAudioAsset("word", `word_${currentWord.word.toLowerCase()}`),
                currentWord.word,
                { rate: 0.82, pitch: 1.05 },
              )}
            >
              播放发音
            </MobileButton>
          </div>
          <div className="word-status-row">
            {(["known", "fuzzy", "unknown"] as WordStatus[]).map((status) => (
              <MobileButton
                data-testid={`word-choice-${status}`}
                key={status}
                className={`choice-button choice-${status}`}
                fill="outline"
                color="default"
                onClick={() => markWordAndContinue(status)}
              >
                {status === "known" ? "知道" : status === "fuzzy" ? "模糊" : "不知道"}
              </MobileButton>
            ))}
          </div>
        </section>
      );
    }
    if (lessonStep === 2 && lesson.passage && passagePage === 0) {
      const passagePages = getPassagePageLines();
      const currentLines = passagePages[Math.min(passageCardPage, passagePages.length - 1)] ?? [];
      return (
        <section className="lesson-panel passage-panel passage-original-panel">
          <p className="eyebrow">对话练习</p>
          <h2>{cleanPassageTitle(lesson.passage.title)}</h2>
          <div className={`passage-subtabs segmented-tab ${passagePage === 0 ? "show-original" : "show-translation"}`} aria-label="课文页面">
            <button className="active" type="button" onClick={() => {
              setPassagePage(0);
              setPassageCardPage(0);
            }}>原文</button>
            <button type="button" onClick={() => {
              setPassagePage(1);
              setPassageCardPage(0);
            }}>译文</button>
          </div>
          <div className="passage-play-row">
            <MobileButton className={`audio-pill ${speakingText === passageSpeechText ? "playing" : ""}`} color="primary" fill="outline" onClick={() => playPassage(0.9)}>正常播放</MobileButton>
            <MobileButton className={`audio-pill slow ${speakingText === passageSpeechText ? "playing" : ""}`} color="primary" fill="outline" onClick={() => playPassage(0.68)}>慢速播放</MobileButton>
          </div>
          <div className="content-card passage-paper">
            {currentLines.map((line, index) => (
              <div className="transcript-row" key={`${line.text}-${index}`}>
                <div className={`speaker-badge ${line.role?.toLowerCase() === "vi" ? "speaker-vi" : ""}`}>
                  {getSpeakerAvatarUrl(line.role) ? (
                    <img src={getSpeakerAvatarUrl(line.role)} alt="" />
                  ) : (
                    <span>{roleLabel(line.role).slice(0, 1) || "T"}</span>
                  )}
                </div>
                <div className="passage-sentence">
                  {line.role ? <span className="speaker-name">{roleLabel(line.role)}</span> : null}
                  <span className="passage-text">{renderDialogueText(line.text)}</span>
                </div>
                <button
                  className={`line-play-button icon-audio ${speakingText === line.text ? "playing" : ""}`}
                  type="button"
                  aria-label={`播放 ${line.text}`}
                  onClick={() => playAudioAssetOrSpeak(
                    findAudioAssetById(line.audio_ref),
                    line.text,
                    { rate: 0.84, pitch: 1.06 },
                  )}
                >
                  <SpeakerIcon />
                </button>
              </div>
            ))}
            {renderCardPager(passageCardPage, passagePages.length, setPassageCardPage)}
          </div>
          {selectedGloss ? (
            <div className="gloss-popover">
              <b>{selectedGloss.word}</b>
              <span>{selectedGloss.meaning}</span>
              <button type="button" onClick={() => setSelectedGloss(null)}>知道了</button>
            </div>
          ) : null}
        </section>
      );
    }
    if (lessonStep === 2 && lesson.passage && passagePage === 1) {
      const translationPages = getTranslationPageLines();
      const currentLines = translationPages[Math.min(passageCardPage, translationPages.length - 1)] ?? [];
      return (
        <section className="lesson-panel passage-panel passage-translation-panel">
          <p className="eyebrow">课文译文</p>
          <h2>{cleanPassageTitle(lesson.passage.title)}</h2>
          <div className={`passage-subtabs segmented-tab ${passagePage === 0 ? "show-original" : "show-translation"}`} aria-label="课文页面">
            <button type="button" onClick={() => {
              setPassagePage(0);
              setPassageCardPage(0);
            }}>原文</button>
            <button className="active" type="button" onClick={() => {
              setPassagePage(1);
              setPassageCardPage(0);
            }}>译文</button>
          </div>
          <div className="difficult-word-list">
            {Array.from(difficultWordMap.entries()).map(([word, meaning]) => (
              <div key={word}>
                <b>{word}</b>
                <span>{meaning}</span>
              </div>
            ))}
          </div>
          <div className="content-card translation-paper">
            {currentLines.map((line, index) => (
              <div className="translation-line" key={`${line.translation ?? line.text}-${index}`}>
                {line.role ? <b>{roleLabel(line.role)}</b> : null}
                <p>{line.translation ?? stripRole(line.text)}</p>
              </div>
            ))}
            {renderCardPager(passageCardPage, translationPages.length, setPassageCardPage)}
          </div>
        </section>
      );
    }
    if (lessonStep === 3 && lesson.knowledge_note) {
      const cards = getKnowledgeCards();
      const currentCard = cards[Math.min(knowledgePage, cards.length - 1)];
      return (
        <section className="lesson-panel knowledge-panel">
          <p className="eyebrow">知识讲解</p>
          <h2>{lesson.theme ?? "今日知识点"}</h2>
          <div className="content-card knowledge-card">
            <p>{currentCard}</p>
            {renderCardPager(knowledgePage, cards.length, setKnowledgePage)}
          </div>
        </section>
      );
    }
    if (lessonStep === 4 && currentQuestion) {
      const wrongSelection = quizWrongSelections[currentQuestion.prompt];
      const checked = Boolean(answers[currentQuestion.prompt] || wrongSelection);
      const quizAudioAsset = findAudioAssetById(currentQuestion.audio_ref)
        ?? findAudioAsset("quiz_question", `quiz_question_${currentQuestion.question_id ?? ""}`);
      const quizAudioText = currentQuestion.audio_text || quizAudioAsset?.text;
      return (
        <section className="lesson-panel quiz-panel">
          <p className="eyebrow">小测试 {quizIndex + 1}/{questions.length}</p>
          <h2>{currentQuestion.prompt}</h2>
          {quizAudioText ? (
            <MobileButton
              className={`audio-pill quiz-audio-pill ${speakingText === quizAudioText ? "playing" : ""}`}
              color="primary"
              fill="outline"
              onClick={() => playAudioAssetOrSpeak(quizAudioAsset, quizAudioText, { rate: 0.84, pitch: 1.04 })}
            >
              播放题目音频
            </MobileButton>
          ) : null}
          <div className="option-grid">
            {currentQuestion.options.map((option) => {
              const selected = answers[currentQuestion.prompt] === option;
              const wrong = wrongSelection === option;
              const correct = option === currentQuestion.answer;
              return (
                <MobileButton
                  data-testid={`quiz-option-${option}`}
                  className={[
                    "option-button quiz-option",
                    selected ? "selected" : "",
                    wrongSelection && correct ? "correct" : "",
                    wrong ? "wrong" : ""
                  ].join(" ")}
                  key={option}
                  fill="outline"
                  onClick={() => handleQuizAnswer(currentQuestion, option)}
                >
                  {option}
                </MobileButton>
              );
            })}
          </div>
          {checked && wrongSelection ? <p className="explain">{currentQuestion.explanation}</p> : null}
        </section>
      );
    }
    return (
      <section className="lesson-panel finish-stage">
        <p className="eyebrow">学习总结</p>
        <h2>今天完成到这里</h2>
        <p>当前测试正确率：{quizScorePreview}%</p>
        <div className="rating-row">
          {["轻松", "刚好", "有点难", "太难"].map((item) => (
            <MobileButton
              key={item}
              size="small"
              fill={selfRating === item ? "solid" : "outline"}
              color={selfRating === item ? "primary" : "default"}
              onClick={() => setSelfRating(item)}
            >
              {item}
            </MobileButton>
          ))}
        </div>
        <MobileTextArea
          value={difficultyText}
          onChange={setDifficultyText}
          placeholder="可以写今天卡住的地方，也可以留空"
          rows={3}
        />
        <MobileButton data-testid="complete-today-learning" className="primary-action" block color="primary" size="large" loading={isSubmitting} onClick={completeToday}>
          {isSubmitting ? "保存中" : "完成今日学习"}
        </MobileButton>
      </section>
    );
  }

  return (
    <main className={`learn-app ${learnView === "lesson" ? "lesson-mode" : ""}`}>
      {learnView === "home" ? <header className="learn-topbar">
        <div>
          <p className="eyebrow">{lesson.lesson_date ?? "今日课程"}</p>
          <h1>Hi, {displayUsername}</h1>
          <div className="home-quote">
            <p>{homeEncouragement?.quote_en}</p>
            <p>{homeEncouragement?.quote_zh}</p>
          </div>
        </div>
        <MobileButton className="utility-button" size="small" fill="none" onClick={props.onLogout}>退出</MobileButton>
      </header> : null}

      {notice ? <div className="notice">{notice}</div> : null}

      {learnView === "home" ? (
        <section className="home-screen">
          <div className="home-copy">
            <p className="eyebrow">今日学习</p>
            <h2>{currentRoute?.theme ?? lesson.theme}</h2>
            <p>{lesson.objectives?.[0] ?? lesson.human_readable_summary}</p>
          </div>

          <div className="home-stat-row">
            <div className="home-stat">
              <b>{day}</b>
              <span>学习天数</span>
            </div>
            <div className="home-stat">
              <b>{learnedWordCount}</b>
              <span>已学单词</span>
            </div>
          </div>

          <div className="today-task-grid">
            <button type="button" onClick={() => openLessonAt(1)}>
              <span>词汇</span>
              <b>{lesson.vocabulary?.length ?? 0} 个</b>
            </button>
            <button type="button" onClick={() => openLessonAt(2)}>
              <span>课文</span>
              <b>{lesson.passage ? "1 篇" : "0 篇"}</b>
            </button>
            <button type="button" onClick={() => openLessonAt(4)}>
              <span>小测试</span>
              <b>{questions.length} 题</b>
            </button>
          </div>

          <div className="study-hero-art" aria-hidden="true">
            <img className="study-avatar-img" src={userAvatarPath} alt="" />
          </div>

          <MobileButton data-testid="start-today-learning" className="primary-action" block color="primary" size="large" onClick={resumeLesson}>
            {primaryLessonActionLabel}
          </MobileButton>
          <button className="map-link-button utility-button" type="button" onClick={() => setLearnView("map")}>
            查看学习进度
          </button>
        </section>
      ) : null}

      {learnView === "map" ? (
        <section className="map-screen">
          <div className="screen-title">
            <p className="eyebrow">学习进度</p>
            <h2>今天学到这里</h2>
          </div>
          {selectedRoute ? (
            <div className={`route-detail-card ${selectedRoute.status ?? "locked"}`}>
              <p className="eyebrow">第 {selectedRoute.day_number ?? 1} 天</p>
              <h3>{selectedRoute.theme}</h3>
              <div className="route-detail-meta">
                <span>{routeSummary.route_module_label}</span>
                <span>{routeSummary.main_knowledge_label}</span>
                <span>{routeSummary.passage_module_label}</span>
              </div>
              {selectedRoute.status === "active" ? (
                <MobileButton className="primary-action compact" block color="primary" onClick={resumeLesson}>
                  {primaryLessonActionLabel}
                </MobileButton>
              ) : null}
            </div>
          ) : null}
          <div className="route-ladder">
            {routeMap.map((item, index) => (
              <button
                className={`route-map-node ${item.status ?? "locked"} ${selectedRoute?.route_item_id === item.route_item_id ? "selected" : ""}`}
                key={item.route_item_id ?? `${item.day_number}-${item.theme}`}
                onClick={() => {
                  setSelectedRouteId(item.route_item_id ?? `${item.day_number}-${item.theme}`);
                }}
                type="button"
              >
                <span className="route-dot">{index + 1}</span>
                <div>
                  <b>第 {item.day_number ?? index + 1} 天 · {item.theme}</b>
                  <small>{item.knowledge_name ?? "知识点"} / {item.scenario_name ?? "场景"}</small>
                </div>
                <em>{item.status === "completed" ? "已完成" : item.status === "active" ? "今天" : item.status === "next" ? "下一课" : "未解锁"}</em>
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {learnView === "lesson" ? (
        <section className="lesson-player">
          <button data-testid="lesson-return-home" className="lesson-home-button utility-button" type="button" onClick={returnHomeFromLesson}>
            返回主页
          </button>
          <div className="lesson-player-head">
            <div>
              <p className="eyebrow">
                跟练 {lessonStep + 1}/{stepLabels.length}{lessonStep === 2 ? ` · ${passagePage === 0 ? "原文" : "译文"}` : ""}
              </p>
              <h2>{stepLabels[lessonStep]}</h2>
            </div>
            <span>已学 {learnedWordCount} 词</span>
          </div>
          <div className="lesson-progress-bar" aria-hidden="true">
            <span style={{ width: `${Math.round(((lessonStep + 1 + (lessonStep === 2 && passagePage === 1 ? 0.45 : 0)) / stepLabels.length) * 100)}%` }} />
          </div>
          <div className="mini-path-map">
            {stepLabels.map((label, index) => (
              <button
                aria-label={label}
                className={`mini-node ${index < lessonStep ? "done" : ""} ${index === lessonStep ? "active" : ""}`}
                key={label}
                onClick={() => goToLessonStep(index)}
                type="button"
              >
                {index + 1}
              </button>
            ))}
          </div>

          {renderLessonStep()}

          <div className={`lesson-action-row ${lessonStep === 0 || lessonStep === stepLabels.length - 1 ? "single-action" : ""}`}>
            {lessonStep > 0 ? (
              <MobileButton className="module-back" fill="outline" onClick={previousModule}>
                上一模块
              </MobileButton>
            ) : null}
            {lessonStep < stepLabels.length - 1 ? (
              <MobileButton data-testid="next-module" className="module-next" color="primary" onClick={nextModule}>
                下一模块
              </MobileButton>
            ) : null}
          </div>
        </section>
      ) : null}

      {learnView === "celebration" ? (
        <section className="celebration-screen">
          <div className="trophy-scene" aria-hidden="true">
            <div className="trophy-cup">
              <span />
            </div>
          </div>
          <p className="eyebrow">今日完成</p>
          <h2>太棒了，{displayUsername}</h2>
          <p className="celebration-message">{completion?.message_zh}</p>
          <div className="quote-box">
            <p>{completion?.quote_en}</p>
            <p>{completion?.quote_zh}</p>
            <span>{completion?.quote_author}</span>
          </div>
          <MobileButton data-testid="celebration-continue" className="primary-action" block color="primary" size="large" onClick={() => setLearnView("profile")}>
            {completion?.button_text ?? "我真行"}
          </MobileButton>
        </section>
      ) : null}

      {learnView === "profile" ? (
        <section className="profile-screen">
          <div className="profile-action-row">
            <button data-testid="profile-settings" className="top-text-button utility-button" type="button" onClick={() => {
              setAccountNotice("");
              setLearnView("settings");
            }}>
              设置
            </button>
            <button className="top-text-button utility-button" type="button" onClick={props.onLogout}>
              退出
            </button>
          </div>
          <div className="profile-identity-card">
            <img className="profile-avatar-img" src={userAvatarPath} alt="" />
            <div>
              <h2>{props.session.nickname ?? "Vi"}</h2>
              <p>{stageEncouragement}</p>
            </div>
          </div>
          <div className="achievement-grid">
            <div className="wide-achievement">
              <b>{completedQuizQuestionCount}</b>
              <span>已完成测试题</span>
            </div>
            <div>
              <b>{day}</b>
              <span>学习天数</span>
            </div>
            <div>
              <b>{completedModuleCount}</b>
              <span>完成模块</span>
            </div>
            <div>
              <b>{currentModuleIndex}</b>
              <span>当前模块</span>
            </div>
          </div>
          <div className="profile-learning-card">
            <b>学习档案</b>
            <div>
              <span>当前模块</span>
              <p>第 {currentModuleIndex}/{Math.max(routeMap.length, currentModuleIndex)} 模块：{currentRoute?.knowledge_name ?? "音标和基础拼读"}</p>
            </div>
            <div>
              <span>模块场景</span>
              <p>{currentRoute?.scenario_name ?? "音标拼读"} · {currentRoute?.level_code ?? "入门"}</p>
            </div>
          </div>
        </section>
      ) : null}

      {learnView === "settings" ? (
        <section className="settings-screen">
          <button className="settings-back-button utility-button" type="button" onClick={() => setLearnView("profile")}>
            返回
          </button>
          <div className="screen-title">
            <p className="eyebrow">账号设置</p>
            <h2>修改账号信息</h2>
            <p>用户名会显示在学习页面；密码只保存在本地账号系统里。</p>
          </div>
          <div className="settings-panel">
            <h3>修改用户名</h3>
            <label className="mobile-field">
              新用户名
              <MobileInput data-testid="display-name-input" value={displayNameDraft} onChange={setDisplayNameDraft} />
            </label>
            <MobileButton data-testid="save-display-name" className="primary-action compact" block color="primary" loading={isSavingAccount} onClick={saveDisplayName}>
              确定
            </MobileButton>
          </div>
          <div className="settings-panel">
            <h3>修改密码</h3>
            <label className="mobile-field">
              当前密码
              <MobileInput value={currentPassword} type="password" onChange={setCurrentPassword} />
            </label>
            <label className="mobile-field">
              新密码
              <MobileInput value={newPassword} type="password" onChange={setNewPassword} />
            </label>
            <label className="mobile-field">
              确认新密码
              <MobileInput value={confirmPassword} type="password" onChange={setConfirmPassword} />
            </label>
            <MobileButton className="primary-action compact" block color="primary" loading={isSavingAccount} onClick={savePassword}>
              确定
            </MobileButton>
          </div>
          {accountNotice ? <p className="account-notice">{accountNotice}</p> : null}
        </section>
      ) : null}

      {learnView !== "lesson" && learnView !== "celebration" && learnView !== "settings" ? <nav className="learn-tabbar">
        {[
          ["home", "学习"],
          ["map", "进度"],
          ["profile", "我的"]
        ].map(([key, label]) => (
          <button
            data-testid={`tab-${key}`}
            className={learnView === key || (key === "home" && learnView === "lesson") ? "active" : ""}
            key={key}
            onClick={() => setLearnView(key as "home" | "map" | "profile")}
            type="button"
          >
            {label}
          </button>
        ))}
      </nav> : null}
    </main>
  );
}

function AdminPage(props: { session: Session; onLogout: () => void }) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState("user_mom");
  const [workspace, setWorkspace] = useState<UserWorkspace | null>(null);
  const [editorText, setEditorText] = useState("");
  const [adminNoteDraft, setAdminNoteDraft] = useState("");
  const [aiInstruction, setAiInstruction] = useState("");
  const [feedbackText, setFeedbackText] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    void loadUsers();
  }, []);

  useEffect(() => {
    if (!selectedUserId) return;
    void loadWorkspace(selectedUserId);
  }, [selectedUserId]);

  useEffect(() => {
    const draft = workspace?.latest_draft;
    if (!draft?.draft_json) {
      setEditorText("");
      setAdminNoteDraft("");
      return;
    }
    setEditorText(JSON.stringify(draft.draft_json, null, 2));
    setAdminNoteDraft(draft.draft_json.admin_note ?? draft.admin_note ?? "");
  }, [workspace?.latest_draft?.draft_id, workspace?.latest_draft?.updated_at]);

  function adminHeaders(isJson = false): HeadersInit {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${props.session.session_token ?? ""}`
    };
    if (isJson) headers["Content-Type"] = "application/json";
    return headers;
  }

  function handleAdminAuth(res: Response) {
    if (res.status === 401 || res.status === 403) {
      props.onLogout();
      return false;
    }
    return true;
  }

  async function loadUsers() {
    const res = await fetch(apiUrl("/api/admin/users"), { headers: adminHeaders() });
    if (!handleAdminAuth(res)) return;
    if (!res.ok) return;
    const data = await res.json();
    const nextUsers = data.users ?? [];
    setUsers(nextUsers);
    if (!selectedUserId && nextUsers[0]?.user_id) setSelectedUserId(nextUsers[0].user_id);
  }

  async function loadWorkspace(userId = selectedUserId) {
    const res = await fetch(apiUrl(`/api/admin/users/${encodeURIComponent(userId)}/workspace`), { headers: adminHeaders() });
    if (!handleAdminAuth(res)) return;
    if (res.ok) setWorkspace(await res.json());
  }

  async function generateDraft() {
    const res = await fetch(apiUrl("/api/admin/drafts/generate"), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({ user_id: selectedUserId })
    });
    if (!handleAdminAuth(res)) return;
    setNotice(res.ok ? "已生成未发布课程草稿。" : "生成失败。");
    await loadWorkspace();
    await loadUsers();
  }

  async function generateWeeklyDrafts() {
    const res = await fetch(apiUrl("/api/admin/drafts/generate-week"), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({ user_id: selectedUserId, days: 7 })
    });
    if (!handleAdminAuth(res)) return;
    if (res.ok) {
      const data = await res.json();
      setNotice(`已生成未来 ${data.drafts?.length ?? 7} 天未发布课程草稿。`);
    } else {
      setNotice("一周草稿生成失败。");
    }
    await loadWorkspace();
    await loadUsers();
  }

  async function confirmNote() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!draftId) return;
    const res = await fetch(apiUrl(`/api/admin/drafts/${encodeURIComponent(draftId)}/note`), {
      method: "PUT",
      headers: adminHeaders(true),
      body: JSON.stringify({ admin_note: adminNoteDraft || null })
    });
    if (!handleAdminAuth(res)) return;
    setNotice(res.ok ? "备注已写入 lesson JSON。" : "备注保存失败。");
    await loadWorkspace();
  }

  async function aiAdjust() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!draftId || !aiInstruction.trim()) return;
    const res = await fetch(apiUrl(`/api/admin/drafts/${encodeURIComponent(draftId)}/ai-adjust`), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({ admin_instruction: aiInstruction })
    });
    if (!handleAdminAuth(res)) return;
    setNotice(res.ok ? "已根据调整指令重新生成草稿。" : "重新生成失败。");
    await loadWorkspace();
  }

  async function manualSave() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!draftId) return;
    try {
      const parsed = JSON.parse(editorText);
      const res = await fetch(apiUrl(`/api/admin/drafts/${encodeURIComponent(draftId)}`), {
        method: "PUT",
        headers: adminHeaders(true),
        body: JSON.stringify({ lesson_json: parsed })
      });
      if (!handleAdminAuth(res)) return;
      if (!res.ok) throw new Error(await res.text());
      setNotice("人工编辑已保存。");
      await loadWorkspace();
    } catch {
      setNotice("保存失败，请检查 JSON 格式和必填字段。");
    }
  }

  async function undoDraft() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!draftId) return;
    const res = await fetch(apiUrl(`/api/admin/drafts/${encodeURIComponent(draftId)}/undo`), {
      method: "POST",
      headers: adminHeaders()
    });
    if (!handleAdminAuth(res)) return;
    setNotice(res.ok ? "已还原到上一步。" : "没有可还原的上一步。");
    await loadWorkspace();
  }

  async function generateDraftAudio() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!draftId) return;
    setNotice("正在生成音频，请稍等。");
    const res = await fetch(apiUrl(`/api/admin/drafts/${encodeURIComponent(draftId)}/audio`), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({ force: false })
    });
    if (!handleAdminAuth(res)) return;
    if (res.ok) {
      const data = await res.json();
      setNotice(`音频已生成：新增 ${data.generated_count ?? 0} 条，复用 ${data.skipped_count ?? 0} 条，失败 ${data.error_count ?? 0} 条。`);
    } else {
      setNotice("音频生成失败。");
    }
    await loadWorkspace();
  }

  async function generatePendingDraftsAudio() {
    setNotice("正在生成未来 7 天待发布草稿音频，请稍等。");
    const res = await fetch(apiUrl("/api/admin/drafts/audio-batch"), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({ user_id: selectedUserId, days: 7, force: false })
    });
    if (!handleAdminAuth(res)) return;
    if (res.ok) {
      const data = await res.json();
      setNotice(`一周音频已处理：草稿 ${data.draft_count ?? 0} 个，新增 ${data.generated_count ?? 0} 条，复用 ${data.skipped_count ?? 0} 条，失败 ${data.error_count ?? 0} 条。`);
    } else {
      setNotice("一周音频生成失败。");
    }
    await loadWorkspace();
  }

  async function publishDraft() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!draftId) return;
    const res = await fetch(apiUrl(`/api/admin/drafts/${encodeURIComponent(draftId)}/publish`), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({ reason: "admin_manual_publish" })
    });
    if (!handleAdminAuth(res)) return;
    setNotice(res.ok ? "草稿已发布并进入正式 lesson JSON 资产库。" : "发布失败。");
    await loadWorkspace();
    await loadUsers();
  }

  async function saveFeedback() {
    const draftId = workspace?.latest_draft?.draft_id;
    if (!feedbackText.trim()) return;
    const res = await fetch(apiUrl("/api/admin/feedback"), {
      method: "POST",
      headers: adminHeaders(true),
      body: JSON.stringify({
        user_id: selectedUserId,
        target_type: "lesson_draft",
        target_id: draftId ?? selectedUserId,
        feedback_text: feedbackText
      })
    });
    if (!handleAdminAuth(res)) return;
    if (res.ok) {
      setFeedbackText("");
      setNotice("管理员反馈已记录到后台开发日志。");
      await loadWorkspace();
    }
  }

  const selectedUser = users.find((item) => item.user_id === selectedUserId);
  const draft = workspace?.latest_draft;
  const overview = workspace?.learning_overview;

  return (
    <Layout className="admin-layout">
      <Layout.Sider className="admin-sider" width={280} breakpoint="lg" collapsedWidth={0}>
        <div className="admin-brand">
          <b>MomoLingo</b>
          <span>Admin Console</span>
        </div>
        <List
          className="admin-user-list"
          dataSource={users}
          renderItem={(user) => (
            <List.Item
              className={selectedUserId === user.user_id ? "admin-user-item selected" : "admin-user-item"}
              onClick={() => setSelectedUserId(user.user_id)}
            >
              <List.Item.Meta
                title={user.nickname ?? user.user_id}
                description={user.login_account ?? user.user_id}
              />
              <Tag color={user.pending_draft_count ? "green" : "default"}>{user.pending_draft_count ?? 0}</Tag>
            </List.Item>
          )}
        />
      </Layout.Sider>
      <Layout>
        <Layout.Header className="admin-topbar">
          <div>
            <Typography.Text type="secondary">管理员工作台</Typography.Text>
            <Typography.Title level={3}>{workspace?.user?.nickname ?? selectedUser?.nickname ?? selectedUserId}</Typography.Title>
          </div>
          <div className="admin-session-card">
            <img className="admin-avatar-img" src={ADMIN_AVATAR_PATH} alt="" />
            <div>
              <b>{props.session.nickname ?? props.session.username ?? "Admin_1"}</b>
              <span>{props.session.login_account}</span>
            </div>
          </div>
          <Space wrap>
            <Tag color={draft ? "green" : "default"}>{draft?.status ?? "无未发布草稿"}</Tag>
            <Button onClick={() => go("/learn")}>学习端</Button>
            <Button onClick={props.onLogout}>退出后台</Button>
          </Space>
        </Layout.Header>
        <Layout.Content className="admin-content">
          {notice ? <div className="notice">{notice}</div> : null}

          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card title="用户信息">
                <p>登录账号：{workspace?.login_accounts?.[0]?.login_account ?? selectedUser?.login_account ?? "未设置"}</p>
                <p>每日时长：{workspace?.profile?.daily_minutes ?? 30} 分钟</p>
                <p>学习目标：{workspace?.profile?.goal ?? "暂无"}</p>
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card title="学习结果">
                <Row gutter={[12, 12]}>
                  <Col span={12}><Statistic title="学习天数" value={overview?.learning_days ?? 0} /></Col>
                  <Col span={12}><Statistic title="词汇量估计" value={overview?.vocabulary_estimate ?? 0} /></Col>
                  <Col span={12}><Statistic title="已掌握词" value={overview?.mastered_vocabulary ?? 0} /></Col>
                  <Col span={12}><Statistic title="待复习词" value={overview?.needs_review_vocabulary ?? 0} /></Col>
                </Row>
              </Card>
            </Col>
          </Row>

          <Card
            className="admin-section"
            title="未发布课程"
            extra={
              <Space>
                <Button onClick={generateDraft}>生成草稿</Button>
                <Button onClick={generateWeeklyDrafts}>生成一周草稿</Button>
                <Button disabled={!draft} onClick={generateDraftAudio}>生成音频</Button>
                <Button disabled={!draft} onClick={generatePendingDraftsAudio}>生成一周音频</Button>
                <Button type="primary" disabled={!draft} onClick={publishDraft}>发布</Button>
              </Space>
            }
          >
            <Typography.Title level={4}>{draft?.draft_json?.theme ?? "暂无未发布 lesson JSON"}</Typography.Title>
            <Typography.Paragraph>{draft?.human_readable_summary ?? "当前用户还没有未发布草稿，可以先生成一个。"}</Typography.Paragraph>
          </Card>

          {draft ? (
            <>
              <Row gutter={[16, 16]} className="admin-section">
                <Col xs={24} md={12}>
                  <Card title="草稿备注">
                    <AntInput.TextArea rows={5} value={adminNoteDraft} onChange={(event) => setAdminNoteDraft(event.target.value)} />
                    <Space className="admin-command-row">
                      <Button type="primary" onClick={confirmNote}>确定</Button>
                      <Button onClick={() => setAdminNoteDraft("")}>清空</Button>
                    </Space>
                  </Card>
                </Col>
                <Col xs={24} md={12}>
                  <Card title="AI 调整">
                    <AntInput.TextArea rows={5} value={aiInstruction} onChange={(event) => setAiInstruction(event.target.value)} />
                    <Space className="admin-command-row">
                      <Button type="primary" onClick={aiAdjust}>确定</Button>
                      <Button onClick={() => setAiInstruction("")}>清空</Button>
                    </Space>
                  </Card>
                </Col>
              </Row>

              <Card
                className="admin-section"
                title="人工编辑 JSON"
                extra={
                  <Space>
                    <Button type="primary" onClick={manualSave}>保存</Button>
                    <Button onClick={undoDraft}>还原</Button>
                  </Space>
                }
              >
                <AntInput.TextArea
                  className="json-editor"
                  rows={22}
                  value={editorText}
                  onChange={(event) => setEditorText(event.target.value)}
                />
              </Card>

              <Card title="管理员反馈" className="admin-section">
                <AntInput.TextArea rows={4} value={feedbackText} onChange={(event) => setFeedbackText(event.target.value)} />
                <Button className="admin-command-row" type="primary" onClick={saveFeedback}>记录反馈</Button>
                <List
                  dataSource={workspace?.feedback_logs ?? []}
                  renderItem={(item) => (
                    <List.Item>
                      <List.Item.Meta title={item.created_at} description={item.feedback_text} />
                    </List.Item>
                  )}
                />
              </Card>
            </>
          ) : null}

          <Card title="近期复盘" className="admin-section">
            <p>当前阶段：{overview?.current_stage ?? "starter"} · 水平：{overview?.overall_level ?? "zero_base"}</p>
            <p>薄弱项：{overview?.weak_summary ?? "暂无"}</p>
            <p>下一步建议：{overview?.next_suggestion ?? "暂无"}</p>
            <List
              dataSource={overview?.recent_reviews ?? []}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta title={item.review_date} description={item.human_readable_summary} />
                </List.Item>
              )}
            />
          </Card>
        </Layout.Content>
      </Layout>
    </Layout>
  );
}

createRoot(document.getElementById("root")!).render(
  <ConfigProvider
    theme={{
      token: {
        colorPrimary: "#1677ff",
        borderRadius: 8,
        fontFamily: "Inter, Noto Sans SC, system-ui, sans-serif"
      }
    }}
  >
    <App />
  </ConfigProvider>
);
