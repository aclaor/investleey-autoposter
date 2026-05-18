[README.md](https://github.com/user-attachments/files/27939132/README.md)
# Investleey FB Auto-Poster

Posts AI stock forecasts to your Facebook page every 4 hours automatically using GitHub Actions.

## Setup

### 1. Create GitHub Repo
Create a new **private** repo called `investleey-autoposter`
Upload both files:
- `poster.py`
- `.github/workflows/post.yml`

### 2. Add GitHub Secrets
Go to repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these 4 secrets:

| Secret Name | Value |
|-------------|-------|
| `FB_PAGE_ACCESS_TOKEN` | Your Facebook Page Access Token |
| `FB_PAGE_ID` | `103114287835428` |
| `STOCK_API_URL` | `https://stockvision-production-ae61.up.railway.app` |
| `STOCK_API_TOKEN` | `mystockvision2025` |

### 3. Get Facebook Page Token
1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app → select your page
3. Add permissions: `pages_manage_posts`, `pages_read_engagement`
4. Generate token → copy it
5. **Important**: Get a long-lived token (60 days) or permanent token

### 4. Enable Actions
Go to repo → **Actions** tab → Enable workflows

### 5. Test Manually
Go to **Actions** → **Investleey FB Auto-Post** → **Run workflow**

## Schedule
Posts automatically at: 12am, 4am, 8am, 12pm, 4pm, 8pm UTC
(Every 4 hours)

## What Gets Posted
- Random stock from watchlist (weighted toward high-volume)
- Current price
- AI forecast for MA-3, MA-7, MA-25, VWAP lines
- 7-day and 30-day price targets
- Accuracy scores
- Link back to investleey.com
- Hashtags for reach
