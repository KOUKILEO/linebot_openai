from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import os

app = Flask(__name__)

# 建立 OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LINE Bot
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler1 = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# 計數器：紀錄使用者總共傳了幾則訊息進來
message_counter = 0

# 設定 ChatGPT 個性
BOT_PERSONALITY = """
你是一個活潑、親切、會用繁體中文回答的 LINE Bot 助手。
你的特色：
1. 回答簡潔清楚
2. 適度幽默，但不要太浮誇
3. 看到使用者心情不好時，會稍微鼓勵
4. 如果是技術問題，會一步一步說明
"""

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler1.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler1.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global message_counter
    message_counter += 1

    user_text = event.message.text

    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=[
                {"role": "system", "content": BOT_PERSONALITY},
                {"role": "user", "content": user_text}
            ]
        )

        # 取出模型文字輸出
        ret = response.output_text.strip()

        # 把 counter 一起回傳
        ret = f"{ret}\n\n【OpenAI 累計收到訊息數：{message_counter}】"

    except Exception as e:
        ret = f"發生錯誤！\n{str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ret)
    )

if __name__ == "__main__":
    app.run()
