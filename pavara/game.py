from direct.showbase.ShowBase import ShowBase
from panda3d.core import AntialiasAttrib, ClockObject, Vec3

from .maps import load_map
from .player import Player
from .world import World

import asyncio
import random
import traceback


class Game (ShowBase):

    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.clock = ClockObject.getGlobalClock()

        self.set_frame_rate_meter(True)
        self.set_background_color(0, 0, 0)
        self.disable_mouse()

        self.render.set_antialias(AntialiasAttrib.M_multisample)

        self.world = World(self.loader)
        self.player = Player()

        # self.world.attach(self.player)

        # axis = self.loader.load_model('zup-axis')
        # axis.reparent_to(self.render)

        self.camera.set_pos(0, -150, 150)
        self.camera.look_at(0, 0, 0)

        self.accept('f-up', self.explode)

    def explode(self):
        print("BOOM")
        for obj in self.world.objects:
            if hasattr(obj, 'mass') and obj.mass > 0:
                obj.velocity = Vec3(
                    random.random() * 3.0,
                    random.random() * 3.0,
                    random.random() * 20.0,
                )

    def tick(self):
        try:
            self.world.tick(self.clock.getDt())

            # head = self.player.actor_node.get_pos() + Point3(0, 0, 1.0)
            # self.camera.set_pos(head)
            # self.camera.look_at(self.floater)

            self.taskMgr.step()
            self.loop.call_soon(self.tick)
        except Exception as ex:
            traceback.print_exc()
            self.loop.stop()

    def run(self):
        self.tick()
        self.loop.run_forever()
        self.loop.close()

    def load(self, filename):
        load_map(filename, self.world)
        self.world.node.reparent_to(self.render)
