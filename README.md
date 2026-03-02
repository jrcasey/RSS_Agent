# RSS_Agent

![RSS Agent Logo](./Logo.jpg)

RSS_Agent is an automated weekly RSS reader and article ranking system that I put together for my own interests. I was tired to leafing through hundreds of articles daily from all of the journals I follow, and thought a LLM would do as good a job as my tired eyes. *I'm usually pretty anti-chatbot but man this is a clear use-case*. Probably others have done this as well but I couldn't find anything. My interests are in microbial oceanography, biogeochemistry, systems biology, and computational biology, but you can easily change the prompt to whatever float your boat. It fetches articles, ranks them using an LLM, filters top results, archives previous weeks, and emails you a curated list. I also have a local `launchctl` script to fetch results to my Obsidian Vault on Monday mornings for coffee reading. 

## Features

- Fetches articles from RSS/Atom feeds listed in `feeds.txt`
- Prevents re-processing by storing previously-seen article IDs in `cache/seen_ids.json`
- Combines title + abstract (`content`) for ranking. The agent comes up with a score for how related an article is to my various interests. Black Magic 🪄🎩
- Filters results by score threshold or top N results (I set a limit because keeping up with the literature is a marathon, not a sprint)
- Outputs weekly results in `curated_latest.md`
- Automatically archives last week’s results as `curated_YYYYMMDD.md`
- Automatically emails weekly curated results
- Fully automated via GitHub Actions (and launchd if you want)

## Installation

```bash
git clone https://github.com/jrcasey/RSS_Agent
cd RSS_Agent
pip install -r requirements.txt
```

Create a `feeds.txt` file in the project root, one feed URL per line.

## Email Setup

To send weekly results by email, set the following secrets in GitHub:

- `SMTP_HOST` – e.g. smtp.gmail.com  
- `SMTP_PORT` – usually 587  
- `SMTP_USER` – your email login  
- `SMTP_PASS` – **an SMTP app password**

### What is an SMTP app password?

Some email providers (e.g., Gmail, Outlook) block regular passwords for automated scripts.  
An **SMTP app password** is a special password you generate for a specific application.  
You use it instead of your real password when sending mail programmatically.

For Gmail:

1. Enable 2‑factor authentication  
2. Visit: https://myaccount.google.com/apppasswords  
3. Create a new app password  
4. Use that password as `SMTP_PASS`

For other clients: idk sorry!

## Automating with GitHub Actions

Two workflow files (`.github/workflows/rss_agent.yml` and `.github/workflows/daily_fetch.yml`) are provided. The daily frequency is there to avoid missing articles that exceed the limit for a feed.

Daily:

- Runs daily
- Fetches articles from all RSS feeds.
- Appends to raw_feeds.json
- Appends to seen_ids.txt

Weekly:

- Runs weekly
- Fetches and ranks new articles
- Archives the last week’s results
- Emails the new curated list
- Commits updates to the repo
- Deletes this week's raw_feeds.json articles but leaves seen_ids.txt to accumulate. 

Ensure you configure repository secrets before enabling the workflow.

## Output

- `output/curated_latest.md` — most recent curated articles  
- `archive/curated_YYYYMMDD.md` — archived weekly snapshot  
- `archive/raw_feeds_last_week.json` - all of last week's articles, for review purposes
- `cache/seen_ids.json` — tracking previously processed article IDs  
- `cache/ranked_results.json` — full ranking logs

## License

MIT

## ToDo's
- [ ] Add some more keys for retrieving abstracts from different feeds. They all seem to have their own peculiarities! 
- [ ] Put my interests in some text file in the root to make it easier for others to customize their own agents. Probably some better prompt engineering would be warranted as well 🫠
- [ ] Add journal names to `feeds.txt` with # comments on their own lines.

