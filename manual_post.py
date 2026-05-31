"""
Manual Multi-Platform Poster
Triggered manually from GitHub Actions with custom message + image
"""
import os, requests, base64, time

MESSAGE   = os.environ.get("MESSAGE", "")
IMAGE_URL = os.environ.get("IMAGE_URL", "").strip()
PLATFORMS = os.environ.get("PLATFORMS", "all")

FB_TOKEN        = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
FB_PAGE_ID      = os.environ.get("FB_PAGE_ID", "")
IG_USER_ID      = os.environ.get("IG_USER_ID", "")
IMGBB_KEY       = os.environ.get("IMGBB_API_KEY", "")
TG_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHANNEL_ID   = os.environ.get("TELEGRAM_CHANNEL_ID", "")
PIN_TOKEN       = os.environ.get("PINTEREST_TOKEN", "")
PIN_BOARD_ID    = os.environ.get("PINTEREST_BOARD_ID", "")
TW_API_KEY      = os.environ.get("TWITTER_API_KEY", "")
TW_API_SECRET   = os.environ.get("TWITTER_API_SECRET", "")
TW_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TW_ACCESS_SECRET= os.environ.get("TWITTER_ACCESS_SECRET", "")

results = []

# ── FACEBOOK ──────────────────────────────────────────────
def post_facebook():
    if not FB_TOKEN or not FB_PAGE_ID:
        print("⚠️ Facebook: No credentials")
        return False
    try:
        data = {"message": MESSAGE, "access_token": FB_TOKEN}
        if IMAGE_URL:
            # Post with image
            r = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos",
                data={"url": IMAGE_URL, "caption": MESSAGE, "access_token": FB_TOKEN},
                timeout=30
            )
        else:
            r = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
                data=data, timeout=30
            )
        if r.status_code == 200 and "id" in r.json():
            print(f"✅ Facebook: Posted! ID: {r.json()['id']}")
            return True
        print(f"❌ Facebook: {r.status_code} {r.text[:100]}")
        return False
    except Exception as e:
        print(f"❌ Facebook error: {e}")
        return False

# ── INSTAGRAM ─────────────────────────────────────────────
def post_instagram():
    if not FB_TOKEN or not IG_USER_ID:
        print("⚠️ Instagram: No credentials")
        return False
    if not IMAGE_URL:
        print("⚠️ Instagram: Skipped (no image URL - Instagram requires image)")
        return False
    try:
        # Create container
        r1 = requests.post(
            f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media",
            data={"image_url": IMAGE_URL, "caption": MESSAGE, "access_token": FB_TOKEN},
            timeout=30
        )
        if r1.status_code != 200:
            print(f"❌ Instagram container: {r1.status_code} {r1.text[:100]}")
            return False
        container_id = r1.json().get("id")
        time.sleep(3)
        # Publish
        r2 = requests.post(
            f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
            data={"creation_id": container_id, "access_token": FB_TOKEN},
            timeout=30
        )
        if r2.status_code == 200:
            print(f"✅ Instagram: Posted! ID: {r2.json().get('id')}")
            return True
        print(f"❌ Instagram publish: {r2.status_code} {r2.text[:100]}")
        return False
    except Exception as e:
        print(f"❌ Instagram error: {e}")
        return False

# ── TELEGRAM ──────────────────────────────────────────────
def post_telegram():
    if not TG_BOT_TOKEN or not TG_CHANNEL_ID:
        print("⚠️ Telegram: No credentials")
        return False
    try:
        if IMAGE_URL:
            r = requests.post(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto",
                data={"chat_id": TG_CHANNEL_ID, "photo": IMAGE_URL, "caption": MESSAGE},
                timeout=30
            )
        else:
            r = requests.post(
                f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
                data={"chat_id": TG_CHANNEL_ID, "text": MESSAGE, "parse_mode": "HTML"},
                timeout=30
            )
        if r.status_code == 200:
            print(f"✅ Telegram: Posted!")
            return True
        print(f"❌ Telegram: {r.status_code} {r.text[:100]}")
        return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

# ── PINTEREST ─────────────────────────────────────────────
def post_pinterest():
    if not PIN_TOKEN or not PIN_BOARD_ID:
        print("⚠️ Pinterest: No credentials")
        return False
    if not IMAGE_URL:
        print("⚠️ Pinterest: Skipped (no image URL)")
        return False
    try:
        r = requests.post(
            "https://api.pinterest.com/v5/pins",
            headers={"Authorization": f"Bearer {PIN_TOKEN}", "Content-Type": "application/json"},
            json={
                "board_id": PIN_BOARD_ID,
                "title": MESSAGE[:100],
                "description": MESSAGE,
                "media_source": {"source_type": "image_url", "url": IMAGE_URL},
                "link": "https://investleey.com"
            },
            timeout=30
        )
        if r.status_code in [200, 201]:
            print(f"✅ Pinterest: Posted!")
            return True
        print(f"❌ Pinterest: {r.status_code} {r.text[:100]}")
        return False
    except Exception as e:
        print(f"❌ Pinterest error: {e}")
        return False

# ── TWITTER/X ─────────────────────────────────────────────
def post_twitter():
    if not TW_API_KEY or not TW_ACCESS_TOKEN:
        print("⚠️ Twitter: No credentials")
        return False
    try:
        from requests_oauthlib import OAuth1
        auth = OAuth1(TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)
        # Truncate to 280 chars
        tweet = MESSAGE[:277] + "..." if len(MESSAGE) > 280 else MESSAGE
        r = requests.post(
            "https://api.twitter.com/2/tweets",
            auth=auth,
            json={"text": tweet},
            timeout=30
        )
        if r.status_code in [200, 201]:
            print(f"✅ Twitter: Posted!")
            return True
        print(f"❌ Twitter: {r.status_code} {r.text[:100]}")
        return False
    except Exception as e:
        print(f"❌ Twitter error: {e}")
        return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    print(f"\n📢 Posting to: {PLATFORMS}")
    print(f"📝 Message: {MESSAGE[:100]}...")
    print(f"🖼️  Image: {IMAGE_URL or 'None'}\n")

    post_fb  = PLATFORMS in ["all", "facebook_instagram_only", "facebook_only"]
    post_ig  = PLATFORMS in ["all", "facebook_instagram_only", "instagram_only"]
    post_tg  = PLATFORMS in ["all", "telegram_only"]
    post_pin = False  # Pinterest pending Standard access approval
    post_tw  = PLATFORMS in ["all"]

    if post_fb:  results.append(("Facebook",  post_facebook()))
    if post_ig:  results.append(("Instagram", post_instagram()))
    if post_tg:  results.append(("Telegram",  post_telegram()))
    if post_pin: results.append(("Pinterest", post_pinterest()))
    if post_tw:  results.append(("Twitter",   post_twitter()))

    print("\n── RESULTS ──────────────────")
    for platform, success in results:
        print(f"  {'✅' if success else '❌'} {platform}")

    success_count = sum(1 for _, s in results if s)
    print(f"\n✅ Posted to {success_count}/{len(results)} platforms!")

if __name__ == "__main__":
    if not MESSAGE:
        print("❌ No message provided!")
        exit(1)
    main()
