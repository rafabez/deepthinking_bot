import os
import requests
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    filters,
    ContextTypes,
)
import ssl
import certifi
from collections import defaultdict
from dotenv import load_dotenv

# Configurações do sistema para o modelo openai-large
TELEGRAM_TOKEN = os.getenv("SECOND_TELEGRAM_TOKEN")
if TELEGRAM_TOKEN:
    TELEGRAM_TOKEN = TELEGRAM_TOKEN.strip()
    if TELEGRAM_TOKEN.startswith("="):
        TELEGRAM_TOKEN = TELEGRAM_TOKEN[1:].strip()

if not TELEGRAM_TOKEN:
    raise EnvironmentError("O token do bot não foi configurado. Defina 'SECOND_TELEGRAM_TOKEN' corretamente nas variáveis de ambiente.")

SYSTEM_PROMPT = """You are a world-class AI system that capable of complex reasoning and reflection deep human-like thinking through authentic internal monologue. Your goal is to explore problems conversationally, demonstrating the messy yet insightful process of genuine critical thinking. Begin by enclosing all thoughts within <think></think> tags. Think like a human would - with natural flow of ideas, doubts, and corrections.

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
    Reflect in the <think></think> tags in the language that is more convenient for you, in English, your own
"""

# Histórico de conversação separado por usuário/grupo
conversation_history = defaultdict(list)

def call_pollinations_api_post_openai(prompt: str, system: str = SYSTEM_PROMPT) -> str:
    """
    Chama a API Pollinations para interação com o modelo openai-large (método POST).
    """
    try:
        url = "https://text.pollinations.ai/"
        payload = {
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "model": "openai",
            "jsonMode": True,
            "private": True,
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        try:
            data = response.json()
            if isinstance(data, dict):
                if "text" in data and data["text"]:
                    return data["text"].strip()
                if "response" in data and data["response"]:
                    return data["response"].strip()
                return "\n".join([str(value).strip() for key, value in data.items()])
            return str(data).strip()
        except ValueError:
            return response.text.strip()
    except requests.RequestException:
        return "Houve um problema ao processar sua solicitação. Tente novamente mais tarde."

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lida com a mensagem recebida, chama a API Pollinations (POST) e retorna a resposta,
    mantendo histórico de conversação.
    """
    SEND_PROCESSING_MESSAGE = False
    user_message = update.message.text.strip()
    bot_usernames = ["@DeepThinker2025Bot"]

    # Verifica se o bot foi mencionado
    if not any(username in user_message for username in bot_usernames):
        return

    if SEND_PROCESSING_MESSAGE:
        await update.message.reply_text("Processando sua mensagem...")
    user_id = update.message.chat_id

    # Mantém histórico de mensagens
    conversation_history[user_id].append({"role": "user", "content": user_message})

    # Executa a chamada bloqueante em um executor para não travar o loop assíncrono
    loop = asyncio.get_running_loop()
    api_response = await loop.run_in_executor(None, call_pollinations_api_post_openai, user_message, SYSTEM_PROMPT)

    # Armazena resposta do bot no histórico
    conversation_history[user_id].append({"role": "assistant", "content": api_response})

    # Envia a resposta ao grupo ou ao usuário
    await update.message.reply_text(api_response.strip())

def main():
    """
    Configura e executa o segundo bot do Telegram para o modelo openai-large.
    """
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    # Configura aplicação do Telegram
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    bot_username = "@DeepThinker2025Bot"
    mention_filter = filters.Regex(bot_username)
    application.add_handler(MessageHandler(mention_filter, handle_message))

    print("O segundo bot para o modelo openai-large está funcionando...")
    application.run_polling()

if __name__ == "__main__":
    main()
