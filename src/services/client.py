import io
from contextlib import AbstractAsyncContextManager, asynccontextmanager

import matplotlib.dates
import matplotlib.pyplot as plt
import matplotlib.ticker
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.types import Dialog, Chat, Message, User

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


async def get_chat_info(session: str, chat_id: int) -> dict:
    """Collect chat info"""

    async with start_session(session) as client:
        user: User = await client.get_entity(chat_id)
        msg_count = (await client.get_messages(user, limit=0)).total

        return {
            'id': user.id,
            'message_count': msg_count
        }


async def get_chat_list(session: str) -> list[dict]:
    """Fetching chat list"""

    async with start_session(session) as client:

        chats: list[Chat] = await client.get_dialogs()
        return [{'id': chat.id, 'name': chat.title} for chat in chats]


async def export_messages(session: str, chat_id: int) -> list[dict]:
    """Export messages from chat"""

    async with start_session(session) as client:

        chat: Chat = await client.get_entity(chat_id)
        messages: list[Message] = await client.get_messages(chat, limit=None)

        return [message.to_dict() for message in messages]


async def parse_chat(session: str) -> io.BytesIO:
    async with start_session(session) as client:

        me = await client.get_me()
        dialog = await get_door_bot_dialog(client)

        messages = await client.get_messages(dialog, from_user=me)

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
