from panda3d.physics import ActorNode, PhysicsCollisionHandler
from panda3d.core import NodePath, CollisionBox, CollisionNode, CollisionPlane, Plane, Vec3, Point3, TransformState, BitMask32
from panda3d.bullet import BulletRigidBodyNode, BulletBoxShape, BulletGhostNode, BulletPlaneShape


class GameObject:

    def __init__(self, name=None):
        self.name = name or '{}-{}'.format(self.__class__.__name__, id(self))

    def setup(self, world):
        """
        Sets up this object, optionally returning a NodePath to attach to the scene graph.
        """
        pass

    def update(self, world, dt):
        pass

    def attached(self, world):
        pass

    def removed(self, world):
        pass

    def collision(self, world, obj):
        pass


class PhysicalObject (GameObject):

    body_class = BulletRigidBodyNode

    def __init__(self, name=None):
        super().__init__(name=name)
        self.body = self.body_class('{}-Body'.format(self.name))
        self.node = NodePath(self.body)

    def setup(self, world):
        return self.node

    def attached(self, world):
        world.physics.attach(self.body)

    def removed(self, world):
        world.physics.remove(self.body)


class SolidObject (PhysicalObject):

    def __init__(self, mass=0, name=None):
        super().__init__(name=name)
        self.mass = float(mass)
        self.body.set_mass(self.mass)


class GhostObject (PhysicalObject):
    body_class = BulletGhostNode


class Block (SolidObject):

    def __init__(self, center, size, color, mass=0, name=None):
        super().__init__(mass, name=name)
        self.center = center
        self.size = size
        self.color = color

    def setup(self, world):
        self.body.add_shape(BulletBoxShape(Vec3(0.5, 0.5, 0.5)))
        self.body.set_angular_damping(1.0)
        self.body.set_restitution(0.0)
        block = world.load_model('models/block')
        block.set_color(self.color)
        block.reparent_to(self.node)
        self.node.set_scale(self.size)
        self.node.set_pos(self.center)
        return self.node


class Ground (SolidObject):

    def setup(self, world):
        #self.body.add_shape(BulletPlaneShape(Vec3(0, 0, 1), 1))
        self.body.add_shape(BulletBoxShape(Vec3(0.5, 0.5, 0.5)))
        self.body.set_restitution(0.0)
        self.node.set_scale(100, 100, 1)
        self.node.set_pos(0, 0, -0.5)
        #self.node.set_p(-30)
        return self.node
