# Pylon Daily — putting it online

Everything for the website is in this folder. These steps take about 30–45 minutes, once.
You'll end up with the game at **https://pylondaily.com**, stats that refresh themselves every morning,
the "you beat X% of players" line, visitor counts, and the site listed on Google.

| File | What it is |
|---|---|
| `index.html` | the game |
| `about.html` | About & privacy page (linked in the game's footer) |
| `data.json` | today's player stats; rebuilt every morning by the update job |
| `tools/build_data.py` | the script that rebuilds `data.json` from nflverse |
| `.github/workflows/update-data.yml` | the daily update job (a copy is in `tools/update-data.yml.txt`) |
| `functions/api/daily.js` | counts Daily results for "you beat X% of players" |
| `og.png`, `icon-*.png`, `favicon-32.png`, `apple-touch-icon.png`, `manifest.webmanifest` | link previews, icons, "Add to Home Screen" |
| `robots.txt`, `sitemap.xml` | help Google find the pages |

## 1. Buy the domain (Cloudflare)
1. Make a free account at **dash.cloudflare.com**.
2. Left menu: **Domain Registration → Register Domains**. Search `pylondaily.com` and buy it (Cloudflare charges cost price, about $10–11 a year).

## 2. Put the files on GitHub (free)
GitHub stores the files and runs the daily stats update.
1. Make a free account at **github.com**.
2. Click **+ → New repository**. Name it `pylondaily`, choose **Public**, click **Create repository**.
3. On the new repository page click **uploading an existing file**. Unzip `pylon-daily-site.zip`, open the
   `pylon-daily` folder, select everything inside it and drag it onto the page. Click **Commit changes**.
4. Make sure the update job made it (computers often hide folders starting with a dot):
   open the repository's **Actions** tab. If you don't see **Update player data**, click **Add file → Create new file**,
   type the name `.github/workflows/update-data.yml`, paste in everything from `tools/update-data.yml.txt`,
   and click **Commit changes**.

## 3. Turn on the website (Cloudflare Pages)
1. In Cloudflare: **Workers & Pages → Create → Pages → Connect to Git**. Connect your GitHub account and pick `pylondaily`.
2. Settings: **Framework preset: None**. Leave **Build command** empty. **Build output directory:** `/`.
3. Click **Save and Deploy**. In a minute the game is live at `pylondaily.pages.dev`.
4. In the Pages project: **Custom domains → Set up a custom domain** → `pylondaily.com` → **Activate**.
   Add `www.pylondaily.com` the same way.

From now on, every change on GitHub (including the daily stats update) puts a new version online automatically.

## 4. "You beat X% of players today"
1. Cloudflare: **Storage & Databases → KV → Create** a namespace called `pylon-stats`.
2. Pages project: **Settings → Bindings → Add → KV namespace**. Variable name **`HM_STATS`**, namespace `pylon-stats`. Save.
3. **Deployments → … → Retry deployment** so it picks up the binding.

## 5. Visitor counts
Pages project: **Metrics → Web Analytics → Enable**. That's it: page views and visitors, no cookies, no banner needed.

## 6. Start the daily stats update
GitHub repository: **Actions → Update player data → Run workflow**. After a minute you should see a green check and,
if new games have been played, a commit called "Update player data: … through Week N". It then runs by itself every
morning at about 6:15 a.m. Eastern. (GitHub pauses scheduled jobs after 60 days with no activity, e.g. in the
offseason; it emails you, and one click on **Enable workflow** turns it back on.)

## 7. Get on Google
1. Go to **search.google.com/search-console**, **Add property → Domain** → `pylondaily.com`.
2. Google shows a TXT record. Choose the Cloudflare option to add it automatically (or paste it in Cloudflare **DNS → Records**).
3. Once verified: **Sitemaps** → enter `sitemap.xml` → **Submit**.
   Google usually starts showing the site within a few days to a couple of weeks.

## Good to know
- The game turns on the hosted extras (stats refresh, the % counter, the link in shared results) only when it runs
  on `pylondaily.com` or `*.pages.dev`.
- Suggestions email you through Web3Forms (already connected: `SUGGEST_KEY` in `index.html`).
- Owner tools: sign in as `joe disney 5678` for Reset Daily and Start fresh (they only affect your own device).
