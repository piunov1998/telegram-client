import logging
import os

import aiohttp_jinja2
from aiohttp import web
from jinja2 import FileSystemLoader

from routes import api_routes

logging.basicConfig(level=logging.INFO)
app = web.Application()
routes = web.RouteTableDef()
aiohttp_jinja2.setup(app, loader=FileSystemLoader('templates'))


@routes.get('/')
async def main(request: web.Request):
    return aiohttp_jinja2.render_template('main.html', request, None)


app.add_routes(routes)
app.add_routes(api_routes)
app.add_routes([web.static('/static', 'static')])


if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '80'))

    web.run_app(app, host=host, port=port)
