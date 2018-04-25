from panda3d.core import NodePath, CollisionBox, CollisionNode, CollisionPlane, Plane, Vec3, Point3, KeyboardButton, TransformState, BitMask32
from panda3d.bullet import BulletConvexHullShape

from .objects import PhysicalObject

import math


forward_button = KeyboardButton.ascii_key(b'w')
backward_button = KeyboardButton.ascii_key(b's')
left_button = KeyboardButton.ascii_key(b'a')
right_button = KeyboardButton.ascii_key(b'd')
jump_button = KeyboardButton.ascii_key(b' ')


class Player (PhysicalObject):

    def __init__(self):
        super().__init__()
        self.body.set_kinematic(True)
        self.foot_offset = Vec3()

    def setup(self, world):
        head = world.load_model('models/head')
        head.set_h(180)
        head.reparent_to(self.node)

        geom = head.find_all_matches('**/+GeomNode').get_path(0).node().get_geom(0)
        shape = BulletConvexHullShape()
        shape.add_geom(geom)
        self.body.add_shape(shape)

        self.node.set_color(1, 1, 1, 1)
        self.node.set_pos(0, 0, 15)
        self.node.set_scale(2.0)
        lower, upper = self.node.get_tight_bounds()
        self.foot_offset = Vec3(0, 0, lower.z)
        return self.node

    def update(self, world, dt):
        old_pos = self.node.get_pos()
        foot = old_pos + self.foot_offset
        end = foot + Vec3(0, 0, -0.2)
        result = world.physics.ray_test_closest(foot, end)
        if result.has_hit():
            self.on_ground = True
            new_pos = old_pos
        else:
            new_pos = old_pos + (world.gravity * dt)

        goal = new_pos + Vec3(0.2, 0.2, 0)
        ts_from = TransformState.make_pos(old_pos)
        ts_to = TransformState.make_pos(goal)
        result = world.physics.sweep_test_closest(self.body.get_shape(0), ts_from, ts_to, BitMask32.all_on(), 0.0)
        if result.has_hit():
            node = result.get_node()
            if node != self.body:
                print(result)

        new_pos = goal
        if new_pos != old_pos:
            self.node.set_pos(new_pos)
