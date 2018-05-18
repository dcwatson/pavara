from panda3d.bullet import BulletSphereShape

from .objects import SolidObject


class Grenade (SolidObject):

    def __init__(self, mass=5.0, name=None):
        super().__init__(mass=mass, name=name)

    def setup(self, world):
        self.body.add_shape(BulletSphereShape(0.5))
        model = world.load_model('models/grenade')
        if model:
            model.set_color(1, 1, 0, 1)
            model.reparent_to(self.node)
