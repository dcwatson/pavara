#!/usr/bin/env python

from panda3d.core import loadPrcFile

from pavara.game import Game


loadPrcFile('pavara.prc')

game = Game()
game.load('maps/icebox-classic.xml')
game.run()
