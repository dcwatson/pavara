from panda3d.bullet import BulletBoxShape
from panda3d.core import Vec3

from .constants import Collision
from .objects import PhysicalObject

import math


class Player (PhysicalObject):
    TURN_SPEED = 360.0  # deg/sec
    WALK_SPEED = 6.0  # m/sec

    def __init__(self, pid, name=None, protocol=None):
        super().__init__(name=name)
        self.pid = pid
        self.protocol = protocol
        self.camera_pos = Vec3(0, 0, 1.25)
        self.velocity = Vec3(0, 0, 0)
        self.resting = False
        self.body.set_into_collide_mask(Collision.PLAYER)
        self.motion = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False,
        }

    def setup(self, world):
        self.body.add_shape(BulletBoxShape(Vec3(0.5, 0.5, 0.5)))
        head = world.load_model('models/head')
        if head:
            head.set_color(1, 0, 0, 1)
            head.set_scale(2.0)
            head.set_h(180)
            head.reparent_to(self.node)

    def serialize(self):
        data = super().serialize()
        data.update({
            'pid': self.pid,
        })
        return data

    def send(self, cmd, **args):
        self.protocol.send(cmd, **args)

    def input(self, cmd, pressed):
        if cmd in self.motion:
            self.motion[cmd] = pressed

    def update(self, world, dt):
        dirty = False
        old_pos = self.node.get_pos()
        h = self.node.get_h()
        new_velocity = self.velocity + (world.gravity * dt)

        if self.motion['left']:
            dirty = True
            h += self.TURN_SPEED * dt
        if self.motion['right']:
            dirty = True
            h -= self.TURN_SPEED * dt
        self.node.set_h(h)

        if self.resting:
            walk_dir = 0.0
            if self.motion['forward']:
                walk_dir += 1.0
            if self.motion['backward']:
                walk_dir -= 1.0
            if walk_dir != 0:
                # TODO: figure out this 90 degree difference
                x = math.cos(math.radians(h + 90)) * self.WALK_SPEED * walk_dir
                y = math.sin(math.radians(h + 90)) * self.WALK_SPEED * walk_dir
                new_velocity.set_x(x)
                new_velocity.set_y(y)
            else:
                new_velocity.set_x(0)
                new_velocity.set_y(0)

        new_pos = old_pos + (new_velocity * dt)

        end = new_pos + Vec3(0, 0, -0.7)
        result = world.physics.ray_test_closest(new_pos, end, Collision.SOLID)
        if result.has_hit():
            self.resting = True
            new_velocity.set_z(0)
            new_pos.set_z(result.hit_pos.z + 0.52)
        else:
            self.resting = False

        self.node.set_pos(new_pos)

        result = world.physics.contact_test(self.body)
        for contact in result.get_contacts():
            m = contact.manifold_point
            normal = m.normal_world_on_b
            new_velocity = new_velocity - (normal * new_velocity.dot(normal))

        new_pos = old_pos + (new_velocity * dt)
        self.node.set_pos(new_pos)
        self.velocity = new_velocity
        if old_pos != new_pos:
            dirty = True
        return dirty
