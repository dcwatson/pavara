from panda3d.core import LColor, Vec3
import drill

from .constants import DEFAULT_GROUND_COLOR, DEFAULT_HORIZON_COLOR, DEFAULT_SKY_COLOR
from .objects import Block, Ground, Ramp
from .sky import Sky


class Map:

    def __init__(self, **attrs):
        self.name = attrs.get('name', '')
        self.tagline = attrs.get('tagline', '')
        self.description = attrs.get('description', '')
        self.coords = attrs.get('coords', 'z-up').lower()

    def parse_vector(self, s, default=None, spatial=True):
        if s is None or not s.strip():
            return default or Vec3(0, 0, 0)
        parts = tuple(float(v.strip()) for v in s.split(','))
        if len(parts) != 3:
            raise ValueError('Expected 3 dimensions in "{}"'.format(s))
        if self.coords == 'z-up':
            return Vec3(*parts)
        elif self.coords == 'y-up':
            if spatial:
                return Vec3(parts[0], -parts[2], parts[1])
            else:
                return Vec3(parts[0], parts[2], parts[1])
        else:
            raise ValueError('Unknown coordinate system: "{}"'.format(self.coords))

    def parse_color(self, s, default=None):
        if s is None or not s.strip():
            return default or LColor(1, 1, 1, 1)
        color = tuple(float(v.strip()) for v in s.split(','))
        if len(color) == 3:
            return LColor(color[0], color[1], color[2], 1)
        elif len(color) == 4:
            return LColor(*color)
        else:
            raise ValueError('Invalid color specification: "{}"'.format(s))

    def parse_float(self, s, default=0.0):
        if s is None or not s.strip():
            return float(default) if isinstance(default, str) else default
        return float(s)

    def load(self, root, world, **context):
        sky = None
        for xml in root:
            if xml.tagname == 'block':
                world.attach(Block(
                    self.parse_vector(xml['center']),
                    self.parse_vector(xml['size'], spatial=False),
                    self.parse_color(xml['color']),
                    self.parse_float(xml.attrs.get('mass'), default=context.get('mass', 0)),
                ))
            elif xml.tagname == 'ramp':
                world.attach(Ramp(
                    self.parse_vector(xml['base']),
                    self.parse_vector(xml['top']),
                    self.parse_float(xml.attrs.get('width'), 8),
                    self.parse_float(xml.attrs.get('thickness')),
                    self.parse_color(xml.attrs.get('color')),
                    Vec3(
                        self.parse_float(xml.attrs.get('yaw')),
                        self.parse_float(xml.attrs.get('pitch')),
                        self.parse_float(xml.attrs.get('roll'))
                    )
                ))
            elif xml.tagname == 'ground':
                if sky:
                    sky.set_ground_color(self.parse_color(xml.attrs.get('color'), DEFAULT_GROUND_COLOR))
                world.attach(Ground())
            elif xml.tagname == 'sky':
                sky = world.attach(Sky(
                    self.parse_color(xml.attrs.get('color'), DEFAULT_SKY_COLOR),
                    self.parse_color(xml.attrs.get('horizon'), DEFAULT_HORIZON_COLOR),
                ))
            elif xml.tagname == 'incarnator':
                world.add_incarnator(
                    self.parse_vector(xml['location']),
                    self.parse_float(xml['heading']),
                )
            elif xml.tagname == 'set':
                context.update(xml.attrs)
                self.load(xml, world, **context)


def load_map(filename, world=None):
    root = drill.parse(filename)
    if root.tagname.lower() != 'map':
        raise Exception('Expected "map" root element.')
    m = Map(**root.attrs)
    if world:
        m.load(root, world)
    return m
