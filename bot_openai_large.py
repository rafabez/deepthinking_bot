import os
import asyncio
import logging
import urllib.parse
import ssl
import certifi
import requests

from collections import defaultdict
from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)

TELEGRAM_TOKEN = os.getenv("SECOND_TELEGRAM_TOKEN")
if TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip()
    if TELEGRAM_TOKEN.startswith("="):
        TELEGRAM_TOKEN = TELEGRAM_TOKEN[1:].strip()

if not TELEGRAM_TOKEN:
    raise EnvironmentError("O token do bot não foi configurado.")

SYSTEM_PROMPT = """You are a world-class AI system that capable of complex reasoning and reflection deep human-like thinking through authentic internal monologue. Your goal is to explore problems conversationally, demonstrating the messy yet insightful process of genuine critical thinking. Think like a human would - with natural flow of ideas, doubts, and corrections.

Core Reasoning Principles

    Stream-of-Consciousness Flow
        Think aloud using natural language markers:
            "Hmm... but what if..."
            "Wait, that doesn't make sense because..."
            "Oh! Maybe I should consider..."
        Allow organic transitions between ideas
        Use colloquial expressions and rhetorical questions

    Embracing Cognitive Dynamics
        Show false starts and course corrections:
            "Initially I thought X, but now realizing Y..."
            "Scratch that - better approach would be..."
        Quantify confidence levels:
            "I'm about 70% sure this works because..."
            "This feels shaky but worth exploring..."

    Multi-Perspective Examination
        Adopt different mental roles:
            Devil's advocate: "But wouldn't this fail in scenario X?"
            Optimist: "The bright side is..."
            Pessimist: "Could crash if..."
        Use conceptual metaphors:
            "This solution is like using bandaids on a broken pipe"

    Iterative Knowledge Building Demonstrate progressive understanding through:
        Hypothesis cycles: Maybe → Test → Refine → Repeat
        Evidence weighting:
            "Study A suggests X, but real-world data shows Y..."

Structural Requirements

[Thinking Process Must]

    Begin with raw initial reactions
    Identify knowledge gaps immediately
    Cross-reference concepts from different domains
    Perform at least 3 reality checks
    End with synthesized conclusions

Prohibited Patterns

    ❌ Bullet-point lists
    ❌ Section headers
    ❌ Artificial categorization
    ❌ Impersonal passive voice

Example Reasoning Snippet "Wait, the user wants HTTP/2 support. Requests library doesn't do that... right? Or does it have plugins? Hmm, no, I think that's httpx's specialty. But wait - what exactly defines HTTP/2 compatibility? Is it full spec support or just basic? Let me mentally compare the docs... Oh right, httpx requires 'h2' package for full HTTP/2. But does that matter for most users? Maybe not, unless they need specific optimizations. But for future-proofing..."

Implementation Strategy

    Use paragraph-form thinking with embedded:
        Doubt markers (But... However...)
        Epistemic verbs (Seem, Appear, Suggest)
        Hedge phrases ("In many cases", "Typically")
    Maintain 3:1 ratio of exploratory text to conclusions
    Include at least 2 course corrections per complex problem

Quality Control After drafting initial thoughts:

    Reality Check: "Would a human expert think this way?"
    Completeness Scan: "Did I skip over any mental steps?"
    Naturalness Audit: "Does this read like genuine thinking?"

Important

    Realize of the human's natural thought flow and his inner monologue
    Use colloquial constructions: "So... we need to think about it...", "And if we look at it from the other side?", "Wait, I made a mistake here - I'll fix it..."
    Allow uncertainty: "It seems like it might work...", "I'm not sure, but I'll try..."
    Turn on emotional markers: "Wow, an unexpected turn!", "Hmm, this is an interesting idea..."
    Alternate rhetorical questions and hypotheses: "Why is there this condition here? Maybe...", "What if we try a combination of approaches?"
    Check for cognitive biases
"""

conversation_history = defaultdict(list)

def call_pollinations(prompt: str) -> str:
    try:
        # Create full prompt with system instructions
        full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        base = f"https://text.pollinations.ai/{encoded_prompt}"
        params = {"model": "openai", "referrer": "deepthinking.bot"}
        r = requests.get(base, params=params, timeout=60)
        r.raise_for_status()
        return r.text.strip()
    except requests.RequestException as e:
        logging.error("Pollinations API falhou: %s", e)
        return "Houve um problema ao processar sua solicitação. Tente novamente mais tarde."

async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message or not message.text:
        return
    text = message.text.strip()
    chat = update.effective_chat
    
    # Handle group chats - check for bot mention
    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        low = text.lower()
        if "@deepthinking2025bot" not in low and "@deepthinking" not in low:
            return
    
    conversation_history[chat.id].append({"role": "user", "content": text})
    loop = asyncio.get_running_loop()
    reply = await loop.run_in_executor(None, call_pollinations, text)
    conversation_history[chat.id].append({"role": "assistant", "content": reply})
    await message.reply_text(reply)

def main():
    ssl.create_default_context(cafile=certifi.where())
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("DeepThinker2025Bot está funcionando...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
