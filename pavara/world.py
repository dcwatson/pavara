from panda3d.bullet import BulletDebugNode, BulletWorld
from panda3d.core import AmbientLight, DirectionalLight, NodePath, TransparencyAttrib, Vec3

from .constants import DEFAULT_AMBIENT_COLOR
from .geom import to_cartesian
from .objects import GameObject, PhysicalObject

import math


class World:

    def __init__(self, loader=None, camera=None, debug=False):
        self.loader = loader
        self.camera = camera
        self.physics = BulletWorld()
        self.gravity = Vec3(0, 0, -30.0)
        self.physics.set_gravity(self.gravity)
        self.objects = {}
        self.frame = 0
        self.last_object_id = 0
        self.incarnators = []
        self.debug = debug
        self.setup()
        self.commands = []

    def setup(self):
        self.node = NodePath('world')
        self.node.set_transparency(TransparencyAttrib.MAlpha)
        if self.debug:
            d = BulletDebugNode('Debug')
            d.show_wireframe(True)
            d.show_normals(True)
            self.node.attach_new_node(d).show()
            self.physics.set_debug_node(d)
        if self.camera:
            self.camera.node().get_lens().set_fov(80.0, 50.0)
            self.camera.node().get_lens().set_near(0.1)
        # Default ambient light
        alight = AmbientLight('ambient')
        alight.set_color(DEFAULT_AMBIENT_COLOR)
        self.ambient = self.node.attach_new_node(alight)
        self.node.set_light(self.ambient)
        # Default directional lights
        self.add_celestial(math.radians(20), math.radians(45), (1, 1, 1, 1), 0.4, 30.0)
        self.add_celestial(math.radians(200), math.radians(20), (1, 1, 1, 1), 0.3, 30.0)

    def tick(self, dt):
        self.frame += 1
        self.physics.doPhysics(dt, 4, 1.0 / 60.0)
        state = {}
        for obj in list(self.objects.values()):
            if obj.update(self, dt):
                state[obj.world_id] = obj.get_state()
        for cmd, args in self.commands:
            yield cmd, args
        if state:
            yield 'state', {'frame': self.frame, 'state': state}
        self.commands = []

    def attach(self, obj):
        obj.setup(self)
        if obj.world_id is None:
            self.last_object_id += 1
            obj.world_id = self.last_object_id
        self.objects[obj.world_id] = obj
        obj.attached(self)
        if self.frame > 0 and False:
            self.commands.append(('attached', {
                'objects': [obj.serialize()],
                'state': {
                    obj.world_id: obj.get_state(),
                }
            }))
        return obj

    def remove(self, world_id):
        if isinstance(world_id, GameObject):
            world_id = world_id.world_id
        if world_id not in self.objects:
            return
        self.objects[world_id].removed(self)
        del self.objects[world_id]
        if self.frame > 0:
            self.commands.append(('removed', {'world_ids': [world_id]}))

    def find(self, pos, radius):
        for obj in self.objects.values():
            if isinstance(obj, PhysicalObject):
                d = (obj.node.get_pos() - pos).length()
                if d <= radius:
                    yield obj, d

    def add_incarnator(self, pos, heading):
        self.incarnators.append((pos, heading))

    def load_model(self, name):
        """
        Stubbed out here in case we want to allow adding/loading custom models from map XML.
        """
        return self.loader.load_model(name) if self.loader else None

    def serialize(self):
        return {world_id: obj.serialize() for world_id, obj in self.objects.items()}

    def deserialize(self, data):
        self.node.remove_node()
        self.setup()
        for world_id, obj_data in data.items():
            self.attach(GameObject.deserialize(obj_data))

    def get_state(self):
        states = {}
        for world_id, obj in self.objects.items():
            states[world_id] = obj.get_state()
        return states

    def set_state(self, states, fluid=True):
        for world_id, state in states.items():
            self.objects[world_id].set_state(state, fluid=fluid)

    def add_celestial(self, azimuth, elevation, color, intensity, radius):
        location = Vec3(to_cartesian(azimuth, elevation, 1000.0 * 255.0 / 256.0))
        if intensity:
            dlight = DirectionalLight('celestial')
            dlight.set_color((color[0] * intensity, color[1] * intensity, color[2] * intensity, 1.0))
            node = self.node.attach_new_node(dlight)
            node.look_at(*(location * -1))
            self.node.set_light(node)
