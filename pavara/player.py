from panda3d.core import NodePath, CollisionBox, CollisionNode, CollisionPlane, Plane, Vec3, Point3, KeyboardButton
from panda3d.physics import LinearVectorForce, ForceNode

from .objects import PhysicalObject

import math


forward_button = KeyboardButton.ascii_key(b'w')
backward_button = KeyboardButton.ascii_key(b's')
left_button = KeyboardButton.ascii_key(b'a')
right_button = KeyboardButton.ascii_key(b'd')
jump_button = KeyboardButton.ascii_key(b' ')


class Player (PhysicalObject):

    def __init__(self):
        super().__init__(mass=100)
        self.moving = False
        self.jumping = False

    def setup(self, loader):
        head = loader.load_model('models/head')
        head.set_h(180)
        head.reparent_to(self.actor_node)

        self.collision_node.node().add_solid(CollisionBox(Point3(0, 0, 0), 0.5, 0.5, 0.5))

        self.collision_handler.setDynamicFrictionCoef(1.0)
        self.collision_handler.setStaticFrictionCoef(1.0)

        self.force = LinearVectorForce(0, 2000.0, 0)
        self.force.set_mass_dependent(True)
        self.thruster = ForceNode('thruster')
        self.thruster.add_force(self.force)
        self.actor_node.attach_new_node(self.thruster)

        self.jump_force = LinearVectorForce(0, 0, 10000.0)
        self.jump_force.set_mass_dependent(True)
        self.jumper = ForceNode('jumper')
        self.jumper.add_force(self.jump_force)
        self.actor_node.attach_new_node(self.jumper)

        self.actor_node.set_pos(0, 0, 10)

    def tick(self, watcher):
        phys = self.actor.getPhysical(0)
        if watcher.is_button_down(forward_button):
            if not self.moving:
                phys.add_linear_force(self.force)
                self.moving = True
        elif self.moving:
            phys.remove_linear_force(self.force)
            self.moving = False

        if watcher.is_button_down(jump_button):
            if not self.jumping:
                phys.add_linear_force(self.jump_force)
                self.jumping = True
        else:
            phys.remove_linear_force(self.jump_force)

        if watcher.is_button_down(left_button):
            self.actor_node.set_hpr(self.actor_node, 0.6, 0, 0)

        if watcher.is_button_down(right_button):
            self.actor_node.set_hpr(self.actor_node, -0.6, 0, 0)
