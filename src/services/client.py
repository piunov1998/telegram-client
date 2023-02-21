import asyncio
import io
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from threading import RLock

import matplotlib.dates
import matplotlib.pyplot as plt
import matplotlib.ticker
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.types import Dialog, Chat, Message

api_id = 25779309
api_hash = '99d351c9c7b27e47e2978465add418a3'


class Client:

    __instances__ = dict()
    __lock__ = RLock()

    def __new__(cls, session: str, *args, **kwargs):
        if session not in cls.__instances__:

            with cls.__lock__:
                instance = super().__new__(cls)
                cls.__instances__[session] = instance

        return cls.__instances__[session]

    def __init__(self, session: str):
        session = StringSession(session)
        self.client = TelegramClient(session, api_id, api_hash)

    def __enter__(self):
        loop = asyncio.get_running_loop()
        future = asyncio.run_coroutine_threadsafe(self.__aenter__(), loop)
        future.result(5)

    def __exit__(self, *args, **kwargs):
        asyncio.get_event_loop().create_task(self.__aexit__(*args, **kwargs))

    async def __aenter__(self):
        if not self.client.is_connected():
            await self.client.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

    async def get_chat_list(self) -> list[dict]:
        """Fetching chat list"""

        chats: list[Chat] = await self.client.get_dialogs()
        return [{'id': chat.id, 'name': chat.title} for chat in chats]

    async def get_chat_info(self, chat_id: int) -> dict:
        """Collect chat info"""

        await self.client.get_dialogs()
        chat = await self.client.get_entity(chat_id)
        msg_count = (await self.client.get_messages(chat, limit=0)).total

        return {
            'id': chat_id,
            'message_count': msg_count
        }

    async def export_messages(self, chat_id: int) -> list[dict]:
        """Export messages from chat"""

        chat: Chat = await self.client.get_entity(chat_id)
        messages: list[Message] = await self.client.get_messages(chat)

        return [message.to_dict() for message in messages]


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
