from panda3d.bullet import BulletWorld, BulletDebugNode
from panda3d.core import NodePath, Vec3


class World:

    def __init__(self, loader):
        self.loader = loader
        self.physics = BulletWorld()
        self.gravity = Vec3(0, 0, -9.81)
        self.physics.set_gravity(self.gravity)
        self.objects = []
        self.node = NodePath('world')
        # Debug node
        self.debug = BulletDebugNode('Debug')
        self.debug.show_wireframe(True)
        # self.debug.show_constraints(True)
        # self.debug.show_bounding_boxes(True)
        self.debug.show_normals(True)
        self.node.attach_new_node(self.debug).show()
        self.physics.set_debug_node(self.debug)

    def tick(self, dt):
        self.physics.doPhysics(dt)
        for obj in self.objects:
            obj.update(self, dt)

    def attach(self, obj):
        self.objects.append(obj)
        node = obj.setup(self)
        if node:
            node.reparent_to(self.node)
        obj.attached(self)

    def load_model(self, name):
        """
        Stubbed out here in case we want to allow adding/loading custom models from map XML.
        """
        return self.loader.load_model(name)
