from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# 動畫爬蟲函式
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

# 接收 Dialogflow 的 webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json()
    intent_name = req["queryResult"]["intent"]["displayName"]

    if intent_name == "查詢最新動畫":
        reply_text = get_latest_anime()
    else:
        reply_text = "這個意圖還沒設定喔！"

    return jsonify({"fulfillmentText": reply_text})

if __name__ == "__main__":
    app.run(port=5000)
