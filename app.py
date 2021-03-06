import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from fsm import TocMachine
from utils import send_text_message, send_image_message

load_dotenv()


machine = TocMachine(
    states=["user", "start", "military", "female", "male", "tall",
            "tall_ex", "Military_service", "Alternative", "Exemption", "remind", "cheerup"],
    transitions=[
        {
            "trigger": "advance",
            "source": "user",
            "dest": "start",
            "conditions": "is_going_to_start",
        },
        {
            "trigger": "advance",
            "source": "start",
            "dest": "military",
            "conditions": "is_going_to_military",
        },
        {
            "trigger": "advance",
            "source": "military",
            "dest": "female",
            "conditions": "is_going_to_female",
        },
        {
            "trigger": "advance",
            "source": "military",
            "dest": "male",
            "conditions": "is_going_to_male",
        },
        {
            "trigger": "advance",
            "source": "male",
            "dest": "tall",
            "conditions": "is_going_to_tall",
        },
        {
            "trigger": "advance",
            "source": "male",
            "dest": "tall_ex",
            "conditions": "is_going_to_tall_ex",
        },
        {
            "trigger": "advance",
            "source": "tall",
            "dest": "Military_service",
            "conditions": "is_going_to_Military_service",
        },
        {
            "trigger": "advance",
            "source": "tall",
            "dest": "Alternative",
            "conditions": "is_going_to_Alternative",
        },
        {
            "trigger": "advance",
            "source": "tall",
            "dest": "Exemption",
            "conditions": "is_going_to_Exemption",
        },
        {
            "trigger": "advance",
            "source": "start",
            "dest": "remind",
            "conditions": "is_going_to_remind",
        },
        {
            "trigger": "advance",
            "source": "start",
            "dest": "cheerup",
            "conditions": "is_going_to_cheerup",
        },
        {
            "trigger": "go_back",
            "source": ["female", "tall_ex", "Military_service", "Alternative", "Exemption", "remind", "cheerup"],
            "dest": "user"
        },
    ],
    initial="user",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        response = machine.advance(event)
        if response == False:
            send_text_message(event.reply_token,
                              "Invalid input! please try again")

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        if not isinstance(event.message.text, str):
            continue
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        response = machine.advance(event)
        if response == False:
            send_text_message(event.reply_token, "Not Entering any State")

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    #machine.get_graph().draw("fsm.png", prog="dot", format="png")
    #machine.get_graph().draw("img/show-fsm.png", prog="dot", format="png")
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
