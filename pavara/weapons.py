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

    def update(self, world, dt):
        result = world.physics.contact_test(self.body)
        if result.get_num_contacts() > 0:
            nade_pos = self.node.get_pos()
            for obj, distance in world.find(nade_pos, 10.0):
                if not isinstance(obj, Grenade):
                    obj.hit(nade_pos, distance)
            world.remove(self)
            return False
        return self.body.is_active()
