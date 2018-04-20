from panda3d.physics import ActorNode, PhysicsCollisionHandler
from panda3d.core import NodePath, CollisionBox, CollisionNode, CollisionPlane, Plane, Vec3, Point3


class GameObject:

    def __init__(self, name=None):
        self.name = name or '{}-{}'.format(self.__class__.__name__, id(self))

    def setup(self, loader):
        pass


class PhysicalObject (GameObject):

    def __init__(self, name=None, mass=None):
        super().__init__(name=name)
        self.mass = mass
        self.node = NodePath(self.name)
        # TODO: split out setup into two calls, one when the object is attached to the scene graph, and another to do what setup does now
        self.actor = ActorNode('{}-Actor'.format(self.name))
        self.actor_node = self.node.attach_new_node(self.actor)
        self.collision_node = self.actor_node.attach_new_node(CollisionNode('{}-Collision'.format(self.name)))
        if self.mass:
            self.actor.getPhysicsObject().setMass(self.mass)
        self.collision_handler = PhysicsCollisionHandler()
        self.collision_handler.add_collider(self.collision_node, self.actor_node)
        self.collision_node.show()

    def setup(self, loader):
        pass


class Block (PhysicalObject):

    def __init__(self, center, size, color, mass=None, name=None):
        super().__init__(name=name, mass=mass)
        self.center = center
        self.size = size
        self.color = color

    def setup(self, loader):
        block = loader.load_model('models/block')
        block.set_color(self.color)
        block.reparent_to(self.actor_node)

        self.collision_node.node().add_solid(CollisionBox(Point3(0, 0, 0), 0.5, 0.5, 0.5))

        if self.collision_handler:
            self.collision_handler.setDynamicFrictionCoef(1.0)
            self.collision_handler.setStaticFrictionCoef(1.0)

        self.node.set_scale(self.size)
        self.node.set_pos(self.center)


class Ground (PhysicalObject):

    def __init__(self):
        super().__init__()
        self.node = NodePath(self.name)
        self.collision_node = self.node.attach_new_node(CollisionNode('{}-Collision'.format(self.name)))

    def setup(self, loader):
        self.collision_node.node().add_solid(CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0))))
