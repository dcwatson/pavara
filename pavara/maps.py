from panda3d.core import NodePath, LVecBase3f, LColor
from panda3d.physics import ForceNode, LinearVectorForce

from .objects import Block, Ground

import drill


class Map:

    def __init__(self, root, loader):
        self.coords = root.attrs.get('coords', 'z-up').lower()
        self.gravity = LinearVectorForce(self.parse_vector(root.attrs.get('gravity'), default=LVecBase3f(0, 0, -9.81)))
        self.node = NodePath('map')
        self.objects = []
        self.loader = loader
        for xml in root:
            func = getattr(self, 'handle_{}'.format(xml.tagname), None)
            if func is not None:
                func(xml)

    def parse_vector(self, s, default=None):
        if s is None or not s.strip():
            return default or (0, 0, 0)
        parts = tuple(float(v.strip()) for v in s.split(','))
        if len(parts) != 3:
            raise ValueError('Expected 3 dimensions in "{}"'.format(s))
        if self.coords == 'z-up':
            return LVecBase3f(*parts)
        elif self.coords == 'y-up':
            return LVecBase3f(parts[0], parts[2], parts[1])
        else:
            raise ValueError('Unknown coordinate system: "{}"'.format(self.coords))

    def parse_color(self, s, default=None):
        if s is None or not s.strip():
            return default or (1, 1, 1, 1)
        color = tuple(float(v.strip()) for v in s.split(','))
        if len(color) == 3:
            return LColor(color[0], color[1], color[2], 1)
        elif len(color) == 4:
            return LColor(*color)
        else:
            raise ValueError('Invalid color specification: "{}"'.format(s))

    def handle_block(self, xml):
        size = self.parse_vector(xml['size'])
        center = self.parse_vector(xml['center'])
        color = self.parse_color(xml['color'])
        mass = float(xml.attrs.get('mass', 0))
        self.objects.append(Block(center, size, color, mass))

    def handle_ground(self, xml):
        self.objects.append(Ground())


def load_maps(filename, loader):
    root = drill.parse(filename)
    if root.tagname.lower() == 'map':
        return [Map(root, loader)]
    else:
        return [Map(e, loader) for e in root.find('map')]
