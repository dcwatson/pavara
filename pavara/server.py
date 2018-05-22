from panda3d.core import Vec3, loadPrcFileData

from .log import configure_logging
from .maps import load_map
from .network import MsgpackProtocol
from .player import Player
from .world import World

import argparse
import asyncio
import logging
import os
import random


logger = logging.getLogger('pavara.server')


class Server:

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
        self.players[proto.pid] = Player(proto.pid, protocol=proto)

    def disconnected(self, proto):
        logger.debug('Player %s disconnected', proto.pid)
        if self.world:
            self.world.remove(self.players[proto.pid])
        del self.players[proto.pid]

    def handle(self, proto, cmd, **args):
        # logger.debug('Message received from Player %s: %s', proto.pid, cmd)
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

    def run(self, run_loop=True):
        logger.debug('Listening on %s:%s', self.opts.addr, self.opts.port)
        coro = self.loop.create_server(lambda: MsgpackProtocol(self), self.opts.addr, self.opts.port)
        self.loop.run_until_complete(coro)
        if run_loop:
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
        player.send('self', pid=player.pid)
        self.broadcast('joined', name=player.name, pid=player.pid)
        if self.world:
            player.send('loaded', objects=self.world.serialize(), state=self.world.get_state())

    def handle_load(self, player, **args):
        if self.world:
            return
        from direct.showbase.Loader import Loader
        loader = Loader(self)
        self.world = World(loader=loader)
        m = load_map(args['xml'], self.world)
        logger.debug('Player %s loaded map "%s"', player.pid, m.name)
        self.broadcast('loaded', objects=self.world.serialize())

    def handle_ready(self, player, **args):
        if player.world_id in self.world.objects:
            return
        self.world.attach(player)
        pos, heading = random.choice(self.world.incarnators)
        player.node.set_pos(pos)
        player.node.set_h(heading)
        self.broadcast('attached', objects=[player.serialize()], state={
            player.world_id: player.get_state(),
        })

    def handle_start(self, player, **args):
        if self.world and self.world.frame == 0:
            players = {}
#            incarnators = random.sample(self.world.incarnators, len(self.players))
#            for idx, pid in enumerate(self.players):
#                players[pid] = self.players[pid].get_state(incarn=incarnators[idx])
            self.game_loop()
            self.broadcast('started', players=players)

    def handle_input(self, player, **args):
        player.input(args['input'], args['pressed'])

    def handle_mouse(self, player, **args):
        player.mouse(args['x'], args['y'])

    def handle_fire(self, player, **args):
        from .weapons import Grenade
        floater_pos = player.floater.get_pos(self.world.node)
        direction = floater_pos - (player.node.get_pos() + Vec3(0, 0, 1.25))
        grenade = Grenade()
        grenade.node.set_pos(floater_pos)
        grenade.body.apply_central_impulse(direction * 100.0)
        self.world.attach(grenade)
        # TODO: need a better system for sending attached/removed events from the world
        self.broadcast('attached', objects=[grenade.serialize()], state={
            grenade.world_id: grenade.get_state(),
        })

    def handle_explode(self, player, **args):
        if not self.world:
            return
        for obj in self.world.objects.values():
            if hasattr(obj, 'mass') and obj.mass > 0:
                obj.body.set_active(True)
                obj.body.apply_central_impulse(Vec3(
                    random.uniform(-5000, 5000),
                    random.uniform(-5000, 5000),
                    random.uniform(-5000, 5000),
                ))


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
