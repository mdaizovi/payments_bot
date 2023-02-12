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
        "Use /chat_id to get the id of this chat to use as event id, /link to make a link to pay for this event"
    )
    await update.message.reply_text(msg)

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = f"This chat id is {update.message.chat.id}"
    await update.message.reply_text(msg)

async def share_spreadsheet_with_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    repository = EventRepository(chat_id)
    user = update.message.from_user
    if user['username'] == ADMIN_USERNAME:
        sheet_input=SPREADSHEET_NAME
        input_mex = update.message.text
        email = input_mex.split('/sharesheet ')[1]
        repository.db.share_spreadsheet(sheet_input, email)
    else:
        msg = f"Sorry Backend can only be shared with the admin user"
    await update.message.reply_text(msg)


async def create_link(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = update.message.chat_id
    repository = EventRepository(chat_id)
    user = update.message.from_user
    if user['username'] != ADMIN_USERNAME:
        msg = f"Sorry link can only be made by the Admin user {ADMIN_USERNAME}"
        await update.message.reply_text(msg)
        return
    
    event_name = repository.get_event_display_name()
    title = event_name
    description = f"Sign up for {event_name}"
    # select a payload just for you to recognize its the donation from your bot
    payload = json.dumps({"chat_id":chat_id, "bot_key": SECRET_BOT_KEY})
    currency = "EUR"
    price = repository.get_event_price_int()
    prices = [LabeledPrice("Admission", price)]
    link = await context.bot.create_invoice_link(
        title=title, description=description, payload=payload, provider_token=PAYMENT_PROVIDER_TOKEN, 
        currency=currency, prices=prices,
        need_name=True, need_email=True, need_shipping_address=False,
        send_phone_number_to_provider=True,
        send_email_to_provider=True
        )
    await update.message.reply_text(link)

async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Answers the PreQecheckoutQuery"""
    query = update.pre_checkout_query
    print(query)
    payload = json.loads(query.invoice_payload)
    # check the payload, is this from your bot?
    if payload["bot_key"] != SECRET_BOT_KEY:
        # answer False pre_checkout_query
        await query.answer(ok=False, error_message="Something went wrong...")
    chat_id = payload["chat_id"]
    repository = EventRepository(chat_id)
    event_name = repository.get_event_display_name()
    if repository.event_is_full():
        msg = f"I'm sorry, {event_name} is currently full. Feel free to try again later, in case of cancellation"
        await query.answer(ok=False, error_message=msg)
    if not repository.event_is_for_sale():
        dt = repository._get_event_start_sale_datetime()
        msg = f"I'm sorry, {event_name} is not for sale until {dt.strftime('%m.%d.%Y')} at {dt.strftime('%H:%M')}"
        await query.answer(ok=False, error_message=msg)
    else:
        await query.answer(ok=True)


# finally, after contacting the payment provider...
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Confirms the successful payment and adds user to Participants"""
    receipt = update.message.successful_payment
    payload = json.loads(receipt.invoice_payload)
    chat_id = payload["chat_id"]
    repository = EventRepository(chat_id)
    event_name = repository.get_event_display_name()
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
    await update.message.reply_text(f"Thank you for signing up for {event_name}")


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # simple start function
    application.add_handler(CommandHandler("start", start_callback))

    application.add_handler(CommandHandler("chat_id", get_chat_id))
    application.add_handler(CommandHandler("sharesheet", share_spreadsheet_with_admin))
    application.add_handler(CommandHandler("link", create_link))

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