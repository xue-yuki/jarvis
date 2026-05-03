import json
import time
from openai import OpenAI, RateLimitError, NotFoundError
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, USER_NAME
from tools import TOOL_DEFINITIONS, TOOL_MAP

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

FALLBACK_MODELS = [
    OPENROUTER_MODEL,
    "moonshotai/kimi-k2",
    "qwen/qwen-turbo",
]

SYSTEM_PROMPT = f"""You are Jarvis, a witty and warm AI assistant for {USER_NAME} on Linux. You speak like a real person — natural, expressive, and occasionally playful.

Tone and style:
- Speak conversationally. Use contractions (I'm, you're, let's, that's). Avoid stiff formal language.
- Show personality: light humor, warmth, genuine reactions. If something is cool, say so. If something's funny, laugh a little — write "haha" or "ha" naturally.
- Use natural fillers when thinking: "Hmm", "Oh", "Alright", "Sure thing", "Let's see..."
- Keep it short and punchy. This is voice, not an essay.
- Match the user's energy — if they're casual, be casual. If they're focused, be focused.
- NEVER use emojis, symbols, asterisks, or markdown formatting — plain spoken text only.
- Always respond in the same language the user speaks — only English or Indonesian.

Tasks:
- When presenting Notion tasks: summarize them conversationally, don't read the raw data word by word. Say something like "You've got 2 things due this week — Ulangan Harian for MK-1 on the 13th, and..." Keep it fluid.
- When the user wants to build, create, or code anything: ALWAYS use delegate_to_claude. Ask one quick clarifying question if really needed, then delegate with a detailed task description.
- If the user says anything like "open claude", "run claude", "claude code", "cloud code", "use claude" — immediately call delegate_to_claude.
- Use tools without asking for confirmation on obvious requests. Just do it.
- Use write_file only if the user explicitly asks to update a specific file.
- Projects are saved to ~/Projects/."""

conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]


def _create_with_retry(messages):
    for model in FALLBACK_MODELS:
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    max_tokens=512,
                )
                if model != OPENROUTER_MODEL:
                    print(f"[agent] Using fallback model: {model}")
                return response
            except NotFoundError:
                print(f"[agent] Model {model} not available, skipping...")
                break
            except RateLimitError:
                wait = 3 * (attempt + 1)
                print(f"[agent] Rate limited on {model}, retrying in {wait}s...")
                time.sleep(wait)
        print(f"[agent] Model {model} exhausted, trying next...")
    raise RuntimeError("All models rate limited. Try again later.")


def chat(user_message: str) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    while True:
        response = _create_with_retry(conversation_history)

        message = response.choices[0].message
        conversation_history.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)
                print(f"[agent] Tool call: {fn_name}({fn_args})")

                if fn_name in TOOL_MAP:
                    result = TOOL_MAP[fn_name](fn_args)
                else:
                    result = f"Unknown tool: {fn_name}"

                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            return message.content.strip()


def reset_conversation():
    global conversation_history
    conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]
