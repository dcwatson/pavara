from panda3d.bullet import BulletDebugNode, BulletWorld
from panda3d.core import NodePath, Vec3

from .objects import GameObject


class World:

    def __init__(self, loader=None):
        self.loader = loader
        self.physics = BulletWorld()
        self.gravity = Vec3(0, 0, -9.81)
        self.physics.set_gravity(self.gravity)
        self.objects = {}
        self.node = NodePath('world')
        # Debug node
        self.debug = BulletDebugNode('Debug')
        self.debug.show_wireframe(True)
        # self.debug.show_constraints(True)
        # self.debug.show_bounding_boxes(True)
        self.debug.show_normals(True)
        self.node.attach_new_node(self.debug).show()
        self.physics.set_debug_node(self.debug)
        self.frame = 0
        self.last_object_id = 0
        self.incarnators = []

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
        if obj.world_id is None:
            self.last_object_id += 1
            obj.world_id = self.last_object_id
        self.objects[obj.world_id] = obj
        node = obj.setup(self)
        if node:
            node.reparent_to(self.node)
        obj.attached(self)

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
        self.node = NodePath('world')
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
