import asyncio
import base64
import io

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
from aiohttp import web
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

from services.client import start_session, parse_chat

app = web.Application()
routes = web.RouteTableDef()


@routes.get('/qrlogin')
async def qrlogin(request: web.Request):
    session = request.cookies.get('session')
    username = ''

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async with start_session(session) as client:
        if not await client.is_user_authorized():
            async def login_() -> StringSession | None:
                qr = await client.qr_login()
                qr_maker = qrcode.QRCode(image_factory=StyledPilImage)
                qr_maker.add_data(qr.url)
                img = qr_maker.make_image(
                    module_drawer=RoundedModuleDrawer(),
                    color_mask=SolidFillColorMask(front_color=(61, 118, 209))
                )
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
                    return await login_()
                except SessionPasswordNeededError:
                    await ws.send_json({
                        "type": "error",
                        "error": "password required"
                    })
                    return
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


@routes.get('/login')
async def login(request: web.Request):
    session = request.cookies.get('session')

    ws = web.WebSocketResponse()
    await ws.prepare(request)

    async with start_session(session) as client:

        async def code_callback():
            await ws.send_json({
                'type': 'f2a'
            })
            try:
                msg = await ws.receive(60)
            except asyncio.TimeoutError:
                return
            data = msg.json()
            return data.get('code')

        user_data = (await ws.receive(50)).json()
        await client.start(
            user_data['phone'],
            user_data['password'],
            code_callback=code_callback  # type: ignore
        )

        session = client.session.save()
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
