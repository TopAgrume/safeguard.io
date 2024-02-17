from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils.env_pipeline import AccessEnv
import telegram

TOKEN, BOT_USERNAME = AccessEnv.telegram_keys()
P_HTML = telegram.constants.ParseMode.HTML


def verify_condition(func):
    async def wrapper(update, context, **kwargs):
        message_type: str = update.message.chat.type
        if message_type == 'group':
            message_body: str = message_body.lower()
            if BOT_USERNAME in message_body:
                # new_text: str = message_body.replace(BOT_USERNAME, '').strip()
                response = 'This bot does not support groups for now. 🚫'
                await update.message.reply_text(response)
            else:
                return
        username = update.message.from_user.username
        if username is None or username == "":
            message = ("Please create a username in your Telegram profile in order to use my features."
                       " Then use /start if you are not already registered.")
            await update.message.reply_text(message)
        else:
            await func(update, context, **kwargs)

    return wrapper


@verify_condition
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    user_id = update.message.from_user.id
    user_first_name: str = str(update.message.chat.first_name)

    if user_id is None:
        message = (f"Hello {user_first_name} 👋! Make sure to <b>create a username</b> in your account settings"
                   "to use my features. When this is done, use the <b>/start</b> command.")
        return await update.message.reply_text(message, parse_mode=P_HTML)

    username = update.message.from_user.username
    print("COMMAND:", f"Start user @{username}")
    if str(user_id) in AccessEnv.on_get_users():
        print("COMMAND:", "Already inside")
        message = "Your profile is already linked with Safeguard.io!"
        return await update.message.reply_text(message)

    AccessEnv.on_create_user(user_id, username)
    message = f"Hello {user_first_name} 🌟! Thanks for chatting with me! I am Safeguard.io 😊."
    await update.message.reply_text(message)

    exploit_data = {}
    remove_user_id = []
    request_data = AccessEnv.on_get_request_user("dict")
    for origin_id, content in request_data.items():
        remove_tag = []
        for dest_tag in content["dest_tags"]:
            if username == dest_tag:
                print('COMMANDS:', f"Send new user request from @{username}")
                remove_tag.append(username)
                exploit_data[origin_id] = content['tag']

        content["dest_tags"] = [element for element in content["dest_tags"] if element not in remove_tag]

        if len(content["dest_tags"]) == 0:
            remove_user_id.append(origin_id)

    # Del request data
    for key in remove_user_id:
        if key in request_data:
            del request_data[key]

    AccessEnv.on_write_all_request(request_data)
    AccessEnv.on_write(user_id, "contact_request", exploit_data)

    for contact_key in exploit_data.keys():
        old_contacts = AccessEnv.on_read(int(contact_key), "contacts")
        for old_contact in old_contacts:
            if old_contact['tag'] == username:
                old_contact['id'] = user_id
        AccessEnv.on_write(int(contact_key), "contacts", old_contacts)

    return await request_command(update, context, quiet=True)


@verify_condition
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    message = ("Welcome! I'm here to ensure everything is smooth for you. Use these commands to interact with me:\n"
               "\n<b>Edit bot configuration</b>\n"
               "/start or /subscribe - Initiate a conversation with me.\n"
               "/stop or /unsubscribe - Delete personal related data.\n"
               "/info - Receive information on how to use the bot.\n"
               "\n<b>In case of emergency</b>\n"
               "/help - Request emergency assistance from your contacts.\n"
               "/undohelp - Disable emergency alerts.\n"
               "\n<b>Edit emergency contacts</b>\n"
               "/addcontact - Add new emergency contacts.\n"
               "/showcontacts - Display your list of emergency contacts.\n"
               "/delcontact - Delete specific emergency contacts.\n"
               "/request - View received association requests.\n"
               "\n<b>Edit daily messages</b>\n"
               "/addverif - Add a daily verification message.\n"
               "/showverifs - Display your list of daily verifications.\n"
               "/delverif - Delete specific daily verifications.\n"
               "/skip - Skip the next verification.\n"
               "/undoskip - Activate the previously skipped verification.\n"
               "/fastcheck - Perform a quick verification.\n"
               "\n<b>Miscellaneous</b>\n"
               "/bugreport - Report any bugs you encounter or suggest improvements!\n\n"
               "Feel free to ask for assistance or information anytime! 😊")

    print("COMMAND:", f"Info")
    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition
async def addcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"AddContact")
    message = ("Sure thing! Please provide me with a list of contacts you'd like to add. 📋\n"
               "<b>Make sure to use the following format:</b>\n\n"
               "<b>@username1</b>\n"
               "<b>@username2</b>\n\n"
               "Send /empty to keep the list empty.")

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "contacts")) > 9:
        message = "You cannot add an additional contacts (10 max). 🛑"
        return await update.message.reply_text(message)

    AccessEnv.on_write(user_id, "state", "addcontact")

    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition
async def showcontacts_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"ShowContacts")
    message = "Sure thing! Here is your list of contacts:\n\n"

    user_id = update.message.from_user.id
    contact_list = AccessEnv.on_read(user_id, "contacts")

    if len(contact_list) == 0:
        message = "<b>There is no emergency contact to display. 🆘</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    for contact in contact_list:
        if contact['pair']:
            message += f"👤 <b>@{contact['tag']}</b>\n"
            continue

        message += f"🚫 <b>@{contact['tag']}</b> - Waiting for pairing.\n"

    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition
async def delcontact_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"DeleteContact")
    message = "Sure! Chose the contact to delete.🗑️\n"

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "contacts")) == 0:
        message = "<b>No contact to delete. 📭</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    get_contacts = AccessEnv.on_read(user_id, "contacts")
    display = ['@' + contact['tag'] for contact in get_contacts]

    reply_markup = ReplyKeyboardMarkup([display], resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "delcontact")
    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition
async def addverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"AddDailyCheck")
    message = ("OK. Send me a list of daily verifications to add. 📅⏰\n"
               "<b>Please use this format</b>:\n\n"
               "08:05 - Awakening\n"
               "21:30 - End of the day\n\n"
               "Click /empty to cancel the operation.")

    user_id = update.message.from_user.id
    if len(AccessEnv.on_read(user_id, "daily_message")) > 5:
        message = "<b>You cannot add an additional daily check (6 max). 🛑</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    AccessEnv.on_write(user_id, "state", "addverif")
    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition
async def showverifs_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"ShowDailyChecks")
    message = "OK. Here is you list of daily verifications:\n\n"
    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")

    if len(verif_list) == 0:
        message = "<b>There is no daily check to display. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x["time"])

    skipped_verif = "\n<b>Skipped today:</b>\n\n"
    skip_bool, active = False, True
    for verif in sorted_list:
        if verif["active"] or verif["active"] is None:
            message += f"🕗 <b>{verif['time']}</b> - {verif['desc']}\n"
            active = False
            continue

        skipped_verif += f"🚫 <b>{verif['time']}</b> - {verif['desc']}\n"
        skip_bool = True

    message += "<b>No daily check for the next 24 hours.</b>  📅\n" if active else ""
    message += skipped_verif if skip_bool else ""
    return await update.message.reply_text(message, parse_mode=P_HTML)


@verify_condition
async def delverif_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"DeleteDailyChecks")
    message = ("Alright! Please choose the daily verifications you'd like to delete. ❌🕒\n"
               "Click /empty to cancel the operation.")

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")

    if len(AccessEnv.on_read(user_id, "daily_message")) == 0:
        message = "<b>No daily message to delete. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x["time"])

    keyboard = [
        [f"{elt['time']}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "delverif")
    return await update.message.reply_text(message, reply_markup=reply_markup)


@verify_condition
async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"SkipDailyCheck")
    message = ("Sure! Please choose the daily verifications you'd like to skip. 🚫🕒\n"
               "Click /empty to cancel the operation.")

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    verif_list = list(filter(lambda x: x["active"], verif_list))

    if len(verif_list) == 0:
        message = "<b>No daily message to skip. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x['time'])

    keyboard = [
        [f"{elt['time']}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "skip")
    return await update.message.reply_text(message, reply_markup=reply_markup)


@verify_condition
async def undoskip_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"Undo SkipDailyCheck")
    message = ("OK. Please choose the daily verifications you'd like to undo skip for. 🔄🕒\n"
               "Click /empty to cancel the operation.")

    user_id = update.message.from_user.id
    verif_list = AccessEnv.on_read(user_id, "daily_message")
    verif_list = list(filter(lambda x: not x['active'], verif_list))

    if len(verif_list) == 0:
        message = "<b>No daily message skip to undo. 📅</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    sorted_list = sorted(verif_list, key=lambda x: x['time'])

    keyboard = [
        [f"{elt['time']}" for elt in sorted_list],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    AccessEnv.on_write(user_id, "state", "undoskip")
    return await update.message.reply_text(message, reply_markup=reply_markup)


@verify_condition
async def bugreport_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"Bug Report")
    message = ("Sure! Please describe the bug and the steps you took to encounter it. 🐞📝\n"
               "Click /empty to cancel the operation.")

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "bugreport")
    return await update.message.reply_text(message)


@verify_condition
async def request_command(update: Update, context: ContextTypes.DEFAULT_TYPE, quiet: bool = False, **kwargs):
    print("COMMAND:", f"Association request")
    user_id = update.message.from_user.id
    contact_request = AccessEnv.on_read(user_id, "contact_request")

    if len(contact_request) == 0 and not quiet:
        message = "<b>There is no association request. 🤷‍♂️</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    for id, username in contact_request.items():
        print("COMMAND:", f"Notif user from del/add {user_id=} to {id}")
        message = f"<b>Do you want to accept the pairing invitation from @{username} 🤝?</b>"

        keyboard = [
            [
                InlineKeyboardButton("Yes", callback_data=f"+{id}"),
                InlineKeyboardButton("No", callback_data=f"-{id}"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition
async def fastcheck_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"Fast Check")
    message = ("Alright! When would you like to have the quick check? 🕒🚀 "
               "<b>(less than 20 minutes)</b>\n"
               "Click /empty to cancel the operation.")
    keyboard = [
        ["5 mn", "10 mn", "15 mn", "20 mn"],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "fastcheck")

    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"Help")
    user_id = update.message.from_user.id
    alert_mode = AccessEnv.on_read(user_id, "alert_mode")
    if alert_mode:
        message = "<b>You are already in alert mode! 🚨</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    if not AccessEnv.on_read(user_id, "response_message"):
        AccessEnv.on_write(user_id, "response_message", True)
        await update.message.reply_text("Answer received, daily verification has been turned off.")

    message = "<b>Do you want to notify emergency contacts? 🚨</b>"
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="1"),
            InlineKeyboardButton("No", callback_data="2"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return await update.message.reply_text(message, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition
async def undohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"Undo help")
    user_id = update.message.from_user.id
    if not AccessEnv.on_read(user_id, "alert_mode"):
        message = "<b>This operation can only be used in alert state! ⚠️</b>"
        return await update.message.reply_text(message, parse_mode=P_HTML)

    response = "<b>Do you want to cancel the alert? 🤔</b>"
    keyboard = [
        [
            InlineKeyboardButton("Yes", callback_data="3"),
            InlineKeyboardButton("No", callback_data="4"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return await update.message.reply_text(response, reply_markup=reply_markup, parse_mode=P_HTML)


@verify_condition
async def empty_command(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    user_id = update.message.from_user.id
    AccessEnv.on_write(user_id, "state", "")
    message = "Sure thing! Operation canceled. ✅"
    return await update.message.reply_text(message)


@verify_condition
async def kill_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE, **kwargs):
    print("COMMAND:", f"Kill user data")
    user_id = update.message.from_user.id
    AccessEnv.on_kill_data(user_id)
    message = "<b>Your personal data has been deleted.🗑️</b>"
    return await update.message.reply_text(message, parse_mode=P_HTML)
