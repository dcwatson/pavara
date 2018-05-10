from direct.interval.LerpInterval import LerpPosHprInterval
from panda3d.bullet import BulletBoxShape, BulletGhostNode, BulletPlaneShape, BulletRigidBodyNode
from panda3d.core import NodePath, Vec3


class GameObject:
    world_id = None
    dirty = False

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

    def get_state(self):
        pass

    def set_state(self, state, fluid=True):
        pass


class PhysicalObject (GameObject):
    body_class = BulletGhostNode

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

    def get_state(self):
        pos = self.node.get_pos()
        hpr = self.node.get_hpr()
        return {
            'pos': (pos.x, pos.y, pos.z),
            'hpr': (hpr.x, hpr.y, hpr.z),
        }

    def set_state(self, state, fluid=True):
        if fluid:
            LerpPosHprInterval(self.node, 1.0 / 30.0, state['pos'], state['hpr']).start()
        else:
            self.node.set_pos_hpr(*state['pos'], *state['hpr'])


class SolidObject (PhysicalObject):
    body_class = BulletRigidBodyNode

    def __init__(self, mass=0, name=None):
        super().__init__(name=name)
        self.mass = float(mass)
        self.velocity = Vec3()
        self.body.set_mass(self.mass)

    def _update(self, world, dt):
        if self.mass == 0:
            return

        self.velocity += (world.gravity * dt)

        old_pos = self.node.get_pos()
        new_pos = old_pos + (self.velocity * dt)

        self.node.set_pos(new_pos)
        result = world.physics.contact_test(self.body)
        if result.get_num_contacts() > 0:
            best_normal = Vec3()
            best_dot = 100000.0
            for contact in result.get_contacts():
                m = contact.manifold_point
                normal = m.normal_world_on_b
                d = self.velocity.dot(normal)

                # Move the object out of each collision.
                move = normal * self.velocity.dot(normal)
                move.normalize()
                self.node.set_pos(self.node, move * m.distance)

                if abs(d) < best_dot:
                    best_dot = abs(d)
                    best_normal = normal
            self.velocity = self.velocity - (best_normal * self.velocity.dot(best_normal))

        if old_pos != self.node.get_pos():
            self.dirty = True


class Block (SolidObject):

    def __init__(self, center, size, color, mass=0, name=None):
        super().__init__(mass, name=name)
        self.center = center
        self.size = size
        self.color = color

    def setup(self, world):
        self.body.add_shape(BulletBoxShape(Vec3(self.size.x / 2.0, self.size.y / 2.0, self.size.z / 2.0)))
        self.body.set_angular_damping(1.0)
        self.body.set_restitution(0.0)
        block = world.load_model('models/block')
        if block:
            block.set_scale(self.size)
            block.set_color(self.color)
            block.reparent_to(self.node)
        self.node.set_pos(self.center)
        return self.node


class Ground (SolidObject):

    def setup(self, world):
        self.body.add_shape(BulletPlaneShape(Vec3(0, 0, 1), 0))
        self.body.set_restitution(0.0)
        return self.node
