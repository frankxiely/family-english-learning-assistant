import { expect, test } from "@playwright/test";

type LessonResponse = {
  lesson_json: {
    quiz?: {
      questions?: Array<{
        prompt: string;
        answer: string;
      }>;
    };
    vocabulary?: Array<{ word: string }>;
  };
};

test("mobile learner can complete today's lesson", async ({ page, request }) => {
  const lessonResponse = await request.get("http://127.0.0.1:8000/api/learning/today?user_id=user_admin_1");
  expect(lessonResponse.ok()).toBeTruthy();
  const lessonPayload = (await lessonResponse.json()) as LessonResponse;
  const questionAnswers = lessonPayload.lesson_json.quiz?.questions?.map((question) => question.answer) ?? [];
  const wordCount = lessonPayload.lesson_json.vocabulary?.length ?? 0;

  await page.goto("/login");
  await page.getByTestId("learner-login-account").fill("AdminXLY");
  await page.getByTestId("learner-login-password").fill("Frank1229");
  await page.getByTestId("learner-login-submit").click();

  await expect(page.getByTestId("start-today-learning")).toBeVisible();
  await page.getByTestId("start-today-learning").click();

  await expect(page.getByText("今日目标")).toBeVisible();
  await page.getByTestId("next-module").click();

  for (let index = 0; index < Math.max(wordCount, 1); index += 1) {
    const knownButton = page.getByTestId("word-choice-known");
    if (!(await knownButton.isVisible({ timeout: 2_000 }).catch(() => false))) break;
    await knownButton.click();
    await page.waitForTimeout(250);
  }

  if (!(await page.getByText("对话练习").isVisible().catch(() => false))) {
    await page.getByTestId("next-module").click();
  }
  await expect(page.getByText("对话练习")).toBeVisible();
  await page.getByTestId("next-module").click();

  await expect(page.getByText("知识讲解")).toBeVisible();
  await page.getByTestId("next-module").click();

  for (const answer of questionAnswers) {
    await page.getByTestId(`quiz-option-${answer}`).click();
  }

  await expect(page.getByText("学习总结")).toBeVisible();
  await page.getByTestId("complete-today-learning").click();
  await expect(page.getByText("今日完成")).toBeVisible();

  await page.getByTestId("celebration-continue").click();
  await expect(page.getByText("学习档案")).toBeVisible();
});
