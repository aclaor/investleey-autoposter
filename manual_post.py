"""
Manual Multi-Platform Poster
Triggered manually from GitHub Actions with custom message + image
Posts to: Facebook, Instagram, Telegram (Crypto+Stocks), Twitter/X, LinkedIn, Discord
"""
import os, requests, time, base64, io

def resize_for_instagram(image_url, imgbb_key):
    """Download image, resize to 1080x1080 square, re-upload to imgbb"""
    try:
        from PIL import Image
        # Download image
        r = requests.get(image_url, timeout=30)
        img = Image.open(io.BytesIO(r.content)).convert('RGB')
        # Crop to square (center crop)
        w, h = img.size
        size = min(w, h)
        left = (w - size) // 2
        top  = (h - size) // 2
        img = img.crop((left, top, left+size, top+size))
        img = img.resize((1080, 1080), Image.LANCZOS)
        # Save to bytes
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=95)
        buf.seek(0)
        # Re-upload to imgbb
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        r2 = requests.post('https://api.imgbb.com/1/upload',
            data={'key': imgbb_key, 'image': b64}, timeout=30)
        if r2.status_code == 200:
            url = r2.json()['data']['url']
            print(f"✅ Image resized to 1080x1080 and re-uploaded: {url}")
            return url
    except Exception as e:
        print(f"⚠️ Resize failed: {e} — using original")
    return image_url

MESSAGE   = os.environ.get("MESSAGE", "")
IMAGE_URL = os.environ.get("IMAGE_URL", "").strip()
PLATFORMS = os.environ.get("PLATFORMS", "all")

# Facebook & Instagram
FB_TOKEN        = os.environ.get("FB_PAGE_ACCESS_TOKEN", "")
IG_USER_ID      = os.environ.get("IG_USER_ID", "")
IMGBB_KEY       = os.environ.get("IMGBB_API_KEY", "")
FB_PAGE_ID      = "103114287835428"  # Caishenshop

# Telegram
TG_BOT_CRYPTO   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAN_CRYPTO  = os.environ.get("TELEGRAM_CHANNEL_ID", "")
TG_BOT_STOCKS   = os.environ.get("TELEGRAM_BOT_TOKEN_STOCKS", "")
TG_CHAN_STOCKS  = os.environ.get("TELEGRAM_STOCK_CHANNEL", "")

# Twitter/X
TW_API_KEY      = os.environ.get("TWITTER_API_KEY", "")
TW_API_SECRET   = os.environ.get("TWITTER_API_SECRET", "")
TW_ACCESS_TOKEN = os.environ.get("TWITTER_ACCESS_TOKEN", "")
TW_ACCESS_SECRET= os.environ.get("TWITTER_ACCESS_SECRET", "")

# LinkedIn
LI_TOKEN_CRYPTO = os.environ.get("LI_ACCESS_TOKEN_CRYPTO", "")
LI_TOKEN_STOCKS = os.environ.get("LI_ACCESS_TOKEN_STOCKS", "")
LI_ORG_CRYPTO   = os.environ.get("LI_ORG_ID_CRYPTO", "")
LI_ORG_STOCKS   = os.environ.get("LI_ORG_ID_STOCKS", "")

# Discord
DC_BOT_TOKEN    = os.environ.get("DISCORD_BOT_TOKEN", "")
DC_CRYPTO_CHAN  = os.environ.get("DISCORD_CRYPTO_CHANNEL", "")
DC_STOCK_CHAN   = os.environ.get("DISCORD_STOCK_CHANNEL", "")

results = []

# ── FACEBOOK ──────────────────────────────────────────────
def post_facebook():
    if not FB_TOKEN:
        print("⚠️ Facebook: No token"); return False
    try:
        if IMAGE_URL:
            r = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/photos",
                data={"url": IMAGE_URL, "caption": MESSAGE, "access_token": FB_TOKEN},
                timeout=30
            )
        else:
            r = requests.post(
                f"https://graph.facebook.com/v21.0/{FB_PAGE_ID}/feed",
                data={"message": MESSAGE, "access_token": FB_TOKEN},
                timeout=30
            )
        d = r.json()
        if "id" in d:
            print(f"✅ Facebook: Posted! ID: {d['id']}"); return True
        print(f"❌ Facebook: {d.get('error',{}).get('message','unknown')}"); return False
    except Exception as e:
        print(f"❌ Facebook error: {e}"); return False

# ── INSTAGRAM ─────────────────────────────────────────────
def post_instagram():
    if not FB_TOKEN or not IG_USER_ID:
        print("⚠️ Instagram: No credentials"); return False
    if not IMAGE_URL:
        print("⚠️ Instagram: Skipped (no image - required)"); return False
    try:
        ig_image = resize_for_instagram(IMAGE_URL, IMGBB_KEY) if IMGBB_KEY else IMAGE_URL
        r1 = requests.post(
            f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media",
            data={"image_url": ig_image, "caption": MESSAGE, "access_token": FB_TOKEN},
            timeout=30
        )
        if r1.status_code != 200:
            print(f"❌ Instagram container: {r1.text[:100]}"); return False
        container_id = r1.json().get("id")
        time.sleep(3)
        r2 = requests.post(
            f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media_publish",
            data={"creation_id": container_id, "access_token": FB_TOKEN},
            timeout=30
        )
        if r2.status_code == 200:
            print(f"✅ Instagram: Posted! ID: {r2.json().get('id')}"); return True
        print(f"❌ Instagram: {r2.text[:100]}"); return False
    except Exception as e:
        print(f"❌ Instagram error: {e}"); return False

def post_telegram(bot_token, channel_id, name):
    if not bot_token or not channel_id:
        print(f"⚠️ Telegram {name}: No credentials"); return False
    try:
        if IMAGE_URL:
            r = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendPhoto",
                data={"chat_id": channel_id, "photo": IMAGE_URL, "caption": MESSAGE},
                timeout=30
            )
        else:
            r = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={"chat_id": channel_id, "text": MESSAGE},
                timeout=30
            )
        if r.status_code == 200:
            print(f"✅ Telegram {name}: Posted!"); return True
        print(f"❌ Telegram {name}: {r.text[:100]}"); return False
    except Exception as e:
        print(f"❌ Telegram {name} error: {e}"); return False

# ── TWITTER/X ─────────────────────────────────────────────
def post_twitter():
    if not TW_API_KEY or not TW_ACCESS_TOKEN:
        print("⚠️ Twitter: No credentials"); return False
    try:
        from requests_oauthlib import OAuth1
        auth = OAuth1(TW_API_KEY, TW_API_SECRET, TW_ACCESS_TOKEN, TW_ACCESS_SECRET)
        tweet = MESSAGE[:277] + "..." if len(MESSAGE) > 280 else MESSAGE
        r = requests.post(
            "https://api.twitter.com/2/tweets",
            auth=auth, json={"text": tweet}, timeout=30
        )
        if r.status_code in [200, 201]:
            print(f"✅ Twitter: Posted!"); return True
        print(f"❌ Twitter: {r.status_code} {r.text[:100]}"); return False
    except Exception as e:
        print(f"❌ Twitter error: {e}"); return False

# ── LINKEDIN ──────────────────────────────────────────────
def post_linkedin(token, org_id, name):
    if not token or not org_id:
        print(f"⚠️ LinkedIn {name}: No credentials"); return False
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        # Handle both raw ID and full URN
        author_urn = org_id if org_id.startswith("urn:") else f"urn:li:organization:{org_id}"
        body = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": MESSAGE},
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        r = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers, json=body, timeout=30
        )
        if r.status_code in [200, 201]:
            print(f"✅ LinkedIn {name}: Posted!"); return True
        print(f"❌ LinkedIn {name}: {r.status_code} {r.text[:100]}"); return False
    except Exception as e:
        print(f"❌ LinkedIn {name} error: {e}"); return False

# ── DISCORD ───────────────────────────────────────────────
def post_discord(channel_id, name):
    if not DC_BOT_TOKEN or not channel_id:
        print(f"⚠️ Discord {name}: No credentials"); return False
    try:
        headers = {"Authorization": f"Bot {DC_BOT_TOKEN}", "Content-Type": "application/json"}
        data = {"content": MESSAGE}
        if IMAGE_URL:
            data["embeds"] = [{"image": {"url": IMAGE_URL}, "description": MESSAGE}]
            data["content"] = ""
        r = requests.post(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            headers=headers, json=data, timeout=30
        )
        if r.status_code in [200, 201]:
            print(f"✅ Discord {name}: Posted!"); return True
        print(f"❌ Discord {name}: {r.status_code} {r.text[:100]}"); return False
    except Exception as e:
        print(f"❌ Discord {name} error: {e}"); return False

# ── MAIN ──────────────────────────────────────────────────
def main():
    print(f"\n📢 Posting to: {PLATFORMS}")
    print(f"📝 Message: {MESSAGE[:100]}...")
    print(f"🖼️  Image: {IMAGE_URL or 'None'}\n")

    post_fb  = PLATFORMS in ["all", "facebook_instagram_only", "facebook_only"]
    post_ig  = PLATFORMS in ["all", "facebook_instagram_only", "instagram_only"]
    post_tg  = PLATFORMS in ["all", "telegram_only"]
    post_tw  = PLATFORMS in ["all", "twitter_only"]
    post_li  = PLATFORMS in ["all", "linkedin_only"]
    post_dc  = PLATFORMS in ["all", "discord_only"]

    if post_fb:
        results.append(("Facebook", post_facebook()))
    if post_ig:
        results.append(("Instagram", post_instagram()))
    if post_tg:
        results.append(("Telegram Crypto", post_telegram(TG_BOT_CRYPTO, TG_CHAN_CRYPTO, "Crypto")))
        results.append(("Telegram Stocks", post_telegram(TG_BOT_STOCKS, TG_CHAN_STOCKS, "Stocks")))
    # Twitter/X disabled - requires $100/mo Basic API plan
    # if post_tw:
    #     results.append(("Twitter/X", post_twitter()))
    if post_li:
        results.append(("LinkedIn Crypto", post_linkedin(LI_TOKEN_CRYPTO, LI_ORG_CRYPTO, "Crypto")))
        results.append(("LinkedIn Stocks", post_linkedin(LI_TOKEN_STOCKS, LI_ORG_STOCKS, "Stocks")))
    if post_dc:
        results.append(("Discord Crypto", post_discord(DC_CRYPTO_CHAN, "Crypto")))
        results.append(("Discord Stocks", post_discord(DC_STOCK_CHAN, "Stocks")))

    print("\n── RESULTS ──────────────────")
    for platform, success in results:
        print(f"  {'✅' if success else '❌'} {platform}")

    success_count = sum(1 for _, s in results if s)
    print(f"\n🎉 Posted to {success_count}/{len(results)} platforms!")

if __name__ == "__main__":
    if not MESSAGE:
        print("❌ No message provided!")
        exit(1)
    main()
