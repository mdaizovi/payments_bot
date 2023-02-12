#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""Basic example for a bot that can receive payment from user."""

import logging
import datetime
import json
from telegram import __version__ as TG_VER

from settings import ADMIN_USERNAME, TELEGRAM_BOT_TOKEN, STRIPE_TOKEN, SECRET_BOT_KEY, SPREADSHEET_NAME,EXAMPLE_SHEET_NAME
from repository import EventRepository

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import LabeledPrice, ShippingOption, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


PAYMENT_PROVIDER_TOKEN = STRIPE_TOKEN

async def start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays info on how to use the bot."""
    msg = (
        "Use /newevent to make a new event, /pay to pay for this event"
    )
    await update.message.reply_text(msg)


async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f"If you need support please contact {ADMIN_USERNAME}")

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = f"This chat id is {update.message.chat.id}"
    await update.message.reply_text(msg)

async def new_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Get example sheet, duplicate contents, make new sheet with example data. tell user id.
    #Problem: won't copy format, just contents.
    repository = EventRepository()
    example_spreadsheet = repository.spreadsheet.worksheet(EXAMPLE_SHEET_NAME)
    contents = example_spreadsheet.get_all_values()
    print("contents")
    print(contents)
    chat_id = update.message.chat_id
    event_sheet = repository.db.create_spreadsheet(chat_id)
    #Something like this, not exactly this, this is an example.
    # event_sheet.batch_update([
    #             {
    #                 'range': 'A1:J1', # head
    #                 'values': [['a', 'b', 'c']],
    #             },
    #             {
    #                 'range': 'A2', # values
    #                 'values': df_array 
    #             }
    #         ])

async def share_spreadsheet_with_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    repository = EventRepository(chat_id)
    user = update.message.from_user
    #print('You talk with user {} and his user ID: {} '.format(user['username'], user['id']))
    if user['username'] == ADMIN_USERNAME:
        sheet_input=SPREADSHEET_NAME
        input_mex = update.message.text
        email = input_mex.split('/sharesheet ')[1]
        repository.db.share_spreadsheet(sheet_input, email)
    else:
        msg = f"Sorry Backend can only be shared with the admin user"
    await update.message.reply_text(msg)


async def pay_for_event(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = update.message.chat_id
    repository = EventRepository(chat_id)
    event_name = repository.get_event_display_name()
    if repository.event_is_full():
        msg = f"I'm sorry, {event_name} is currently full. Feel free to try again later, in case of cancellation"
        await update.message.reply_text(msg)
        return
    if not repository.event_is_for_sale():
        dt = repository._get_event_start_sale_datetime()
        msg = f"I'm sorry, {event_name} is not for sale until {dt.strftime('%m.%d.%Y')} at {dt.strftime('%H:%M')}"
        await update.message.reply_text(msg)
        return

    title = event_name
    description = f"Sign up for {event_name}"
    # select a payload just for you to recognize its the donation from your bot
    payload = json.dumps({"chat_id":chat_id, "bot_key": SECRET_BOT_KEY})
    currency = "EUR"
    price = repository.get_event_price_int()
    prices = [LabeledPrice("Admission", price)]
    await context.bot.send_invoice(
        chat_id, title, description, payload, PAYMENT_PROVIDER_TOKEN, currency, prices,
        need_name=True, need_email=True, need_shipping_address=False,
        send_phone_number_to_provider=True,
        send_email_to_provider=True
    )
    # delete initial /pay message
    await context.bot.delete_message(chat_id=update.message.chat_id,
               message_id=update.message.message_id,)


# after (optional) shipping, it's the pre-checkout
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    print(query)
    payload = json.loads(query.invoice_payload)
    # check the payload, is this from your bot?
    if payload["bot_key"] != SECRET_BOT_KEY:
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Something went wrong...")
    else:
        await query.answer(ok=True)


# finally, after contacting the payment provider...
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirms the successful payment and adds user to Participants"""
    receipt = update.message.successful_payment
    payload = json.loads(receipt.invoice_payload)
    chat_id = payload["chat_id"]
    repository = EventRepository(chat_id)
    print("receipt")
    print(receipt)
    payload_value_list = [
                receipt.order_info.name,
                update.message.chat.username,
                receipt.order_info.email,
                receipt.order_info.phone_number,
                "stripe",
                str(datetime.datetime.now()),
                receipt.provider_payment_charge_id,
                receipt.telegram_payment_charge_id
                ]
    repository.add_participant(payload_value_list)
    await update.message.reply_text("Thank you for signing up for {}")


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # simple start function
    application.add_handler(CommandHandler("start", start_callback))

    application.add_handler(CommandHandler("chat_id", get_chat_id))
    application.add_handler(CommandHandler("pay", pay_for_event))
    application.add_handler(CommandHandler("sharesheet", share_spreadsheet_with_admin))
    application.add_handler(CommandHandler("new", new_event))

    #how to do unknown text in this version?
    #application.add_handler(MessageHandler(Filters.text, unknown_text))

    # Pre-checkout handler to final check
    application.add_handler(PreCheckoutQueryHandler(precheckout_callback))

    # Success! Notify your user!
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    )

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()