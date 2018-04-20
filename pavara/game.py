from direct.showbase.ShowBase import ShowBase
from panda3d.core import AmbientLight, VBase4, AntialiasAttrib, CollisionTraverser, Point3
from panda3d.physics import ForceNode, LinearVectorForce

from .maps import load_maps
from .sky import Sky
from .objects import PhysicalObject
from .player import Player

import asyncio


class Game (ShowBase):

    def __init__(self):
        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.map = None

        # self.sky = Sky(self.cam, self.loader)

        self.set_frame_rate_meter(True)
        self.set_background_color(0, 0, 0)
        self.enable_particles()
        self.disable_mouse()

        self.render.set_antialias(AntialiasAttrib.M_multisample)

        self.player = Player()
        self.floater = self.player.actor_node.attach_new_node('floater')
        self.floater.set_pos(0, 2.0, 1.0)

        axis = self.loader.load_model('zup-axis')
        axis.reparent_to(self.render)

    def tick(self):
        try:
            self.player.tick(self.mouseWatcherNode)

            head = self.player.actor_node.get_pos() + Point3(0, 0, 1.0)
            self.camera.set_pos(head)
            self.camera.look_at(self.floater)

            self.taskMgr.step()
            self.loop.call_soon(self.tick)
        except Exception as ex:
            print(ex)
            self.loop.stop()

    def run(self):
        self.tick()
        self.loop.run_forever()
        self.loop.close()

    def load_map(self, filename):
        if self.map:
            self.render.remove_node(self.map.node)
        self.map = load_maps(filename, self.loader)[0]

        gravity_node = ForceNode('gravity')
        gravity_node.add_force(self.map.gravity)
        self.render.attach_new_node(gravity_node)
        self.physicsMgr.add_linear_force(self.map.gravity)

        self.cTrav = CollisionTraverser('collisions')
        self.cTrav.show_collisions(self.render)

        self.map.objects.append(self.player)

        for obj in self.map.objects:
            obj.setup(self.loader)
            if isinstance(obj, PhysicalObject):
                self.cTrav.add_collider(obj.collision_node, obj.collision_handler)
                self.physicsMgr.attach_physical_node(obj.actor)
            obj.node.reparent_to(self.render)
