from panda3d.core import BitMask32


DEFAULT_AMBIENT_COLOR = (0.4, 0.4, 0.4, 1)
DEFAULT_GROUND_COLOR = (0, 0, 0.15, 1)
DEFAULT_SKY_COLOR = (0, 0, 0.15, 1)
DEFAULT_HORIZON_COLOR = (0, 0, 0.8, 1)
DEFAULT_HORIZON_SCALE = 0.05


class Collision:
    NONE = BitMask32.all_off()
    MAP = BitMask32.bit(0)
    SOLID = BitMask32.bit(1)
    ALL = BitMask32.all_on()
