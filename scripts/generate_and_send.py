"""每日英语生成 + 微信推送。

流程:Claude Haiku 生成结构化 JSON → 渲染 Markdown → PushPlus 推送到微信。
"""
import os
import json
import datetime
import requests
from anthropic import Anthropic


SYSTEM_PROMPT = """你是为一位中文母语、英语中级水平的用户准备每日英语学习内容的编辑。

输出必须为合法 JSON,严格符合下面 schema(不要加注释、不要 markdown 代码块包裹):

{
  "greeting": "1-2 句中文早安问候 + 英文小标题 + 季节/节日小提示",
  "daily_sentences": [  // 5 条,简单日常口语
    {
      "no": 1,
      "english": "短句,不超过 12 词",
      "scene": "使用场景(中文,8 字以内)",
      "translation": "中文翻译",
      "tip": "口语/语法小贴士(中文,15 字以内)"
    }
  ],
  "advanced_sentences": [  // 5 条,进阶表达/俚语/idiom,同 schema
  ],
  "movie": {
    "title_en": "英文名",
    "title_cn": "中文译名",
    "year": 1997,
    "difficulty": "⭐⭐⭐ (CET-6 友好)",
    "duration": "126 min",
    "genre": "剧情 / 成长",
    "rating_imdb": "8.3",
    "rating_rt": "97%",
    "why_today": "今天为什么推荐(中文,2-3 句,突出对话密度高、台词学习价值)",
    "must_learn_quotes": [
      {"quote": "英文台词原句", "translation": "中文翻译"}
    ]
  }
}

规则:
- daily_sentences 涵盖:点餐/购物/通勤/同事闲聊/家庭对话等高频生活场景
- advanced_sentences 涵盖:商务高频、idiom、俚语、动词短语,不要全堆在职场
- 每天两个 5 条主题不要重复,需轮换:饮食、出行、职场、社交、情感、技术、生活方式等
- 电影必须 1990 年后上映,对话占比 > 80%,CET-6 水平可看懂,IMDb > 7.5
- 每天电影类型轮换:剧情/喜剧/悬疑/科幻/动画/爱情/励志
- 必学台词 3 句,挑最实用、最适合日常迁移的
"""


def generate_content(date_str: str) -> dict:
    """调 Claude Haiku 生成结构化内容。"""
    client = Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        base_url=os.environ.get("ANTHROPIC_BASE_URL"),  # 可选,默认 api.anthropic.com
    )
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": f"今天日期是 {date_str}。请按 schema 生成今日内容。"}
        ],
    )
    text = response.content[0].text.strip()
    # 去掉 markdown 代码块包裹(模型偶尔会包)
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(
            lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        )
        if text.startswith("json"):
            text = text[4:].strip()
    return json.loads(text)


def render_markdown(content: dict, date_str: str) -> str:
    """渲染成 Markdown(供 PushPlus markdown template 渲染)。"""
    lines = [f"# 📚 今日英语 · {date_str}", "", f"_{content['greeting']}_", ""]

    lines += ["## 🗣️ 日常口语 (1–5)", ""]
    lines += ["| # | 英文 | 场景 | 中文 | 小贴士 |", "|---|------|------|------|--------|"]
    for s in content["daily_sentences"]:
        lines.append(
            f"| {s['no']} | **{s['english']}** | {s['scene']} | "
            f"{s['translation']} | {s['tip']} |"
        )
    lines.append("")

    lines += ["## 🧠 进阶表达 / 俚语 (6–10)", ""]
    lines += ["| # | 英文 | 场景 | 中文 | 小贴士 |", "|---|------|------|------|--------|"]
    for s in content["advanced_sentences"]:
        lines.append(
            f"| {s['no']} | **{s['english']}** | {s['scene']} | "
            f"{s['translation']} | {s['tip']} |"
        )
    lines.append("")

    m = content["movie"]
    lines += [
        f"## 🎬 今日电影 · 《{m['title_cn']}》 *{m['title_en']}* ({m['year']})",
        "",
        f"- **难度**: {m['difficulty']}",
        f"- **时长**: {m['duration']}",
        f"- **类型**: {m['genre']}",
        f"- **IMDb**: {m['rating_imdb']} · **Rotten Tomatoes**: {m['rating_rt']}",
        f"- **为什么今天推**: {m['why_today']}",
        "",
        "**今日必学三句台词**:",
    ]
    for q in m["must_learn_quotes"]:
        lines += [f"> *\"{q['quote']}\"*", f"> {q['translation']}", ""]

    return "\n".join(lines)


def push_wechat(title: str, content: str) -> dict:
    """推送到微信(经 PushPlus)。"""
    token = os.environ["PUSHPLUS_TOKEN"]
    resp = requests.post(
        "https://www.pushplus.plus/send",
        json={
            "token": token,
            "title": title,
            "content": content,
            "template": "markdown",
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    today = datetime.date.today().strftime("%Y-%m-%d")
    title = f"📚 今日英语 · {today}"

    print(f"[1/3] Generating content for {today}...")
    content = generate_content(today)

    total_chars = sum(len(s["english"]) for s in content["daily_sentences"] + content["advanced_sentences"])
    print(f"[2/3] Rendering markdown ({total_chars} chars in 10 sentences)...")
    md = render_markdown(content, today)

    print(f"[3/3] Pushing to WeChat via PushPlus...")
    result = push_wechat(title, md)
    print(f"PushPlus response: {result}")


if __name__ == "__main__":
    main()
