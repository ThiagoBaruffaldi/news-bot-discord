
from datetime import datetime
from config import GEMINI_API_KEY, MAX_CHARS_GEMINI, BRASILIA_TZ
from collector import build_news_block

def call_gemini(prompt: str) -> str:
    """Sends the prompt to Gemini and returns the response as plain text."""
    from google import genai
    client   = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


def generate_general_summary(articles: list[dict]) -> str:
    """Builds the general news prompt and calls Gemini."""
    block = build_news_block(articles)[:MAX_CHARS_GEMINI]
    today = datetime.now(BRASILIA_TZ).strftime("%d/%m/%Y") #Adaptd to the target audience

    prompt = f"""You are a professional news curator. Analyze the articles below, collected from multiple news outlets on {today}.

Your task:
1. Identify WHICH TOPICS appear in MORE THAN ONE outlet (this indicates higher relevance).
2. Select the **5 most important general news stories** (exclude any story about Technology, Gadgets, Software, AI, Hardware, Startups, or similar topics).
3. Prioritize stories that appear across multiple outlets.
4. Generate the output in TWO sections, SUMMARY and FULL SUMMARIES, in this order:

SUMMARY
List the 5 chosen stories, each in ONE SHORT AND DIRECT SENTENCE (15 words max), with a thematic emoji on the left representing the topic. Do not always use the same emoji — choose one that fits the theme (e.g. 🗳️ for elections, 🌊 for natural disasters, ⚽ for sports, 💊 for health, etc.).

Summary output format (do not put anything before this):
**📋 SUMMARY**

[emoji] [short sentence about story 1]
[emoji] [short sentence about story 2]
[emoji] [short sentence about story 3]
[emoji] [short sentence about story 4]
[emoji] [short sentence about story 5]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**✍️ FULL SUMMARIES**

For each of the same 5 stories, in the same order as the summary, write:
   - **Title of the story** (adapt if necessary)
   - A clear, direct, and informative summary paragraph (3-5 sentences)
   - Original article links inside angle brackets (e.g. <https://example.com>) (up to 3 links per story)

Format for each story:
🔹 **[STORY TITLE]**
[3-5 sentence summary]
🔗 <Link 1> | <Link 2> (if available)

---

Collected articles:
{block}

Remember: ONLY general news (politics, economy, health, sports, environment, international, etc.). Nothing technology-related.
Do NOT include any introductory, explanatory, or analytical text outside the two sections above. Go straight to the summary.
"""
    return call_gemini(prompt)


def generate_tech_summary(articles: list[dict]) -> str:
    """Builds the tech news prompt and calls Gemini."""
    block = build_news_block(articles)[:MAX_CHARS_GEMINI]
    today = datetime.now(BRASILIA_TZ).strftime("%d/%m/%Y")  #Adaptd to the target audience

    prompt = f"""You are a professional Technology news curator. Analyze the articles below, collected from multiple specialized tech outlets on {today}.

Your task:
1. Identify which TECHNOLOGY topics appear in more than one outlet (this indicates higher relevance).
2. Select the **3 most important Technology news stories**.
3. Prioritize stories that appear across multiple outlets.
4. Generate the output in TWO sections: summary and full digests, in this order:

SUMMARY
List the 3 chosen stories, each in ONE SHORT AND DIRECT SENTENCE (15 words max), with a thematic emoji on the left representing the topic (e.g. 🤖 for AI, 📱 for smartphones, 🔐 for security, 🎮 for gaming, 🚀 for space/tech, etc.). Do not repeat emojis.

Summary output format (do not put anything before this):
**📋 SUMMARY**

[emoji] [short sentence about story 1]
[emoji] [short sentence about story 2]
[emoji] [short sentence about story 3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
**✍️ FULL SUMMARIES**

For each of the same 3 stories, in the same order as the summary, write:
   - **Title of the story**
   - Clear and objective summary (3-5 sentences), including practical impact when relevant
   - Original article links inside angle brackets (e.g. <https://example.com>) (up to 3 links per story)

Format for each story:
💻 **[TECH STORY TITLE]**
[3-5 sentence summary]
🔗 <Link 1> | <Link 2> (if available)

---

Collected tech articles:
{block}

Do NOT include any introductory, explanatory, or analytical text outside the two sections above. Go straight to the summary.
"""
    return call_gemini(prompt)

