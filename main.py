from twilio.rest import Client
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import schedule
import time
import asyncio

account_sid = 'ACd82bc829c02333b6c5c9dac3eab546f1'
auth_token = '287440909711bad55b8e727c852336d0'
client = Client(account_sid, auth_token)

app = Flask(__name__)

server_number = 'whatsapp:+14155238886'
client_number = 'whatsapp:+33647528686'
emergency_number = 'whatsapp:+33636363636'

last_message_time = 0
alert_mode = False
last_alert_time = 0
reminder_count = 0


def send_daily_message_10h():
    global last_message_time
    client.messages.create(
        from_=server_number,
        body='Hey! This is your first daily message, please answer if you are fine! :)',
        to=client_number
    )

    last_message_time = time.time()


def send_daily_message_21h():
    global last_message_time
    client.messages.create(
        from_=server_number,
        body='Hey! This is your second daily message, please answer if you are fine! :)',
        to=client_number
    )

    last_message_time = time.time()


def send_reminder():
    global reminder_count
    reminder_count += 1
    client.messages.create(
        from_=server_number,
        body=f"Reminder {reminder_count}: Please respond to the verification message.",
        to=client_number
    )
    if reminder_count >= 4:
        send_alert_message()


async def check_for_response():
    global alert_mode
    global last_alert_time
    while alert_mode:
        # Attendre pendant 15 minutes avant d'envoyer un rappel
        await asyncio.sleep(900)
        send_reminder()
        current_time = time.time()
        if current_time - last_alert_time >= 3600:
            # Si une heure s'est écoulée depuis l'alerte, déclencher l'alerte d'urgence
            send_alert_message()
            alert_mode = False
            break


def send_alert_message():
    client.messages.create(
        from_=server_number,
        body='No response received from VAL. URGENT SYSTEM LAUNCHING',
        to=emergency_number
    )
    client.messages.create(
        from_=server_number,
        body='Alert sent to emergency contacts',
        to=client_number
    )


@app.route("/sms", methods=['POST'])
def sms_reply():
    global last_message_time
    global alert_mode
    global last_alert_time
    global reminder_count

    message_body = request.values.get('Body', '').strip().lower()
    current_time = time.time()

    if current_time - last_message_time <= 3600:
        if time.localtime().tm_hour == 11:
            response_message = 'Thank you for your response! Have a great day! :D'
        else:
            response_message = 'Thank you for your response! Have a wonderful night! ;)'

        client.messages.create(
            from_=server_number,
            body=response_message,
            to=client_number
        )
        reminder_count = 0
    else:
        if alert_mode:
            alert_mode = False
            client.messages.create(
                from_=server_number,
                body='Alert status is reset. Everything is back to normal.',
                to=emergency_number
            )
            client.messages.create(
                from_=server_number,
                body='Alert status is reset. Everything is back to normal.',
                to=client_number
            )
        else:
            if time.localtime().tm_hour != 11 or time.localtime().tm_hour != 21:
                send_alert_message()
                alert_mode = True
                last_alert_time = current_time
            else:
                print(f"Message received at unexpected time: {message_time} hours")

    return ''


if __name__ == "__main__":
    schedule.every().day.at("10:00").do(send_daily_message_10h)
    schedule.every().day.at("21:00").do(send_daily_message_21h)

    while True:
        schedule.run_pending()
        time.sleep(1)

        #asyncio.create_task(check_for_response())
