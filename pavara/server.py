from direct.showbase.ShowBase import ShowBase
from panda3d.core import Vec3, loadPrcFileData

from .log import configure_logging
from .maps import load_map
from .network import MsgpackProtocol
from .world import World

import argparse
import asyncio
import logging
import os
import random


logger = logging.getLogger('pavara.server')


class Player:

    def __init__(self, protocol):
        self.name = 'unnamed'
        self.protocol = protocol

    @property
    def pid(self):
        return self.protocol.pid

    def send(self, cmd, **args):
        self.protocol.send(cmd, **args)


class Server (ShowBase):

    def __init__(self, opts):
        super().__init__()
        self.opts = opts
        self.timestep = 1.0 / 30.0
        self.loop = asyncio.get_event_loop()
        self.map = None
        self.world = None
        self.players = {}

    def connected(self, proto):
        logger.debug('Player %s connected', proto.pid)
        self.players[proto.pid] = Player(proto)

    def disconnected(self, proto):
        logger.debug('Player %s disconnected', proto.pid)
        del self.players[proto.pid]

    def handle(self, proto, cmd, **args):
        logger.debug('Message received from Player %s: %s', proto.pid, cmd)
        player = self.players[proto.pid]
        func = getattr(self, 'handle_{}'.format(cmd), None)
        if func:
            func(player, **args)
        else:
            logger.error('Unknown command from Player %s: %s', proto.pid, cmd)

    def game_loop(self):
        for cmd, args in self.world.tick(self.timestep):
            self.broadcast(cmd, **args)
        self.loop.call_later(self.timestep, self.game_loop)

    def run(self):
        logger.debug('Listening on %s:%s', self.opts.addr, self.opts.port)
        coro = self.loop.create_server(lambda: MsgpackProtocol(self), self.opts.addr, self.opts.port)
        self.loop.run_until_complete(coro)
        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.loop.close()

    def broadcast(self, cmd, **args):
        for pid, player in self.players.items():
            player.send(cmd, **args)

    def handle_join(self, player, **args):
        player.name = args.get('name', player.name)
        logger.debug('Player %s joined as %s', player.pid, player.name)
        self.broadcast('joined', name=player.name, pid=player.pid)
        if self.world and self.map_xml:
            player.send('loaded', xml=self.map_xml, state=self.world.get_state())

    def handle_load(self, player, **args):
        if self.world:
            return
        self.map_xml = args['xml']
        self.world = World(self.loader)
        m = load_map(self.map_xml, self.world)
        logger.debug('Player %s loaded map "%s"', player.pid, m.name)
        self.broadcast('loaded', xml=self.map_xml)

    def handle_start(self, player, **args):
        self.game_loop()
        self.broadcast('started')

    def handle_explode(self, player, **args):
        for obj in self.world.objects.values():
            if hasattr(obj, 'mass') and obj.mass > 0:
                obj.velocity = Vec3(
                    random.random() * 3.0,
                    random.random() * 3.0,
                    random.random() * 20.0,
                )


if __name__ == '__main__':
    configure_logging()

    pavara_root = os.path.dirname(os.path.abspath(__name__))
    loadPrcFileData('', """
        window-type none
        model-path %s
    """ % pavara_root)

    parser = argparse.ArgumentParser(description='Pavara server')
    parser.add_argument('-a', '--addr', default='0.0.0.0')
    parser.add_argument('-p', '--port', type=int, default=19567)
    server = Server(parser.parse_args())
    server.run()