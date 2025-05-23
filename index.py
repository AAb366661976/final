from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from bs4 import BeautifulSoup
import requests, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# === LINE Bot 設定 ===
LINE_CHANNEL_ACCESS_TOKEN = "你的 Access Token"
LINE_CHANNEL_SECRET = "你的 Channel Secret"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# === LINE Webhook 路由 ===
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# === 主處理訊息 ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    query = event.message.text.strip()
    region, *keywords = query.split(" ", 1)
    keyword = keywords[0] if keywords else ""

    accupass = crawl_accupass(region, keyword)
    tourism = crawl_tourism(region, keyword)
    results = accupass + tourism

    if not results:
        reply = "找不到符合的活動。"
    else:
        reply = "\n\n".join(results[:5])

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# === Accupass 爬蟲 ===
def crawl_accupass(region, keyword):
    options = Options()
    options.add_argument("--headless")
    browser = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    url = f"https://www.accupass.com/search/r/{region}"
    browser.get(url)
    time.sleep(3)
    soup = BeautifulSoup(browser.page_source, "html.parser")
    browser.quit()

    results = []
    for card in soup.select(".event-card")[:10]:
        try:
            title = card.select_one(".event-title").text.strip()
            if keyword.lower() not in title.lower():
                continue
            date = card.select_one(".event-date").text.strip()
            location = card.select_one(".event-location").text.strip()
            link = card.select_one("a")["href"]
            results.append(f"[Accupass] {title}\n📅 {date}\n📍 {location}\n🔗 https://www.accupass.com{link}")
        except:
            continue
    return results

# === 台灣觀光局活動爬蟲 ===
def crawl_tourism(region, keyword):
    url = "https://www.taiwan.net.tw/m1.aspx?sNo=0001016"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    results = []
    items = soup.select(".themeList .themeListItem")[:10]
    for item in items:
        try:
            title = item.select_one(".themeTitle").text.strip()
            if keyword.lower() not in title.lower():
                continue
            act_region = item.select_one(".themeCity").text.strip()
            if region not in act_region:
                continue
            date = item.select_one(".themeTime").text.strip()
            link = item.select_one("a")["href"]
            results.append(f"[觀光局] {title}\n📅 {date}\n📍 {act_region}\n🔗 https://www.taiwan.net.tw/{link}")
        except:
            continue
    return results

# === 啟動伺服器 ===
if __name__ == "__main__":
    app.run(port=5000)
