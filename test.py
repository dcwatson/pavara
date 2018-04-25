#!/usr/bin/env python

from pavara.game import Game
from panda3d.core import loadPrcFile

loadPrcFile('pavara.prc')

game = Game()
game.load_map('maps/icebox-classic.xml')
game.run()
