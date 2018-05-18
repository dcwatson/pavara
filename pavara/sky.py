from panda3d.core import Shader

from .constants import DEFAULT_GROUND_COLOR, DEFAULT_HORIZON_COLOR, DEFAULT_HORIZON_SCALE, DEFAULT_SKY_COLOR
from .geom import GeomBuilder
from .objects import GameObject


class Sky (GameObject):

    def __init__(self, color=None, horizon=None, ground=None, gradient=None, name=None):
        super().__init__(name=name)
        self.node = None
        self.color = color or DEFAULT_SKY_COLOR
        self.horizon = horizon or DEFAULT_HORIZON_COLOR
        self.ground = ground or DEFAULT_GROUND_COLOR
        self.gradient = gradient or DEFAULT_HORIZON_SCALE

    def serialize(self):
        data = super().serialize()
        data.update({
            'color': self.color,
            'horizon': self.horizon,
            'ground': self.ground,
            'gradient': self.gradient,
        })
        return data

    def attached(self, world):
        if not world.camera:
            return
        bounds = world.camera.node().get_lens().make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        self.node = world.camera.attach_new_node(GeomBuilder('sky').add_rect((1, 1, 1, 1), dl.x, 0, dl.z, ur.x, 0, ur.z).get_geom_node())
        self.node.set_shader(Shader.load('shaders/sky.cg', Shader.SL_Cg))
        self.node.set_shader_input('sky', self.node)
        self.node.set_shader_input('groundColor', self.ground)
        self.node.set_shader_input('skyColor', self.color)
        self.node.set_shader_input('horizonColor', self.horizon)
        self.node.set_shader_input('gradientHeight', self.gradient, 0, 0, 0)
        self.node.set_pos(world.camera, 0, 9999, 0)

    def set_sky_color(self, color):
        self.color = color
        if self.node:
            self.node.set_shader_input('skyColor', self.color)

    def set_horizon_color(self, color):
        self.horizon = color
        if self.node:
            self.node.set_shader_input('horizonColor', self.horizon)

    def set_ground_color(self, color):
        self.ground = color
        if self.node:
            self.node.set_shader_input('groundColor', self.ground)
