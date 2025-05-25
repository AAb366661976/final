from flask import Flask, request, abort, jsonify
from bs4 import BeautifulSoup
import requests, time, os
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

@app.route("/callback", methods=["POST"])
def line_webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    query = event.message.text.strip()
    region, *keywords = query.split(" ", 1)
    keyword = keywords[0] if keywords else ""
    results = crawl(region, keyword)
    reply = "\n\n".join(results[:5]) if results else "找不到活動。"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/dialogflow_webhook", methods=["POST"])
def dialogflow_webhook():
    req = request.get_json()
    params = req.get("queryResult", {}).get("parameters", {})
    region = params.get("geo-city", "台北")
    keyword = params.get("any", "")
    results = crawl(region, keyword)
    reply = "\n\n".join(results[:5]) if results else "找不到活動。"
    return jsonify({"fulfillmentText": reply})

def crawl(region, keyword):
    url = "https://www.taiwan.net.tw/m1.aspx?sNo=0001016"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    results = []
    for item in soup.select(".themeList .themeListItem")[:10]:
        try:
            title = item.select_one(".themeTitle").text.strip()
            if keyword.lower() not in title.lower():
                continue
            act_region = item.select_one(".themeCity").text.strip()
            if region not in act_region:
                continue
            date = item.select_one(".themeTime").text.strip()
            link = item.select_one("a")["href"]
            results.append(f"[觀光局] {title}\n📅 {date}\n📍 {act_region}\n🔗 https://www.taiwan.net.tw{link}")
        except:
            continue
    return results

def handler(request, response):  # Vercel 入口
    return app(request, response)
