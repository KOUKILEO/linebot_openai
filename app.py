from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler1 = WebhookHandler(os.getenv("CHANNEL_SECRET"))

message_counter = 0

BOT_PERSONALITY = """
你是一個活潑、親切、會用繁體中文回答的 LINE Bot 助手。
請簡潔回答，適度幽默。
如果是技術問題，請一步一步說明。
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

        ret = response.output_text.strip()
        ret += f"\n\n【OpenAI累計收到訊息數：{message_counter}】"

    except Exception as e:
        ret = f"發生錯誤：{str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=ret)
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
