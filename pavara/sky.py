from panda3d.core import Shader

from .constants import DEFAULT_GROUND_COLOR, DEFAULT_HORIZON_COLOR, DEFAULT_HORIZON_SCALE, DEFAULT_SKY_COLOR

import math


class Sky:

    def __init__(self, camera, loader):
        self.node = loader.load_model('models/rect')
        self.node.set_hpr(0, math.pi, math.pi * 2.0)
        bounds = camera.node().get_lens().make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        y = dl.y * 0.99
        self.node.set_scale(abs(ur.x - dl.x), 1, abs(ur.z - dl.z))
        self.node.set_shader(Shader.load('shaders/sky.cg'))
        self.node.set_shader_input('camera', camera)
        self.node.set_shader_input('sky', self.node)
        self.node.set_shader_input('groundColor', *DEFAULT_GROUND_COLOR)
        self.node.set_shader_input('skyColor', *DEFAULT_SKY_COLOR)
        self.node.set_shader_input('horizonColor', *DEFAULT_HORIZON_COLOR)
        self.node.set_shader_input('gradientHeight', DEFAULT_HORIZON_SCALE, 0, 0, 0)
        self.node.reparent_to(camera)
        self.node.set_pos(camera, 0, y, 0)
