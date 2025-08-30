import os, json, urllib.request

def notify_slack(text: str):
    webhook = os.getenv("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        return
    data = {"text": text}
    req = urllib.request.Request(webhook, data=json.dumps(data).encode("utf-8"), headers={"Content-Type":"application/json"})
    try:
        urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        pass
