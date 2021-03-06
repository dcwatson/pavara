from panda3d.core import BitMask32, LColor


DEFAULT_AMBIENT_COLOR = LColor(0.4, 0.4, 0.4, 1)
DEFAULT_GROUND_COLOR = LColor(0, 0, 0.15, 1)
DEFAULT_SKY_COLOR = LColor(0, 0, 0.15, 1)
DEFAULT_HORIZON_COLOR = LColor(0, 0, 0.8, 1)
DEFAULT_HORIZON_SCALE = 0.05


class Collision:
    NONE = BitMask32.all_off()
    SOLID = BitMask32.bit(0)
    GHOST = BitMask32.bit(1)
    PLAYER = BitMask32.bit(2)
    ALL = BitMask32.all_on()
