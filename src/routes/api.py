import asyncio
import base64
import io

import qrcode
from aiohttp import web
from telethon.sessions import StringSession

from services.client import start_session, parse_chat

app = web.Application()
routes = web.RouteTableDef()


@routes.get('/login')
async def login(request: web.Request):
    session = request.cookies.get('session')
    username = ''

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async with start_session(session) as client:
        if not await client.is_user_authorized():
            async def login_() -> StringSession | None:
                qr = await client.qr_login()
                img = qrcode.make(qr.url)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                data = {
                    'type': 'auth',
                    'link': qr.url,
                    'img': base64.b64encode(buffer.getvalue()).decode()
                }
                await ws.send_json(data)

                try:
                    await qr.wait()
                except asyncio.TimeoutError:
                    # msg = await ws.receive(0.1)
                    # if msg.data == 'CLOSE':
                    #     return None
                    return await login_()
                else:
                    return client.session.save()

            session = await login_()
        username = (await client.get_me()).username

    ws.set_cookie('session', session)
    await ws.send_json({
        'type': 'status',
        'status': 'logged in',
        'session': session,
        'username': username
    })
    await ws.close()

    return ws


@routes.get('/logout')
async def logout(request: web.Request):

    response = web.Response(text='logged out', status=200)

    session = request.cookies.get('session')
    if session is None:
        return response

    async with start_session(session) as client:
        await client.log_out()

    return response


@routes.get('/start')
async def test(request: web.Request):
    session = request.cookies.get('session')
    if session is None:
        return web.Response(text='Unauthorized', status=401)

    buffer = await parse_chat(session)

    return web.Response(
        body=buffer.getvalue(),
        content_type='image/jpg'
    )


app.add_routes(routes)
