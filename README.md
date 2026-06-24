# AI Investment Radar

Free, lightweight AI-investment monitoring pipeline.

It collects RSS/Atom feeds, classifies items by investment-chain themes, writes a daily digest, uploads the digest as a GitHub Actions artifact, and can push the generated `dist/` output to a Gitee repository.

## Can GitHub Actions push artifacts to Gitee?

Yes. The workflow in `.github/workflows/daily-radar.yml` does three things:

1. Builds `dist/daily-digest.md` and `dist/daily-items.json`.
2. Uploads `dist/` as a GitHub Actions artifact.
3. If Gitee secrets are configured, commits `dist/` into a Gitee repository.

## Quick Start

```bash
python3 scripts/build_digest.py
```

Then open:

- `dist/daily-digest.md`
- `dist/daily-items.json`

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

After the digest is generated, paste `dist/daily-digest.md` into an AI assistant with:

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

