import io
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import matplotlib.dates
import matplotlib.pyplot as plt
import matplotlib.ticker
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.types import Dialog, Chat, Message

api_id = 25779309
api_hash = '99d351c9c7b27e47e2978465add418a3'


@asynccontextmanager
async def start_session(
    session: str | None = None
) -> AbstractAsyncContextManager[TelegramClient]:
    """Session context manger"""

    client = TelegramClient(StringSession(session), api_id, api_hash)
    await client.connect()

    try:
        yield client
    finally:
        await client.disconnect()


def format_time(value: float, _):
    value = float(value)
    minutes = int(value * 60)
    hours = minutes // 60
    minutes -= hours * 60
    return f'{hours:0>2}:{minutes:0>2}'


async def get_door_bot_dialog(client: TelegramClient) -> Dialog | Chat:
    async for dialog in client.iter_dialogs():
        dialog: Dialog | Chat
        if dialog.title == 'OfficeDoorBot':
            return dialog


async def parse_chat(session: str) -> io.BytesIO:
    async with start_session(session) as client:

        me = await client.get_me()
        dialog = await get_door_bot_dialog(client)

        messages = []
        async for message in client.iter_messages(dialog):
            if message.from_id is None:
                continue
            message: Message
            if message.from_id.user_id == me.id:
                messages.append(message)

    x = [msg.date.date() for msg in messages]
    y = [msg.date.time().hour + msg.date.time().minute / 60 + 3 for msg in messages]

    axes = plt.subplot(1, 1, 1)
    axes.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(format_time))
    axes.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%d.%m'))
    plt.plot_date(matplotlib.dates.date2num(x), y, fmt='r.')
    plt.axhline(y=9, color='gray', linestyle='--')
    plt.ylim((8, 12))

    buffer = io.BytesIO()
    plt.savefig(buffer, format='jpg', dpi=400)
    return buffer
