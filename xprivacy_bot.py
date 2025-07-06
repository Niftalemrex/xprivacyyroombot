import random
import os
from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from telegram import Update

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    print("Error: Telegram bot TOKEN not found in .env file!")
    exit(1)

# States for ConversationHandler
ASK_HER_NAME, ASK_HIS_NAME, MENU, ADD_TRUTH, ADD_DARE = range(5)

# Data storage (in-memory)
custom_truths = []
custom_dares = []
player_profiles = {}  # user_id -> {'her_name': str, 'his_name': str}
current_sessions = {}  # user_id -> session data (level, last challenge, unlocked, etc.)

LEVELS = {
    1: {"name": "Flirty Start", "emoji": "💋", "description": "Mildly suggestive questions and dares"},
    2: {"name": "Getting Hot", "emoji": "🔥", "description": "More explicit questions and physical dares"},
    3: {"name": "Nasty Mode", "emoji": "🍑", "description": "Graphic sexual questions and intimate dares"},
    4: {"name": "XXX Rated", "emoji": "🔞", "description": "Taboo topics and sexual acts"},
    5: {"name": "No Limits", "emoji": "🚨", "description": "Extreme fantasies and hardcore challenges"},
}

default_truths = {
    1: [
        "What's your favorite feature of {his} body?",
        "What's the sexiest outfit you've seen {her} wear?",
        "Where's the most unusual place you've kissed?",
        "What's your go-to move to initiate sex?",
        "Do you prefer making love or rough sex? Why?",
    ],
    2: [
        "What's your dirtiest sexual fantasy involving {her}?",
        "Have you ever faked an orgasm? Why?",
        "What's the most unusual place you've masturbated?",
        "Describe {her}'s body using only food metaphors.",
        "What's something sexual you've done that you're secretly proud of?",
    ],
    3: [
        "What's the kinkiest thing you've done that {his} doesn't know about?",
        "Have you ever been attracted to {her}'s friend? Details.",
        "What's your secret fetish you've never admitted?",
        "Describe your perfect sexual encounter in graphic detail.",
        "What's the most embarrassing thing that's happened during sex?",
    ],
    4: [
        "Have you ever fantasized about a threesome? Who would you include?",
        "What's the most taboo sexual thought you've ever had?",
        "Have you ever had sex with someone you shouldn't have? Who?",
        "What's the most degrading sexual thing you've done/enjoyed?",
        "Have you ever used sex toys? Which ones and how?",
    ],
    5: [
        "Would you try BDSM? What role would you take?",
        "Have you ever recorded yourself having sex? Would you?",
        "What's your ultimate no-holds-barred fantasy?",
        "Would you have sex with someone watching? Who?",
        "What's the most extreme sexual act you'd try with your partner?",
    ],
}

default_dares = {
    1: [
        "Kiss your partner passionately for 20 seconds",
        "Whisper something sexy in your partner's ear",
        "Send a flirty selfie with a sexy caption",
        "Describe what you want to do to your partner later",
        "Play with your partner's hair sensually for 1 minute",
    ],
    2: [
        "Send a voice message moaning your partner's name",
        "Let your partner choose what you wear tonight",
        "Write your partner's name on your body and send proof",
        "Describe your last orgasm in detail",
        "Give your partner a sensual massage for 5 minutes",
    ],
    3: [
        "Perform a 30-second striptease for your partner",
        "Tell your partner where you want to be touched right now",
        "Send a photo of your sexiest body part",
        "Let your partner control your vibrator for 2 minutes",
        "Describe your dirtiest fantasy in a voice message",
    ],
    4: [
        "Have phone sex with your partner right now",
        "Take a naughty photo in a risky place (bathroom, etc.)",
        "Tell your partner your most taboo desire",
        "Masturbate while describing it to your partner",
        "Let your partner choose your underwear for 24 hours",
    ],
    5: [
        "Have orgasm control play - partner decides when you cum",
        "Do a sexual favor your partner chooses (within limits)",
        "Try a new kink your partner suggests tonight",
        "Send a video of yourself doing something naughty",
        "Roleplay your partner's fantasy via text/voice",
    ],
}

extreme_truths = [
    "Would you do a sex tape with your partner? What scenes?",
    "Have you ever had public sex? Where and how?",
    "What's the most people you've had sex with at once?",
    "Would you try partner swapping? Under what conditions?",
    "What's your ultimate degradation fantasy?",
]

extreme_dares = [
    "Let your partner tie you up for 10 minutes (safely)",
    "Do a sexual act while video calling your partner",
    "Wear a remote-controlled toy in public for 1 hour",
    "Try anal play (giving or receiving) tonight",
    "Give your partner complete control over your orgasms for 24h",
]

def get_names(user_id):
    profile = player_profiles.get(user_id, {})
    her = profile.get("her_name", "her")
    his = profile.get("his_name", "his")
    return her, his

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        "🔥 Welcome to XPrivacyRoomBot - The Ultimate Couples Game (18+ ONLY) 🔥\n\n"
        "To start, please tell me *HER* name (the female partner):",
        parse_mode='Markdown'
    )
    return ASK_HER_NAME

async def get_her_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    her_name = update.message.text.strip()
    player_profiles[user_id] = {"her_name": her_name}
    await update.message.reply_text(f"Got it! Now tell me *HIS* name (the male partner):", parse_mode='Markdown')
    return ASK_HIS_NAME

async def get_his_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    his_name = update.message.text.strip()
    player_profiles[user_id]["his_name"] = his_name
    current_sessions[user_id] = {
        "level": 1,
        "last_challenge": None,
        "extreme_unlocked": False,
        "custom_truths_asked": [],
        "custom_dares_asked": [],
    }
    her, his = get_names(user_id)
    await update.message.reply_text(
        f"Perfect! You are now set as:\n💃 *{her}* & 🕺 *{his}*\n\n"
        "Use the following commands to play:\n"
        "/begin - Start the game\n"
        "/truth - Get a truth question\n"
        "/dare - Get a dare\n"
        "/addtruth - Add your own spicy truth\n"
        "/adddare - Add your own naughty dare\n"
        "/levelup - Increase game intensity\n"
        "/cancel - End the game\n"
        "/help - Show this help message\n\n"
        "Type /begin when you're ready!",
        parse_mode='Markdown'
    )
    return MENU

async def begin_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in player_profiles:
        await update.message.reply_text("Please start with /start first.")
        return MENU
    level = current_sessions[user_id]["level"]
    her, his = get_names(user_id)
    await update.message.reply_text(
        f"Let's start the fun!\n\n"
        f"You're at Level {level} {LEVELS[level]['emoji']} - *{LEVELS[level]['name']}*\n"
        f"{LEVELS[level]['description']}\n\n"
        "Get ready for your first challenge...",
        parse_mode='Markdown'
    )
    await send_challenge(update, context)
    return MENU

async def send_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    session = current_sessions.get(user_id)
    if not session:
        await update.message.reply_text("Please start with /start first.")
        return

    level = session["level"]
    her, his = get_names(user_id)

    if session["last_challenge"] == "truth":
        challenge_type = "dare"
    else:
        challenge_type = "truth"

    if challenge_type == "truth":
        pool = default_truths.get(level, default_truths[5]) + custom_truths
        if session["extreme_unlocked"]:
            pool += extreme_truths
        pool = [q for q in pool if q not in session["custom_truths_asked"]]
        if not pool:
            session["custom_truths_asked"] = []
            pool = default_truths.get(level, default_truths[5]) + custom_truths
            if session["extreme_unlocked"]:
                pool += extreme_truths
        challenge = random.choice(pool)
        session["custom_truths_asked"].append(challenge)
        text = challenge.format(her=her, his=his)
        prefix = f"{LEVELS[level]['emoji']} *TRUTH (Level {level})*:" if challenge not in extreme_truths else "🚨 *EXTREME TRUTH:*"
    else:
        pool = default_dares.get(level, default_dares[5]) + custom_dares
        if session["extreme_unlocked"]:
            pool += extreme_dares
        pool = [d for d in pool if d not in session["custom_dares_asked"]]
        if not pool:
            session["custom_dares_asked"] = []
            pool = default_dares.get(level, default_dares[5]) + custom_dares
            if session["extreme_unlocked"]:
                pool += extreme_dares
        challenge = random.choice(pool)
        session["custom_dares_asked"].append(challenge)
        text = challenge.format(her=her, his=his)
        prefix = f"{LEVELS[level]['emoji']} *DARE (Level {level})*:" if challenge not in extreme_dares else "🚨 *EXTREME DARE:*"

    await update.message.reply_text(f"{prefix}\n\n{text}", parse_mode='Markdown')
    session["last_challenge"] = challenge_type

async def truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in current_sessions:
        await update.message.reply_text("Please start the game first with /start.")
        return
    current_sessions[user_id]["last_challenge"] = "truth"  # so next is dare
    await send_challenge(update, context)

async def dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in current_sessions:
        await update.message.reply_text("Please start the game first with /start.")
        return
    current_sessions[user_id]["last_challenge"] = "dare"  # so next is truth
    await send_challenge(update, context)

async def levelup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in current_sessions:
        await update.message.reply_text("Please start the game first with /start.")
        return
    session = current_sessions[user_id]
    level = session["level"]
    if level < 5:
        session["level"] = level + 1
        await update.message.reply_text(
            f"🎉 Level up! You are now at Level {session['level']} {LEVELS[session['level']]['emoji']} - {LEVELS[session['level']]['name']}.\n"
            f"{LEVELS[session['level']]['description']}"
        )
    elif not session["extreme_unlocked"]:
        session["extreme_unlocked"] = True
        await update.message.reply_text(
            "💥 Extreme Mode UNLOCKED! Prepare for the wildest truths and dares! 💥"
        )
    else:
        await update.message.reply_text("You're already at maximum level and Extreme Mode!")

async def add_truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🖋️ Please type your custom *Truth* question.\n"
        "Make it spicy and creative!\n"
        "Send your text now:",
        parse_mode='Markdown'
    )
    return ADD_TRUTH

async def save_truth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 10:
        await update.message.reply_text("Too short! Please enter at least 10 characters:")
        return ADD_TRUTH
    custom_truths.append(text)
    await update.message.reply_text("✅ Your custom truth has been added!")
    return MENU

async def add_dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🖋️ Please type your custom *Dare* challenge.\n"
        "Make it naughty but safe!\n"
        "Send your text now:",
        parse_mode='Markdown'
    )
    return ADD_DARE

async def save_dare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if len(text) < 10:
        await update.message.reply_text("Too short! Please enter at least 10 characters:")
        return ADD_DARE
    custom_dares.append(text)
    await update.message.reply_text("✅ Your custom dare has been added!")
    return MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in current_sessions:
        del current_sessions[user_id]
    await update.message.reply_text("Game ended. Type /start to play again!")
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Commands:\n"
        "/start - Setup names and start\n"
        "/begin - Start playing\n"
        "/truth - Get a truth question\n"
        "/dare - Get a dare challenge\n"
        "/addtruth - Add a custom truth\n"
        "/adddare - Add a custom dare\n"
        "/levelup - Increase intensity\n"
        "/cancel - End the game\n"
        "/help - Show this message"
    )

def main():
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ASK_HER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_her_name)],
            ASK_HIS_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_his_name)],
            MENU: [
                CommandHandler('begin', begin_game),
                CommandHandler('truth', truth),
                CommandHandler('dare', dare),
                CommandHandler('addtruth', add_truth),
                CommandHandler('adddare', add_dare),
                CommandHandler('levelup', levelup),
                CommandHandler('help', help_command),
            ],
            ADD_TRUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_truth)],
            ADD_DARE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_dare)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('help', help_command))

    print("Bot started...")
    application.run_polling()

if __name__ == '__main__':
    main()