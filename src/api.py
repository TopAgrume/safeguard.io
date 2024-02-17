import time
import re
import random
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.ext import CallbackQueryHandler
from datetime import datetime, timedelta
from utils.env_pipeline import AccessEnv

from src.commands import start_command, info_command, bugreport_command, request_command, verify_condition
from src.commands import addcontact_command, showcontacts_command, delcontact_command, empty_command
from src.commands import addverif_command, showverifs_command, delverif_command, kill_user_data
from src.commands import skip_command, undoskip_command, fastcheck_command, help_command, undohelp_command

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()
P_HTML = telegram.constants.ParseMode.HTML
bot = Bot(TOKEN)


async def send_hope_message(update: Update):
    print('API:', 'Send Hope Message')
    message = '<b>Alert status is reset</b>. Everything is back to normal. ✅'
    await update.message.reply_text(text=message, parse_mode=P_HTML)


async def notif_user(update: Update, notif_details: list):
    user_id = update.message.from_user.id
    username = update.message.from_user.username

    for notif in notif_details:
        print("API:", f"Notif user from del/add {user_id=} to {notif['id']}")
        message = f"<b>Do you want to accept the pairing invitation from @{username}? 🤝</b>"

        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"+{str(user_id)}"),
                InlineKeyboardButton("No", callback_data=f"-{str(user_id)}"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await bot.send_message(chat_id=notif['id'], text=message, reply_markup=reply_markup, parse_mode=P_HTML)


async def extract_user_id_add(update: Update, content: str):
    error_contact, new_contacts = [], []
    user_id = update.message.from_user.id
    user_username = update.message.from_user.username

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'@(\w+)', line)

        if match_tag:
            new_contacts.append(match_tag.group(1))
        else:
            error_contact.append(line)

    # Send notif to the new users
    notification = AccessEnv.on_write_contacts(user_id, user_username, "add", new_contacts)
    await notif_user(update, notification)

    message = "Given contact(s) are now added to your account.\nThey received an association request.🎉\n"
    if len(error_contact) != 0:
        message += "\nFollowing contact(s) weren't added due to their unknown format:\n"
        for elt in error_contact:
            message += f"\n❌ {elt}"
    return await update.message.reply_text(message)


async def extract_user_id_del(update: Update, content: str):
    error_contact, del_contacts = [], []
    user_id = update.message.from_user.id
    user_username = update.message.from_user.username

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'@(\w+)', line)

        if match_tag:
            del_contacts.append(match_tag.group(1))
        else:
            error_contact.append(line)

    AccessEnv.on_write_contacts(user_id, user_username, "del", del_contacts)

    message = "Given contact(s) are now deleted from your account.🚮\n"
    if len(error_contact) != 0:
        message += "\nFollowing contact(s) weren't removed due to their unknown format:\n"
        for elt in error_contact:
            message += f"\n❌ {elt}"
    return await update.message.reply_text(message)


async def extract_verif_add(update: Update, content: str):
    error_contact, new_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]) *- *([\w ]+)', line)

        if match_tag:
            chosen_time, desc = f"{match_tag.group(1)}:{match_tag.group(2)}", match_tag.group(3)
            new_verif.append({"time": chosen_time, "desc": desc, "active": True})
        else:
            error_contact.append(line)

    not_valid = AccessEnv.on_write_verifications(user_id, "add", new_verif)

    message = "Given daily verification(s) are now added to your account. 📅🔐\n"
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't added due to their unknown format:\n"
        for elt in error_contact:
            message += f"\n❌ {elt}"
        message += "\n"
    if len(not_valid) != 0:
        message += ("\nFollowing verification(s) weren't added. Make sure to"
                    "space daily messages at least 20 minutes apart:\n")
        for elt in not_valid:
            message += f"\n❌ {elt}"
    return await update.message.reply_text(message)


async def extract_verif_del(update: Update, content: str):
    error_contact, del_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line)

        if match_tag:
            chosen_time = f"{match_tag.group(1)}:{match_tag.group(2)}"
            del_verif.append(chosen_time)
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "del", del_verif)

    message = "Given daily verification(s) are now deleted to your account.🚫📅\n"
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't removed due to their unknown format:\n"
        for elt in error_contact:
            message += f"\n❌ {elt}"
    return await update.message.reply_text(message)


async def extract_bugreport(update: Update, content: str):
    date = datetime.now().strftime("%d.%m.%Y_%Hh%M")
    filename = f"bug_reports/report_{date}_{random.randint(0, 999999)}"
    with open(filename, 'w') as file:
        file.write(content)
        file.close()
    message = "Thank you for the report!"
    return await update.message.reply_text(message)


async def skip_alarm(update: Update, content: str):
    error_contact, skip_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line)

        if match_tag:
            chosen_time = f"{match_tag.group(1)}:{match_tag.group(2)}"
            skip_verif.append(chosen_time)
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "skip", skip_verif)

    message = "Given daily verification(s) are now skipped for the next 24h.⏰✨\n"
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't skipped due to their unknown format:\n"
        for elt in error_contact:
            message += f"\n❌ {elt}"
    return await update.message.reply_text(message)


async def undoskip_alarm(update: Update, content: str):
    error_contact, skip_verif = [], []
    user_id = update.message.from_user.id

    # Use regular expression to extract the username from the tag
    for line in content.splitlines():
        match_tag = re.match(r'^(0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$', line)

        if match_tag:
            chosen_time = f"{match_tag.group(1)}:{match_tag.group(2)}"
            skip_verif.append(chosen_time)
        else:
            error_contact.append(line)

    AccessEnv.on_write_verifications(user_id, "undoskip", skip_verif)

    message = "Given daily verification(s) are now activated.🔐🔄\n"
    if len(error_contact) != 0:
        message += "\nFollowing verification(s) weren't activated due to their unknown format:\n"
        for elt in error_contact:
            message += f"\n❌ {elt}"
    return await update.message.reply_text(message)


async def extract_fastcheck(update: Update, content: str):
    user_id = update.message.from_user.id
    current_time = datetime.now()
    # Use regular expression to extract the username from the tag
    match_tag = re.match(r'(\d+) *mn', content)

    if not match_tag:
        return await update.message.reply_text(f"Unknown format: \"{content}\".")

    waiting_time = int(match_tag.group(1))
    if waiting_time > 20:
        return await update.message.reply_text("Invalid time, 20mn max")

    current_time += timedelta(minutes=waiting_time)
    time_to_display = current_time.strftime("%H:%M")

    new_alarm = {"time": time_to_display, "desc": "Auto fast check", "active": None}
    AccessEnv.on_write_verifications(user_id, "add", [new_alarm], True)

    message = f"Fast Check in {waiting_time}mn taken into account! ({time_to_display}) 🚀"
    return await update.message.reply_text(message)


async def default_case(update: Update, content: str):
    return await update.message.reply_text(f"Excuse me, I didn't quite understand your request. 🤔")


async def state_dispatcher(update: Update, state: str, message_body: str):
    switch_dict = {
        "addcontact": extract_user_id_add,
        "delcontact": extract_user_id_del,
        "addverif": extract_verif_add,
        "delverif": extract_verif_del,
        "bugreport": extract_bugreport,
        "skip": skip_alarm,
        "undoskip": undoskip_alarm,
        "fastcheck": extract_fastcheck,
    }

    selected_case = switch_dict.get(state, default_case)

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "")

    return await selected_case(update, message_body)


@verify_condition
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    message_body: str = update.message.text

    user_id = update.message.from_user.id
    response_message, alert_mode = AccessEnv.on_read(user_id)

    if response_message:
        # Already answered / Random call
        get_state = AccessEnv.on_read(user_id, "state")

        print('API:', f"Command call {get_state=}", f"Content: {message_body=}")
        return await state_dispatcher(update, get_state, message_body)

    if not alert_mode:
        print('API:', 'Response to contact and confirmation demand')
        greeting = "Have a great day 🌞!" if time.localtime().tm_hour < 16 else "Have a wonderful afternoon 🌅!"
        response = f"Thank you for your response! {greeting}"

        AccessEnv.on_write(user_id, "response_message", True)
        return await update.message.reply_text(response)

    print('API:', 'Response to unset the alert mode')
    AccessEnv.on_write(user_id, "alert_mode", False)
    AccessEnv.on_write(user_id, "response_message", True)
    await manual_undohelp(user_id, update.message.from_user.username)
    return await send_hope_message(update)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print('API ERROR:', f'Update {update} caused error {context}')


async def manual_help(user_id: int, username: str):
    message = (f"🚨<b>ALERT</b>🚨. @{username} has manually triggered the call for help."
               " <b>Please take this call seriously and ensure their well-being!</b>")

    for contact in AccessEnv.on_read(user_id, "contacts"):
        if not contact["pair"]:
            continue

        await bot.send_message(chat_id=contact["id"], text=message, parse_mode=P_HTML)


async def manual_undohelp(user_id: int, username: str):
    message = (f"⚠️<b>Alert disabled</b>⚠️. @{username} manually disabled the alert."
               " <b>Please confirm it was intentional or check if it was a simple mistake.</b>")

    for contact in AccessEnv.on_read(user_id, "contacts"):
        if not contact["pair"]:
            continue

        await bot.send_message(chat_id=contact["id"], text=message, parse_mode=P_HTML)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    # 'button' will be called for each button the user clicks
    await query.answer()

    if query.data is None or len(query.data) == 0:
        return await query.edit_message_text(text=f"Unknown: Query data empty ({query.data})")

    if query.data == "1":
        AccessEnv.on_write(user_id, "alert_mode", True)
        message = ("OK. Emergency contacts have received your request for help! 🆘\n"
                   "Type /undohelp to cancel the alert.")
        await manual_help(user_id, query.from_user.username)
        return await query.edit_message_text(text=message)
    if query.data == "2":
        message = "OK 😅. Glad to hear it was a mistake!"
        return await query.edit_message_text(text=message)

    if query.data == "3":
        AccessEnv.on_write(user_id, "alert_mode", False)
        message = "OK. Your emergency contacts have received information that the alert has been disabled. 📢"
        await manual_undohelp(user_id, query.from_user.username)
        return await query.edit_message_text(text=message)
    if query.data == "4":
        message = "OK. Operation canceled."
        return await query.edit_message_text(text=message)

    if query.data[0] == "-":
        contact_request = AccessEnv.on_read(user_id, "contact_request")
        del contact_request[query.data[1:]]
        AccessEnv.on_write(user_id, "contact_request", contact_request)
        message = "<b>OK. Association request declined. ❌</b>"
        return await query.edit_message_text(text=message, parse_mode=P_HTML)

    origin_id = int(query.data[1:])
    updated_pairing = []
    contacts_pairing = AccessEnv.on_read(origin_id, "contacts")

    for contact in contacts_pairing:
        if contact['id'] == user_id:
            contact['pair'] = True
        updated_pairing.append(contact)

    AccessEnv.on_write(origin_id, "contacts", updated_pairing)
    users_data = AccessEnv.on_get_user_id_usernames()

    contact_request = AccessEnv.on_read(user_id, "contact_request")
    del contact_request[query.data[1:]]
    AccessEnv.on_write(user_id, "contact_request", contact_request)

    print('API:', f"Response message to association with {origin_id}")
    message = (f"<b>@{query.from_user.username} has accepted your association "
               f"request and will be contacted in the event of an emergency. 🤝</b>")
    await bot.send_message(chat_id=origin_id, text=message, parse_mode=P_HTML)

    message = (f"<b>Successful association @{users_data[query.data[1:]]} 🎉. "
               f"You will now be informed if this person no longer gives any news.</b>")

    return await query.edit_message_text(text=message, parse_mode=P_HTML)


def run_api():
    print('API:', 'Starting bot...')

    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('subscribe', start_command))
    app.add_handler(CommandHandler('info', info_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('undohelp', undohelp_command))
    app.add_handler(CommandHandler('bugreport', bugreport_command))
    app.add_handler(CommandHandler('addcontact', addcontact_command))
    app.add_handler(CommandHandler('showcontacts', showcontacts_command))
    app.add_handler(CommandHandler('delcontact', delcontact_command))
    app.add_handler(CommandHandler('addverif', addverif_command))
    app.add_handler(CommandHandler('showverifs', showverifs_command))
    app.add_handler(CommandHandler('delverif', delverif_command))
    app.add_handler(CommandHandler('skip', skip_command))
    app.add_handler(CommandHandler('undoskip', undoskip_command))
    app.add_handler(CommandHandler('fastcheck', fastcheck_command))
    app.add_handler(CommandHandler('stop', kill_user_data))
    app.add_handler(CommandHandler('unsubscibe', kill_user_data))
    app.add_handler(CommandHandler('request', request_command))
    app.add_handler(CommandHandler('empty', empty_command))

    # Buttons under text
    app.add_handler(CallbackQueryHandler(button))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    app.run_polling()
