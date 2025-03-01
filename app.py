import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()
twilio_account_sid = 'AC224ed1fdd954915e8ceb92fd6af24ef8'
twilio_api_key_sid = 'SK837567be456422a5afff843881d420ca'
twilio_api_key_secret = 'ndOFOCjaRP7W3pstvKtn4XQjP2PFLvuF'
twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret, twilio_account_sid)


app = Flask(__name__)


def get_chatroom(name):
    name = 'big'
    for conversation in twilio_client.conversations.conversations.stream():
        if conversation.friendly_name == name:
            return conversation

    # a conversation with the given name does not exist ==> create a new one
    return twilio_client.conversations.conversations.create(
        friendly_name=name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.get_json(force=True).get('username')
    if not username:
        abort(401)

    conversation = get_chatroom('My Room')
    try:
        conversation.participants.create(identity=username)
    except TwilioRestException as exc:
        # do not error if the user is already in the conversation
        if exc.status != 409:
            raise

    token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                        twilio_api_key_secret, identity=username)
    token.add_grant(VideoGrant(room='My Room'))
    token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid)) 

    return {'token': token.to_jwt(),
         'conversation_sid': conversation.sid}




if __name__ == '__main__':
    app.run(host='0.0.0.0')
