from direct.showbase.ShowBase import ShowBase
from panda3d.core import AntialiasAttrib, WindowProperties, loadPrcFile, loadPrcFileData

from .log import configure_logging
from .network import MsgpackProtocol
from .objects import GameObject
from .world import World

import argparse
import asyncio
import logging
import math
import os
import sys


logger = logging.getLogger('pavara.client')


class Client (ShowBase):

    def __init__(self, opts):
        super().__init__()

        self.opts = opts
        self.throttle = 1.0 / opts.throttle

        self.loop = asyncio.get_event_loop()
        self.protocol = None
        self.pid = None
        self.world = None
        self.player = None
        self.overhead = True

        self.set_frame_rate_meter(True)
        self.set_background_color(0, 0, 0)
        self.disable_mouse()

        props = WindowProperties()
        props.set_cursor_hidden(True)
        props.set_mouse_mode(WindowProperties.M_confined)
        self.win.request_properties(props)

        self.render.set_antialias(AntialiasAttrib.M_multisample)

        self.accept('l-up', self.load)
        self.accept('r-up', self.ready)
        self.accept('g-up', self.start)
        self.accept('f-up', self.explode)
        self.accept('tab-up', self.toggle_camera)
        self.accept('mouse1', self.fire)
        self.accept('escape', sys.exit)

        self.taskMgr.add(self.check_mouse, 'check_mouse')

        motion = {
            'w': 'forward',
            's': 'backward',
            'a': 'left',
            'd': 'right',
            '2': 'center',
        }
        for key, cmd in motion.items():
            self.accept(key, self.input, [cmd, True])
            self.accept(key + '-up', self.input, [cmd, False])

        self.a = 0.0

    def load(self):
        with open('maps/icebox-classic.xml', 'r') as f:
            self.protocol.send('load', xml=f.read())

    def ready(self):
        self.protocol.send('ready')

    def start(self):
        self.protocol.send('start')

    def explode(self):
        self.protocol.send('explode')

    def input(self, cmd, pressed):
        self.protocol.send('input', input=cmd, pressed=pressed)

    def fire(self):
        self.protocol.send('fire')

    def toggle_camera(self):
        if self.player:
            if self.player.camera:
                self.player.camera = None
                self.camera.reparent_to(self.render)
                self.overhead = True
            else:
                self.player.set_camera(self.camera)
                self.overhead = False
        else:
            self.camera.reparent_to(self.render)
            self.overhead = True

    def check_mouse(self, task):
        mw = self.mouseWatcherNode
        if mw.has_mouse():
            x, y = mw.get_mouse_x(), mw.get_mouse_y()
            self.protocol.send('mouse', x=x, y=y)
            props = self.win.get_properties()
            self.win.move_pointer(0, int(props.get_x_size() / 2), int(props.get_y_size() / 2))
        return task.cont

    def render_loop(self):
        next_call = self.loop.time() + self.throttle
        if self.overhead:
            self.a += math.pi / 2400.0
            x = math.cos(self.a) * 100.0
            y = math.sin(self.a) * 100.0
            self.camera.set_pos(x, y, 150)
            self.camera.look_at(0, 0, 0)
        self.taskMgr.step()
        if self.world and self.opts.debug:
            # This is just so the BulletWorld draws the debug node.
            self.world.physics.doPhysics(0)
        self.loop.call_at(next_call, self.render_loop)

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

    def handle_self(self, **args):
        self.pid = args['pid']

    def handle_joined(self, **args):
        pass

    def handle_started(self, **args):
        self.player = self.world.objects[self.pid]
        self.player.set_camera(self.camera)
        self.overhead = False

    def handle_attached(self, **args):
        for data in args['objects']:
            self.world.attach(GameObject.deserialize(data))
        if 'state' in args:
            self.world.set_state(args['state'], fluid=False)

    def handle_removed(self, **args):
        for world_id in args['world_ids']:
            self.world.remove(world_id)

    def handle_state(self, **args):
        # logger.debug('Got state for frame %s', args['frame'])
        self.world.set_state(args['state'])

    def handle_loaded(self, **args):
        self.world = World(loader=self.loader, camera=self.cam, debug=self.opts.debug)
        self.world.deserialize(args['objects'])
        if 'state' in args:
            self.world.set_state(args['state'], fluid=False)
        self.world.node.reparent_to(self.render)


if __name__ == '__main__':
    configure_logging()

    pavara_root = os.path.dirname(os.path.abspath(__name__)).replace('\\', '/').replace('C:', '/c')
    loadPrcFile(os.path.join(pavara_root, 'pavara.prc'))
    loadPrcFileData('', """
        model-path %s
    """ % pavara_root)

    parser = argparse.ArgumentParser(description='Pavara client')
    parser.add_argument('-a', '--addr', default='127.0.0.1')
    parser.add_argument('-p', '--port', type=int, default=19567)
    parser.add_argument('-n', '--name', default='unnamed')
    parser.add_argument('-l', '--local', action='store_true', default=False)
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-t', '--throttle', type=float, default=100.0)

    opts = parser.parse_args()

    if opts.local:
        from .server import Server
        server = Server(opts)
        server.run(run_loop=False)

    client = Client(opts)
    client.run()
