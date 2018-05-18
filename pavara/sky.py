from panda3d.core import NodePath, Shader

from .constants import DEFAULT_GROUND_COLOR, DEFAULT_HORIZON_COLOR, DEFAULT_HORIZON_SCALE, DEFAULT_SKY_COLOR
from .geom import GeomBuilder


class Sky:

    def __init__(self, camera):
        self.node = self.make_node(camera) if camera else NodePath('sky')
        if camera:
            self.node.reparent_to(camera)
            self.node.set_pos(camera, 0, 9999, 0)

    def make_node(self, camera):
        bounds = camera.node().get_lens().make_bounds()
        dl = bounds.getMin()
        ur = bounds.getMax()
        node = NodePath(GeomBuilder('sky').add_rect((1, 1, 1, 1), dl.x, 0, dl.z, ur.x, 0, ur.z).get_geom_node())
        node.set_shader(Shader.load('shaders/sky.cg', Shader.SL_Cg))
        node.set_shader_input('sky', node)
        node.set_shader_input('groundColor', DEFAULT_GROUND_COLOR)
        node.set_shader_input('skyColor', DEFAULT_SKY_COLOR)
        node.set_shader_input('horizonColor', DEFAULT_HORIZON_COLOR)
        node.set_shader_input('gradientHeight', DEFAULT_HORIZON_SCALE, 0, 0, 0)
        return node
