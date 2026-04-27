# 📰 Discord Daily News Bot

A Discord bot that automatically collects news from multiple RSS feeds, uses Google Gemini AI to identify the most repeated stories across outlets, and posts a daily digest every morning at **6:00 AM (Brasília time)**. The digest includes a quick summary section followed by full breakdowns — separately for general news and technology.

> Built with Python. Hosted on Railway. Powered by Gemini 2.5 Flash.

---

## 🗂️ Project Structure

```
discord-news-bot/
├── news_bot.py        # Main bot file — all logic lives here
├── requirements.txt   # Python dependencies
├── Procfile           # Tells Railway how to start the bot
├── .gitignore         # Prevents sensitive files from being pushed to GitHub
└── .env               # Secret credentials — NOT pushed to GitHub
```

### `news_bot.py`
The core of the project. Contains:
- RSS feed collection from 22 sources (12 general, 10 tech)
- Gemini API integration for news analysis and summarization
- Discord bot setup with scheduled and on-demand digest posting
- Message chunking logic to respect Discord's 2000-character limit

### `requirements.txt`
Lists all Python libraries the project depends on. Railway reads this file automatically to install dependencies before running the bot.

### `Procfile`
Tells Railway's build system how to start the application. Uses `worker` (not `web`) because the bot does not serve HTTP requests.

### `.gitignore`
Prevents the `.env` file and `bot.log` from being accidentally pushed to GitHub, keeping your credentials safe.

### `.env` *(not included — create locally)*
Stores your secret credentials as environment variables. Never commit this file. On Railway, set these variables directly in the project's **Variables** tab.

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Your bot's token from the Discord Developer Portal |
| `GEMINI_API_KEY` | Your API key from Google AI Studio |
| `DISCORD_CHANNEL_ID` | Numeric ID of the Discord channel where the bot will post |

---

## 📦 Libraries Used

| Library | Purpose |
|---|---|
| `discord.py` | Discord bot framework |
| `feedparser` | Parses RSS feeds from news outlets |
| `google-generativeai` | Google Gemini API client |
| `apscheduler` | Schedules the daily 6 AM digest |
| `pytz` | Timezone handling (Brasília time) |
| `aiohttp` | Async HTTP support |
| `python-dotenv` | Loads environment variables from the `.env` file |

Install all dependencies with:

```bash
pip install discord.py feedparser google-generativeai apscheduler pytz aiohttp python-dotenv
```

---

## 🤖 AI Models Used

This project was built with the assistance of **Claude** (by Anthropic) in two configurations:

- **Claude Sonnet 4.6** — Used for general code generation, debugging, and iterative improvements throughout the development process.
- **Claude Sonnet 4.6 (Extended Thinking)** — Used for more complex reasoning tasks, such as designing the prompt structure and planning the overall bot architecture.

The bot itself uses **Gemini 2.5 Flash** (by Google) at runtime to analyze the collected RSS articles and generate the Portuguese-language news digests.

---

## 🚀 How to Run Locally

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install discord.py feedparser google-generativeai apscheduler pytz aiohttp python-dotenv
   ```
3. Create a `.env` file in the project root:
   ```
   DISCORD_TOKEN=your_token_here
   GEMINI_API_KEY=your_key_here
   DISCORD_CHANNEL_ID=your_channel_id_here
   ```
4. Run the bot:
   ```bash
   python news_bot.py
   ```

> ⚠️ The bot will stop if you close the terminal or shut down your computer. For 24/7 uptime, deploy to a cloud platform such as Railway.

---

## ☁️ Deploying to Railway

1. Push this repository to GitHub (keep it **private** to protect your code)
2. Go to [railway.app](https://railway.app) and create a new project linked to your GitHub repo
3. In the Railway project, go to the **Variables** tab and add the three environment variables listed above
4. Railway will detect the `Procfile` and `requirements.txt` automatically and deploy the bot

---

## 💬 Bot Commands

| Command | Description |
|---|---|
| `!summary` | Generates and posts the news digest immediately |
| `!status` | Shows the date and time of the next scheduled digest |
| `!help` | Lists all available commands |

---

## 📡 News Sources

**General (12 feeds):** G1, Folha de S.Paulo (World, Brazil, Economy), UOL, Agência Brasil, BBC Brasil, BBC News, The New York Times, Reuters, The Guardian, Sky News

**Technology (10 feeds):** Folha Tec, G1 Tecnologia, Tecmundo, TudoCelular, Olhar Digital, TechCrunch, Ars Technica, The Verge, Wired, CNET
