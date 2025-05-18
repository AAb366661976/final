from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from bs4 import BeautifulSoup
import requests
import os

app = Flask(__name__)

# 請替換成你自己的 LINE Token & Secret
LINE_CHANNEL_ACCESS_TOKEN = "你的 Access Token"
LINE_CHANNEL_SECRET = "你的 Channel Secret"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 動畫爬蟲函數
def get_latest_anime():
    url = "https://ani.gamer.com.tw/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    anime_items = soup.select("ul.newanime-block li a")[:5]

    info = "🔥 本季熱門動畫：\n"
    for item in anime_items:
        title = item.get("title", "").strip()
        link = item.get("href", "").strip()
        if title:
            info += f"📌 {title}\n🔗 {link}\n\n"
    return info.strip()

# webhook 路由（LINE 會來這裡打）
@app.route("/line_webhook", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# 處理文字訊息事件
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()

    # 如果使用者問動畫，就回覆最新動畫
    if "動畫" in user_msg:
        reply = get_latest_anime()
    else:
        reply = f"你說的是：{user_msg}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()
