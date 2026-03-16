import os
from openai import OpenAI

OUTPUT_ORDER = [
    "twitter_thread",
    "linkedin_post",
    "instagram_caption",
    "short_video_script",
    "newsletter_summary",
]

PROMPTS = {
    "twitter_thread": """You are a social media writer who specialises in Twitter threads that feel human, not promotional.

Convert the following content into a Twitter thread.

Rules:
- Number each tweet as 1/ 2/ 3/ etc.
- First tweet is the hook: one sharp, specific insight or question that makes someone stop scrolling. No hype, no all-caps, no exclamation marks in the hook.
- Each tweet must be under 280 characters (count carefully).
- Write 6-8 tweets total.
- Tone: match the tone of the input — if it's calm and informative, stay calm and informative. Do NOT add excitement, urgency, or marketing energy that isn't in the original.
- No all-caps words. No words like "HUGE", "GAME-CHANGER", "CRUSH". No filler phrases like "let's dive in!" or "thread time 🧵".
- Every tweet should add new information — no padding or repetition.
- Hashtags: 0-1 per tweet, only if genuinely relevant. Do not force them.
- Last tweet: brief, grounded takeaway or a single genuine question to the reader.
-number tweets accurately — count your tweets before numbering them
-only use information present in the input — do not invent quotes, statistics, or personal anecdotes

Content:
{user_input}
""",

    "linkedin_post": """You are a writer who creates LinkedIn posts for individual creators and professionals — not brands or agencies.

Convert the following content into a LinkedIn post.

Rules:
- Write in first-person singular ("I", not "we" or "our team").
- Opening line: one sentence that earns the next click — a specific observation, a counterintuitive point, or a short story opener. Not a question like "Are you tired of...?".
- Body: 3-4 short paragraphs. Each paragraph is 1-3 sentences max. Use line breaks generously — LinkedIn compresses text.
- Tone: match the tone of the input. Professional but direct. No buzzwords like "game-changer", "revolutionize", "supercharge", or "leverage".
- Call to action: one natural question or prompt at the end. Not "Contact us" or "Click the link below".
- No bullet lists. No bold headers. Just clean paragraphs.
- No hashtags unless they appear naturally — LinkedIn over-hashtagging looks spammy.

Content:
{user_input}
""",

    "instagram_caption": """You are a copywriter who writes Instagram captions that are concise, real, and easy to read in the feed.

Convert the following content into an Instagram caption.

Rules:
- Opening line: short and punchy — 5-10 words max. This is what shows before "more" is tapped.
- Body: 2-4 short lines. Use line breaks between each line so it's easy to scan. Do NOT write a wall of text.
- Tone: match the tone of the input. Conversational, but not fake-enthusiastic. No all-caps words, no "GAME-CHANGER ALERT", no excessive exclamation marks.
- Hashtags: add 7-10 at the very end, separated from the caption by a blank line. Mix specific and broad tags. No invented hashtags.
- Total caption length (excluding hashtags): under 150 words.

Content:
{user_input}
""",

    "short_video_script": """You are a video scriptwriter for short-form content (TikTok, YouTube Shorts, Instagram Reels).

Convert the following content into a short video script.

Rules:
- Hook (0-3 seconds): one spoken sentence that creates immediate curiosity or relevance. Put it on its own line labeled [HOOK].
- Structure the rest with clear timestamp labels: [0-10s], [10-25s], [25-40s], [40-50s] etc.
- Include on-screen text or visual direction cues in square brackets on their own line, e.g. [Text on screen: "3 ways to save time"] or [Cut to: screen recording].
- Spoken words only go on lines without brackets — keep each spoken section natural and brief.
- Target spoken length: 45-55 seconds at a normal pace (~120 words of spoken content).
- Tone: match the tone of the input. Clear and informative — not hype-y or sales-y.
- End with a single, specific call to action (not "smash that like button").

Content:
{user_input}
""",

    "newsletter_summary": """You are an email writer who writes newsletter summaries that are clear, skimmable, and respect the reader's time.

Convert the following content into a newsletter summary section.

Rules:
- Subject line: write one on the first line, prefixed with "Subject: ". Make it specific and curiosity-driven — not generic ("This week in AI"). Under 50 characters.
- Opening sentence: one line that gives the reader the core idea immediately. No "Dear Creator" or formal greeting.
- Bullet points: 3-5 bullets. Each bullet is one clear, complete sentence. Start each with a bold 2-4 word label followed by a colon, e.g. "**Less platform juggling:** AI tools let you..."
- Takeaway: one final sentence prefixed with "Takeaway:" — the single most useful thing to remember.
- Tone: match the tone of the input. Informative and direct. No superlatives, no marketing fluff.
- Total length: under 200 words.

Content:
{user_input}
""",
}

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set.")
        _client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


def _get_model():
    return os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def generate_text(prompt: str) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model=_get_model(),
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    text = response.choices[0].message.content
    if not text:
        return "No content generated. Please try again."
    return text.strip()


def generate_all(user_input: str) -> dict[str, str]:
    outputs = {}
    for output_type in OUTPUT_ORDER:
        prompt = PROMPTS[output_type].format(user_input=user_input)
        outputs[output_type] = generate_text(prompt)
    return outputs