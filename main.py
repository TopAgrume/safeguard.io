from twilio.rest import Client

account_sid = 'ACd82bc829c02333b6c5c9dac3eab546f1'
auth_token = '287440909711bad55b8e727c852336d0'
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  media_url=['https://demo.twilio.com/owl.png'],
  body='test',
  to='whatsapp:+33647528686'
)

print(message.sid)

from flask import Flask
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    """Respond to incoming calls with a simple text message."""
    # Start our TwiML response
    resp = MessagingResponse()

    # Add a message
    resp.message("The Robots are coming! Head for the hills!")

    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)