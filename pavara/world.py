from panda3d.bullet import BulletDebugNode, BulletWorld
from panda3d.core import AmbientLight, DirectionalLight, LColor, NodePath, Vec3

from .constants import DEFAULT_AMBIENT_COLOR
from .objects import GameObject


class World:

    def __init__(self, loader=None, debug=False):
        self.loader = loader
        self.physics = BulletWorld()
        self.gravity = Vec3(0, 0, -9.81)
        self.physics.set_gravity(self.gravity)
        self.objects = {}
        self.frame = 0
        self.last_object_id = 0
        self.incarnators = []
        self.debug = debug
        self.setup()

    def setup(self):
        self.node = NodePath('world')
        if self.debug:
            d = BulletDebugNode('Debug')
            d.show_wireframe(True)
            d.show_normals(True)
            self.node.attach_new_node(d).show()
            self.physics.set_debug_node(d)
        alight = AmbientLight('ambient')
        alight.set_color(DEFAULT_AMBIENT_COLOR)
        self.ambient = self.node.attach_new_node(alight)
        self.node.set_light(self.ambient)
        dlight = DirectionalLight('celestial')
        dlight.set_color(LColor(0.7, 0.7, 0.7, 1))
        self.directional = self.node.attach_new_node(dlight)
        self.directional.look_at(0, -1, -1)
        self.node.set_light(self.directional)

    def tick(self, dt):
        self.frame += 1
        self.physics.doPhysics(dt, 4, 1.0 / 60.0)
        state = {}
        for obj in self.objects.values():
            if obj.update(self, dt):
                state[obj.world_id] = obj.get_state()
        if state:
            yield 'state', {'frame': self.frame, 'state': state}

    def attach(self, obj):
        obj.setup(self)
        if obj.world_id is None:
            self.last_object_id += 1
            obj.world_id = self.last_object_id
        self.objects[obj.world_id] = obj
        obj.attached(self)

    def remove(self, obj):
        if obj.world_id not in self.objects:
            return
        del self.objects[obj.world_id]
        obj.removed(self)

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
