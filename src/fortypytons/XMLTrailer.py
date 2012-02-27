# -*- coding: utf-8 -*-
'''
Created on 26.02.2012

@author: marcel
'''

import math
from panda3d.core import *
from Drivetrain import AutomaticDt
from XMLVehicle import XMLVehicle
from VComponent import *

class XMLTrailer(XMLVehicle):
	def update(self, dt, truckSteerDir):
		""" Called by the hitched truck. """
		self._steer(truckSteerDir)

	def _steer(self, direction):
		if direction > -90 and direction < 90:
			for axle in range(0, self.parser.getAxleCount()):
				if self.parser.isAxleSteerable(axle):
					self.vehicle.setSteeringValue(direction * self.parser.getAxleSteeringFactor(axle), 2 * axle)
					self.vehicle.setSteeringValue(direction * self.parser.getAxleSteeringFactor(axle), 2 * axle + 1)
		else:
			print "[WRN] XMLTrailer:steer(): Invalid direction parameter:", direction

	def reset(self):
		self.chassis.setPos(self.chassis.getPos() + (0,0,1.5))
		self.chassis.setR(0)
