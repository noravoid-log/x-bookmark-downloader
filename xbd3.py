#!/usr/bin/env python3
import os, sys, json, time, urllib.request, urllib.parse, traceback
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION — edit these before running
# ─────────────────────────────────────────────

# Where downloaded images will be saved
OUTPUT_BASE = r'C:\Users\YourName\Pictures\X Bookmarks'

# Your bookmark folders: 'Display Name': 'folder_id'
# See README for how to find your folder IDs
FOLDERS = {
    'Folder Name One': 'YOUR_FOLDER_ID_HERE',
    'Folder Name Two': 'YOUR_FOLDER_ID_HERE',
}

# ─────────────────────────────────────────────
# DO NOT EDIT BELOW THIS LINE
# ─────────────────────────────────────────────

CREDS_FILE   = os.path.join(OUTPUT_BASE, '_creds.json')
LOG_FILE     = os.path.join(OUTPUT_BASE, '_download_log.json')
ACTIVITY_LOG = os.path.join(OUTPUT_BASE, '_download_activity.log')
BEARER = 'AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
GQL_ID = 'bVS9KtDz8mnOp7SKpHhR0w'

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    try:
        with open(ACTIVITY_LOG, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass

def load_creds():
    if not os.path.exists(CREDS_FILE):
        log(f'ERROR: No credentials file found at {CREDS_FILE}')
        log('Run save_creds.py first to set up your X credentials.')
        sys.exit(1)
    with open(CREDS_FILE, encoding='utf-8') as f:
        return json.load(f)

GQL_FEATURES = {'rweb_video_screen_enabled':False,'rweb_cashtags_enabled':True,'profile_label_improvements_pcf_label_in_post_enabled':True,'responsive_web_graphql_timeline_navigation_enabled':True,'responsive_web_graphql_skip_user_profile_image_extensions_enabled':False,'longform_notetweets_consumption_enabled':True,'responsive_web_twitter_article_tweet_consumption_enabled':True,'longform_notetweets_inline_media_enabled':False,'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled':True,'longform_notetweets_rich_text_read_enabled':True,'freedom_of_speech_not_reach_fetch_enabled':True,'standardized_nudges_misinfo':True,'articles_preview_enabled':True}

def _api_headers(ct0, auth_token):
    return {
        'Authorization':         f'Bearer {BEARER}',
        'x-csrf-token':          ct0,
        'x-twitter-auth-type':   'OAuth2Session',
        'x-twitter-active-user': 'yes',
        'Cookie':                f'auth_token={auth_token}; ct0={ct0}',
        'User-Agent':            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    }

def get_folder_media(folder_id, ct0, auth_token):
    headers = _api_headers(ct0, auth_token)
    fq = urllib.parse.quote(json.dumps(GQL_FEATURES))
    all_media = []; cursor = None; page = 0
    while True:
        page += 1
        v = {'bookmark_collection_id': folder_id, 'count': 100, 'includePromotedContent': False}
        if cursor: v['cursor'] = cursor
        url = f'https://x.com/i/api/graphql/{GQL_ID}/BookmarkFolderTimeline?variables={urllib.parse.quote(json.dumps(v))}&features={fq}'
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                data = json.loads(r.read())
        except urllib.error.HTTPError as e:
            log(f'  HTTP {e.code}: request failed')
            if e.code == 401:
                log('  Auth failed - your credentials may have expired. Re-run save_creds.py.')
            break
        except Exception as e:
            log(f'  API error: {e}'); break
        instructions = data.get('data',{}).get('bookmark_collection_timeline',{}).get('timeline',{}).get('instructions',[])
        entries = []; next_cursor = None
        for inst in instructions:
            if 'entries' in inst: entries = inst['entries']
        new_count = 0
        for entry in entries:
            c = entry.get('content', {}); et = c.get('entryType', '')
            if et == 'TimelineTimelineItem':
                tr = c.get('itemContent',{}).get('tweet_results',{}).get('result',{})
                leg = tr.get('legacy', {})
                for m in (leg.get('extended_entities',{}).get('media',[]) or leg.get('entities',{}).get('media',[])):
                    if m.get('type') == 'photo' and m.get('id_str') and m.get('media_url_https'):
                        all_media.append({'id': m['id_str'], 'url': m['media_url_https'].split('?')[0], 'tweet_id': tr.get('rest_id','')})
                        new_count += 1
            elif et == 'TimelineTimelineCursor' and c.get('cursorType') == 'Bottom':
                next_cursor = c.get('value')
        log(f'  Page {page}: {new_count} images (more: {"yes" if next_cursor else "no"})')
        if not next_cursor or len(entries) <= 2: break
        cursor = next_cursor; time.sleep(1.5)
    return all_media

def load_log():
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, encoding='utf-8') as f: return json.load(f)
        except: pass
    return {}

def save_log(d):
    with open(LOG_FILE, 'w', encoding='utf-8') as f: json.dump(d, f)

def download_folder(folder_name, items, log_data):
    out_dir = os.path.join(OUTPUT_BASE, folder_name)
    os.makedirs(out_dir, exist_ok=True)
    seen = set(log_data.get(folder_name, []))
    hdrs = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
    dl = sk = fa = 0
    for item in items:
        mid = item['id']
        if mid in seen: sk += 1; continue
        try:
            with urllib.request.urlopen(urllib.request.Request(item['url']+'?format=jpg&name=large', headers=hdrs), timeout=20) as r:
                img = r.read()
            with open(os.path.join(out_dir, f'{mid}.jpg'), 'wb') as f: f.write(img)
            seen.add(mid); dl += 1
        except Exception as e:
            log(f'    FAILED {mid}: {e}'); fa += 1
        time.sleep(0.3)
    log_data[folder_name] = list(seen)
    return dl, sk, fa

def main():
    log('='*50); log('X Bookmark Downloader'); log('='*50)
    if not os.path.exists(OUTPUT_BASE):
        log(f'ERROR: Output folder not found: {OUTPUT_BASE}')
        log('Check that OUTPUT_BASE in xbd3.py points to a valid folder and try again.')
        sys.exit(1)
    creds = load_creds()
    auth_token = creds.get('auth_token'); ct0 = creds.get('ct0')
    if not auth_token or not ct0:
        log('ERROR: _creds.json is missing auth_token or ct0. Re-run save_creds.py.'); sys.exit(1)
    log(f'Credentials loaded OK')
    dl_log = load_log()
    for folder_name, folder_id in FOLDERS.items():
        log(f'--- {folder_name} ---')
        try:
            items = get_folder_media(folder_id, ct0, auth_token)
            log(f'Total media in folder: {len(items)}')
            dl, sk, fa = download_folder(folder_name, items, dl_log)
            log(f'New: {dl}  |  Skipped: {sk}  |  Failed: {fa}')
            save_log(dl_log)
        except Exception as e:
            log(f'ERROR: {e}'); log(traceback.format_exc())
    log('All done.\n')

if __name__ == '__main__':
    main()
