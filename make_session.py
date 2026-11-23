# Run this ON YOUR OWN Android device (Pydroid 3 or Termux).
# Never send your OTP, 2FA password, or printed session string to anyone.

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

async def main():
    api_id = int(input("Your Telegram API_ID: ").strip())
    api_hash = input("Your Telegram API_HASH: ").strip()
    phone = input("Your Telegram phone number with country code: ").strip()

    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.connect()
    try:
        await client.send_code_request(phone)
        code = input("Enter the login code received in Telegram: ").strip()
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = input("Enter your Telegram 2-step verification password: ")
            await client.sign_in(password=password)

        print("\nSESSION STRING (SECRET — paste only into your own Render Environment):\n")
        print(client.session.save())
        print("\nDo not share this string. Anyone with it may access your Telegram account.")
    finally:
        await client.disconnect()

asyncio.run(main())
