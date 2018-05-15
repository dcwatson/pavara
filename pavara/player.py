from panda3d.bullet import BulletBoxShape
from panda3d.core import BitMask32, KeyboardButton, TransformState, Vec3

from .objects import SolidObject


forward_button = KeyboardButton.ascii_key(b'w')
backward_button = KeyboardButton.ascii_key(b's')
left_button = KeyboardButton.ascii_key(b'a')
right_button = KeyboardButton.ascii_key(b'd')
jump_button = KeyboardButton.ascii_key(b' ')


class Player (SolidObject):

    def __init__(self, pid, mass=None, name=None, protocol=None):
        super().__init__(name=name, mass=150.0)
        self.pid = pid
        self.protocol = protocol
        # self.body.set_kinematic(True)
        self.camera_pos = Vec3(0, 0, 1.25)

    def setup(self, world):
        self.body.add_shape(BulletBoxShape(Vec3(0.5, 0.5, 0.5)))
        head = world.load_model('models/head')
        if head:
            head.set_color(1, 1, 1, 1)
            head.set_scale(2.0)
            head.set_h(180)
            head.reparent_to(self.node)
        return self.node

    def update(self, world, dt):
        return True

    def attached(self, world):
        super().attached(world)

    def removed(self, world):
        super().removed(world)

    def serialize(self):
        data = super().serialize()
        data.update({
            'pid': self.pid,
        })
        return data

    def send(self, cmd, **args):
        self.protocol.send(cmd, **args)

    def _update(self, world, dt):
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
