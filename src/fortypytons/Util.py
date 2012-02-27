# -*- coding: utf-8 -*-

'''
Created on 26.02.2012

@author: marcel
'''

import math
from panda3d.bullet import BulletGhostNode

class Util:
	@staticmethod
	def getAbsolutePos(relPos, node):
		""" Calculates the position of relPos (which is relative to node) relative to render (the origin). """
		dummy = render.attachNewNode(BulletGhostNode())
		dummy.setPos(node, relPos)
		absPos = dummy.getPos()
		return absPos

	@staticmethod
	def getDistance(first, second):
		""" Calculates the distance between two Vec3 instances. """
		# The sqrt of the sum ((Pi - Qi)^2)
		return math.sqrt((first[0]-second[0])**2 + (first[1]-second[1])**2 + (first[2]-second[2])**2)
