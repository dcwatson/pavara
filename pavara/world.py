from panda3d.bullet import BulletDebugNode, BulletWorld
from panda3d.core import NodePath, Vec3


class World:

    def __init__(self, loader):
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

    def tick(self, dt):
        self.frame += 1
        self.physics.doPhysics(dt)
        for obj in self.objects.values():
            obj.dirty = False
            obj.update(self, dt)
        state = {}
        for obj in self.objects.values():
            if obj.dirty:
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

    def load_model(self, name):
        """
        Stubbed out here in case we want to allow adding/loading custom models from map XML.
        """
        return self.loader.load_model(name)

    def get_state(self):
        states = {}
        for world_id, obj in self.objects.items():
            states[world_id] = obj.get_state()
        return states

    def set_state(self, states):
        for world_id, state in states.items():
            self.objects[world_id].set_state(state)
