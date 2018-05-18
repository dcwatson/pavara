from panda3d.bullet import BulletBoxShape
from panda3d.core import Vec3

from .constants import Collision
from .objects import PhysicalObject

import math


class Player (PhysicalObject):
    TURN_ACCEL = 0.1  # seconds to reach TURN_SPEED
    TURN_SPEED = 75.0  # deg/sec
    TURN_DAMPER = 0.5  # The fraction of motor power to reduce turn power by while moving
    WALK_ACCEL = 0.25  # seconds to reach WALK_SPEED
    WALK_SPEED = 12.0  # m/sec
    MAX_SWIVEL = 60.0  # Maximum head swivel (side-to-side) in degrees
    MAX_PITCH = 20.0  # Maximum head pitch (up-and-down) in degrees

    def __init__(self, pid, name=None, protocol=None):
        super().__init__(name=name)
        self.pid = pid
        self.world_id = pid
        self.protocol = protocol
        self.velocity = Vec3(0, 0, 0)
        self.resting = False
        self.body.set_into_collide_mask(Collision.PLAYER)
        self.floater = self.node.attach_new_node('floater')
        self.floater.set_pos(0, 1, 1.75)
        self.motion = {
            'forward': False,
            'backward': False,
            'left': False,
            'right': False,
        }
        self.turn_power = 0.0
        self.motor_power = 0.0
        self.head_swivel = 0.0
        self.head_pitch = 0.0
        self.mouse_dirty = False

    def update_camera(self, world, camera):
        pos = self.node.get_pos() + Vec3(0, 0, 1.75)
        camera.set_pos(pos)
        camera.look_at(self.floater.get_pos(world.node))

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

    def get_state(self):
        state = super().get_state()
        state.update({
            'head_swivel': self.head_swivel,
            'head_pitch': self.head_pitch,
        })
        return state

    def set_state(self, state, fluid=True):
        super().set_state(state, fluid=fluid)
        self.head_swivel = state['head_swivel']
        self.head_pitch = state['head_pitch']
        self.floater.set_pos(0, 0, 1.75)
        self.floater.set_h(self.head_swivel * -self.MAX_SWIVEL)
        self.floater.set_p(self.head_pitch * self.MAX_PITCH)
        self.floater.set_y(self.floater, 2.0)

    def send(self, cmd, **args):
        self.protocol.send(cmd, **args)

    def input(self, cmd, pressed):
        if cmd in self.motion:
            self.motion[cmd] = pressed
        if cmd == 'center' and pressed:
            self.head_swivel = 0.0
            self.head_pitch = 0.0
            self.mouse_dirty = True

    def mouse(self, x, y):
        self.head_swivel = max(min(self.head_swivel + x, 1.0), -1.0)
        self.head_pitch = max(min(self.head_pitch + y, 1.0), -1.0)
        self.mouse_dirty = True
        self.floater.set_pos(0, 0, 1.75)
        self.floater.set_h(self.head_swivel * -self.MAX_SWIVEL)
        self.floater.set_p(self.head_pitch * self.MAX_PITCH)
        self.floater.set_y(self.floater, 2.0)

    def update(self, world, dt):
        dirty = self.mouse_dirty
        old_pos = self.node.get_pos()
        h = self.node.get_h()
        new_velocity = self.velocity + (world.gravity * dt)

        if self.resting:
            if not (self.motion['forward'] ^ self.motion['backward']):
                self.motor_power /= 1.5
                if abs(self.motor_power) < 0.05:
                    self.motor_power = 0.0
            elif self.motion['forward']:
                self.motor_power = min(max(self.motor_power, 0) + (dt / self.WALK_ACCEL), 1.0)
            elif self.motion['backward']:
                self.motor_power = max(min(self.motor_power, 0) - (dt / self.WALK_ACCEL), -1.0)
        else:
            self.motor_power /= 1.5
            if abs(self.motor_power) < 0.05:
                self.motor_power = 0.0

        if not (self.motion['left'] ^ self.motion['right']):
            self.turn_power /= 1.25
            if abs(self.turn_power) < 0.05:
                self.turn_power = 0.0
        elif self.motion['left']:
            self.turn_power = min(max(self.turn_power, 0) + (dt / self.TURN_ACCEL), 1.0)
        elif self.motion['right']:
            self.turn_power = max(min(self.turn_power, 0) - (dt / self.TURN_ACCEL), -1.0)

        # Dampen the turn motor while walking.
        self.turn_power /= ((abs(self.motor_power) * self.TURN_DAMPER) + 1.0)

        if (abs(self.turn_power) + abs(self.motor_power)) > 0:
            dirty = True
        h += self.TURN_SPEED * dt * self.turn_power
        self.node.set_h(h)

        if self.motor_power != 0:
            # Panda's heading starts along the Y axis, so we need to rotate 90 degrees to start along X.
            x = math.cos(math.radians(h + 90)) * self.WALK_SPEED * self.motor_power
            y = math.sin(math.radians(h + 90)) * self.WALK_SPEED * self.motor_power
            new_velocity.set_x(x)
            new_velocity.set_y(y)
        else:
            new_velocity.set_x(0)
            new_velocity.set_y(0)

        new_pos = old_pos + (new_velocity * dt)
        self.node.set_pos(new_pos)

        result = world.physics.contact_test(self.body)
        for contact in result.get_contacts():
            m = contact.manifold_point
            normal = m.normal_world_on_b
            new_velocity = new_velocity - (normal * new_velocity.dot(normal))

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
        self.velocity = new_velocity
        self.mouse_dirty = False
        if old_pos != new_pos:
            dirty = True

        return dirty
