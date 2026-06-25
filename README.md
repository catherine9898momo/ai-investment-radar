# AI Investment Radar

Free, lightweight AI-investment monitoring pipeline.

It collects RSS/Atom feeds, classifies items by investment-chain themes, writes a daily digest, uploads the digest as a GitHub Actions artifact, and can push the generated `dist/` output to a Gitee repository.

## Can GitHub Actions push artifacts to Gitee?

Yes. The workflow in `.github/workflows/daily-radar.yml` does four things:

1. Builds dated files such as `dist/daily-digest-YYYY-MM-DD.md`, `dist/daily-digest-YYYY-MM-DD.zh.md`, `dist/daily-concept-YYYY-MM-DD.zh.md`, and `dist/daily-items-YYYY-MM-DD.json`.
2. Uploads `dist/` as a GitHub Actions artifact.
3. Commits generated `dist/` files back to the GitHub repository.
4. If Gitee secrets are configured, syncs `dist/` into a Gitee repository.

`dist/` stays ignored for local development, but the workflow force-adds it during the automated daily commit.

## Quick Start

```bash
python3 scripts/build_digest.py
```

Then open:

- `dist/daily-digest-YYYY-MM-DD.zh.md` for the Chinese market reading report with Chinese summaries, reading focus points, and original source summaries
- `dist/daily-concept-YYYY-MM-DD.zh.md` for one daily value-investing book/chapter lesson and execution exercise
- `dist/value-investing-progress-YYYY-MM-DD.json` for the dated learning route state used to avoid repeating the same daily concept
- `dist/daily-digest-YYYY-MM-DD.md` for the English report
- `dist/daily-items-YYYY-MM-DD.json` for structured data

## Daily Value-Investing Course

The Chinese daily course follows the supplied Buffett/Munger study list route A: `The Intelligent Investor`, `Common Stocks and Uncommon Profits`, `The Essays of Warren Buffett`, `The Outsiders`, `Security Analysis`, and `Poor Charlie's Almanack`.

The workflow stores progress in dated snapshots such as `dist/value-investing-progress-YYYY-MM-DD.json` and loads the latest snapshot on the next run. Running it again on the same date keeps the same lesson. Running it on a later date advances to the next lesson; when the current book's prepared lessons are finished, the next report moves to the next book in the route. After the whole prepared route finishes, the progress round advances and the route starts again for review unless more lessons are added.

## Configure Feeds

Edit `config/feeds.json`.

Good feed sources:

- Company investor relations RSS/Atom feeds
- SEC Atom feeds
- Google News RSS searches
- Industry sites with RSS
- Your own RSSHub feeds, if you run RSSHub

## GitHub Secrets For Gitee Push

Create a Gitee repository first, then add these GitHub repository secrets:

| Secret | Example | Purpose |
|---|---|---|
| `GITEE_USERNAME` | `your-gitee-name` | Gitee login name |
| `GITEE_TOKEN` | `xxxxx` | Gitee personal access token with repo write permission |
| `GITEE_REPO` | `your-gitee-name/ai-investment-radar-output` | Target Gitee repo path without `.git` |

If these secrets are missing, the workflow still builds the digest and uploads the GitHub artifact, but skips the Gitee push.

## Daily Review Prompt

After the digest is generated, paste the latest `dist/daily-digest-YYYY-MM-DD.md` into an AI assistant with:

```text
Please summarize this AI investment digest into:
1. Top 3 hard signals
2. Top 3 risk signals
3. Which part of the AI value chain changed
4. Companies affected
5. Follow-up verification points
Only use facts from the digest.
```

## Weekly Review Questions

- Is AI capex still flowing into the chain?
- Where is the newest bottleneck: chips, HBM, packaging, networking, power, data centers, or applications?
- Are downstream companies turning AI into paid products?
- Are valuations already pricing in the good news?
- Which thesis was weakened by facts this week?

