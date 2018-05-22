from direct.interval.LerpInterval import LerpPosHprInterval
from panda3d.bullet import BulletBoxShape, BulletConvexHullShape, BulletGhostNode, BulletPlaneShape, BulletRigidBodyNode
from panda3d.core import NodePath, Point3, Vec3

from .constants import Collision
from .geom import GeomBuilder

import importlib


class GameObject:
    world_id = None

    def __init__(self, name=None):
        self.name = name or '{}-{}'.format(self.__class__.__name__, id(self))

    def setup(self, world):
        """
        Sets up this object, optionally returning a NodePath to attach to the scene graph.
        """
        pass

    def update(self, world, dt):
        return False

    def attached(self, world):
        pass

    def removed(self, world):
        pass

    def collision(self, world, obj):
        pass

    def serialize(self):
        return {
            '__class__': '{}.{}'.format(self.__module__, self.__class__.__name__),
            'world_id': self.world_id,
            'name': self.name,
        }

    @classmethod
    def deserialize(cls, data):
        module_path, class_name = data.pop('__class__').rsplit('.', 1)
        module = importlib.import_module(module_path)
        world_id = data.pop('world_id')
        obj = getattr(module, class_name)(**data)
        obj.world_id = world_id
        return obj

    def get_state(self):
        pass

    def set_state(self, state, fluid=True):
        pass


class PhysicalObject (GameObject):
    body_class = BulletGhostNode

    def __init__(self, name=None):
        super().__init__(name=name)
        self.body = self.body_class('{}-Body'.format(self.name))
        self.body.set_into_collide_mask(Collision.GHOST)
        self.node = NodePath(self.body)

    def attached(self, world):
        world.physics.attach(self.body)
        self.node.reparent_to(world.node)

    def removed(self, world):
        world.physics.remove(self.body)
        self.node.remove_node()

    def hit(self, pos, distance):
        pass

    def get_state(self):
        return {
            'pos': self.node.get_pos(),
            'hpr': self.node.get_hpr(),
        }

    def set_state(self, state, fluid=True):
        if fluid:
            LerpPosHprInterval(self.node, 1.0 / 30.0, state['pos'], state['hpr']).start()
        else:
            self.node.set_pos(state['pos'])
            self.node.set_hpr(state['hpr'])


class SolidObject (PhysicalObject):
    body_class = BulletRigidBodyNode

    def __init__(self, mass=0, name=None):
        super().__init__(name=name)
        self.mass = float(mass)
        self.velocity = Vec3()
        self.body.set_mass(self.mass)
        self.body.set_into_collide_mask(Collision.SOLID)

    def serialize(self):
        data = super().serialize()
        data.update({
            'mass': self.mass,
        })
        return data

    def hit(self, pos, distance):
        power = (1.0 / (distance * distance)) * 20000.0
        impulse = (self.node.get_pos() - pos) * power
        self.body.set_active(True)
        self.body.apply_central_impulse(impulse)

    def update(self, world, dt):
        return self.body.is_active()


class Block (SolidObject):

    def __init__(self, center, size, color, mass=0, name=None):
        super().__init__(mass, name=name)
        self.center = center
        self.size = size
        self.color = color

    def serialize(self):
        data = super().serialize()
        data.update({
            'center': self.center,
            'size': self.size,
            'color': self.color,
        })
        return data

    def setup(self, world):
        self.body.add_shape(BulletBoxShape(Vec3(self.size.x / 2.0, self.size.y / 2.0, self.size.z / 2.0)))
        self.body.set_angular_damping(1.0)
        self.body.set_restitution(0.0)
        self.node.attach_new_node(GeomBuilder().add_block(self.color, (0, 0, 0), self.size).get_geom_node())
        self.node.set_pos(self.center)


class Ramp (SolidObject):

    def __init__(self, base, top, width, thickness, color, ypr, mass=0, name=None):
        super().__init__(name=name)
        self.base = base
        self.top = top
        self.width = width
        self.thickness = thickness
        self.color = color
        self.ypr = ypr
        self.midpoint = Point3((self.base + self.top) / 2.0)

    def serialize(self):
        data = super().serialize()
        data.update({
            'base': self.base,
            'top': self.top,
            'width': self.width,
            'thickness': self.thickness,
            'color': self.color,
            'ypr': self.ypr,
        })
        return data

    def setup(self, world):
        rel_base = Point3(self.base - (self.midpoint - Point3(0, 0, 0)))
        rel_top = Point3(self.top - (self.midpoint - Point3(0, 0, 0)))
        self.geom = GeomBuilder().add_ramp(self.color, rel_base, rel_top, self.width, self.thickness).get_geom_node()
        self.node.attach_new_node(self.geom)

        shape = BulletConvexHullShape()
        shape.add_geom(self.geom.get_geom(0))
        self.body.add_shape(shape)

        self.node.set_pos(self.midpoint)
        self.node.set_hpr(self.ypr)


class Ground (SolidObject):

    def setup(self, world):
        self.body.add_shape(BulletPlaneShape(Vec3(0, 0, 1), 0))
        self.body.set_restitution(0.0)
