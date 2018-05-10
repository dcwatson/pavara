from direct.showbase.ShowBase import ShowBase
from panda3d.core import AntialiasAttrib, loadPrcFile, loadPrcFileData

from .log import configure_logging
from .maps import load_map
from .network import MsgpackProtocol
from .world import World

import argparse
import asyncio
import logging
import math
import os


logger = logging.getLogger('pavara.client')


class Client (ShowBase):

    def __init__(self, opts):
        super().__init__()

        self.opts = opts
        self.fps_step = 1.0 / 60.0

        self.loop = asyncio.get_event_loop()
        self.protocol = None
        self.world = None

        self.set_frame_rate_meter(True)
        self.set_background_color(0, 0, 0)
        self.disable_mouse()

        self.render.set_antialias(AntialiasAttrib.M_multisample)

        self.camera.set_pos(0, 0, 200)
        self.camera.look_at(0, 0, 0)

        self.accept('l-up', self.load)
        self.accept('r-up', self.start)
        self.accept('f-up', self.explode)

        self.a = 0.0

    def load(self):
        with open('maps/icebox-classic.xml', 'r') as f:
            self.protocol.send('load', xml=f.read())

    def start(self):
        self.protocol.send('start')

    def explode(self):
        self.protocol.send('explode')

    def render_loop(self):
        self.a += math.pi / 2400.0
        x = math.cos(self.a) * 130.0
        y = math.sin(self.a) * 130.0
        self.camera.set_pos(x, y, 150)
        self.camera.look_at(0, 0, 0)
        self.taskMgr.step()
        self.loop.call_soon(self.render_loop)

    def run(self):
        coro = self.loop.create_connection(lambda: MsgpackProtocol(self), self.opts.addr, self.opts.port)
        try:
            self.loop.run_until_complete(coro)
        except ConnectionRefusedError:
            logger.debug('Connection refused to %s:%s', self.opts.addr, self.opts.port)
        else:
            self.render_loop()
            self.loop.run_forever()
        self.loop.close()

    def load_map(self, xml):
        self.world = World(self.loader)
        load_map(xml, self.world)
        self.world.node.reparent_to(self.render)

    # MsgpackProtocol delegate

    def connected(self, proto):
        logger.debug('Connected to %s:%s', proto.address, proto.port)
        self.protocol = proto
        self.protocol.send('join', name=self.opts.name)

    def disconnected(self, proto):
        logger.debug('Disconnected')
        self.protocol = None

    def handle(self, proto, cmd, **args):
        # logger.debug('Message received: %s', cmd)
        func = getattr(self, 'handle_{}'.format(cmd), None)
        if func:
            func(**args)
        else:
            logger.error('Unknown command: %s', cmd)

    def handle_joined(self, **args):
        pass

    def handle_state(self, **args):
        # logger.debug('Got state for frame %s', args['frame'])
        self.world.set_state(args['state'])

    def handle_loaded(self, **args):
        self.world = World(self.loader)
        load_map(args['xml'], self.world)
        if 'state' in args:
            self.world.set_state(args['state'], fluid=False)
        self.world.node.reparent_to(self.render)


if __name__ == '__main__':
    configure_logging()

    pavara_root = os.path.dirname(os.path.abspath(__name__))
    loadPrcFile(os.path.join(pavara_root, 'pavara.prc'))
    loadPrcFileData('', """
        model-path %s
    """ % pavara_root)

    parser = argparse.ArgumentParser(description='Pavara client')
    parser.add_argument('-a', '--addr', default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=19567)
    parser.add_argument('-n', '--name', default='unnamed')
    parser.add_argument('-l', '--local', action='store_true', default=False)

    opts = parser.parse_args()

    if opts.local:
        from .server import Server
        server = Server(opts)
        server.run(run_loop=False)

    client = Client(opts)
    client.run()
