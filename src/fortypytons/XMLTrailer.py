# -*- coding: utf-8 -*-
'''
Created on 26.02.2012

@author: marcel
'''

import math
from Drivetrain import AutomaticDt
from VehicleDOMParser import *
from SoundController import SoundController
from VComponent import *
from panda3d.core import *
from panda3d.bullet import *

class XMLTrailer:
	def __init__(self, xmlfile, datadir, spawnpos, world):
		self.datadir = datadir
		self.world = world
		self.parser = VehicleDOMParser.createDOMParser(self.datadir + xmlfile)

		if self.parser == None:
			print "[ERR] XMLTrailer: The xml file seems to have an unknown vehicle type set."

		p = self.parser # Will get ugly otherwise...

		# ===== Chassis =====
		self.npBody = render.attachNewNode(BulletRigidBodyNode('truckBox'))
		npTruckMdl = self.npBody.attachNewNode(loader.loadModel(self.datadir + p.getMesh()).node())

		# Configure the collision shapes
		for shape in p.getColShapes():
			if shape["type"] == "box":
				size = Vec3(shape["width"]/2, shape["length"]/2, shape["height"]/2)
				self.npBody.node().addShape(BulletBoxShape(size), TransformState.makePos(shape["offset"]))
			else:
				print "[WRN] XMLTrailer: got a non-box collision shape, not supported yet."

		self.npBody.node().setMass(p.getWeight())
		self.npBody.node().setDeactivationEnabled(False)
		self.npBody.setPos(spawnpos + p.getSpawnheight())
		self.world.attachRigidBody(self.npBody.node())
		self.chassis = VComponent(npTruckMdl, self.npBody)

        # ===== BulletVehicle setup =====
		self.vehicle = BulletVehicle(self.world, self.npBody.node())
		self.vehicle.setCoordinateSystem(ZUp)
		self.world.attachVehicle(self.vehicle)

		# ===== Dumper =====

		# ===== Wheels =====
		self.wheels = []

		for axIndex in range(0, p.getAxleCount()):
			axPos = p.getAxlePosition(axIndex)
			axWidth = p.getAxleWidth(axIndex)
			rideHeight = p.getRideheight()

			for wheelIndex in range(0, 2):
				# Wheel 0 is left, 1 is the right one
				# Prepare the wheel's position vector
				pos = Point3(axWidth/2., axPos, rideHeight)

				# Prepare the wheel's bullet node
				npWheel = render.attachNewNode(BulletRigidBodyNode('wheelBox'))
				npWheel.node().setMass(p.getWheelWeight())
				npWheel.setPos(pos)
				self.world.attachRigidBody(npWheel.node())

				# Load the wheel mesh
				npWheelMdl = npWheel.attachNewNode(loader.loadModel(self.datadir + p.getWheelMesh()).node())
				if wheelIndex == 0:
					# We need to turn around the mesh of the left wheel
					npWheelMdl.setH(180.0)
					# And invert it's x position (from right to left side)
					pos[0] *= -1.

				# Add the wheel to the BulletVehicle
				wheel = self.vehicle.createWheel()
				wheel.setNode(npWheel.node())
				wheel.setChassisConnectionPointCs(pos)

				wheel.setWheelDirectionCs(Vec3(0, 0, -1))
				wheel.setWheelAxleCs(Vec3(1, 0, 0))
				wheel.setWheelRadius(p.getWheelRadius())

				# suspension setup
				wheel.setFrontWheel(p.isAxleSteerable(axIndex))
				wheel.setMaxSuspensionTravelCm(p.getAxleSuspMaxTravel(axIndex))
				wheel.setMaxSuspensionForce(p.getAxleSuspMaxForce(axIndex))
				wheel.setSuspensionStiffness(p.getAxleSuspStiffness(axIndex))
				wheel.setWheelsDampingRelaxation(p.getAxleSuspDampingRelax(axIndex))
				wheel.setWheelsDampingCompression(p.getAxleSuspDampingComp(axIndex))
				wheel.setFrictionSlip(p.getAxleSuspFrictionSlip(axIndex))
				wheel.setRollInfluence(p.getAxleSuspRollInfluence(axIndex))

				self.wheels.append(VWheel(npWheelMdl, npWheel, wheel, False))

	def update(self, dt):
		self._steer()

	def setBrake(self, brake):
		if brake <= 1. and brake >= 0.:
			self.drivetrain.setBrake(brake)
		else:
			print "XMLTrailer:setBrake(brake) out of range! (0 < x < 1)"

	def steer(self, direction):
		if direction in [-1, 0, 1]:
			self._steerDir = direction
		else:
			print "[WRN] XMLTrailer:steer(): Invalid direction parameter."

	def _steer(self):
		# We are speed sensitive
		speed = self.vehicle.getCurrentSpeedKmHour()
		if speed > 0 and speed < 90:
			self.maxAngle = (-.5) * speed + 45 # Graph this on WolframAlpha to make it obvious :)
		elif speed > 90:
			self.maxAngle = 1.0

		if self._steerDir == 1 and self.curAngle < self.maxAngle:
			if self.curAngle < 0:
				self.curAngle += 2.0 * self.rate
			else:
				self.curAngle += self.rate
		elif self._steerDir == -1 and self.curAngle > self.maxAngle * -1:
			if self.curAngle > 0:
				self.curAngle -= 2.0 * self.rate
			else:
				self.curAngle -= self.rate
		else: # self._steerDir == 0
			# steer straight
			if self.curAngle > self.rate:
				self.curAngle -= 2.0 * self.rate
			elif self.curAngle < self.rate * -1.0:
				self.curAngle += 2.0 * self.rate
			else:
				self.curAngle = 0.0

		self.vehicle.setSteeringValue(self.curAngle, 0)
		self.vehicle.setSteeringValue(self.curAngle, 1)

	def reset(self):
		self.chassis.setPos(self.chassis.getPos() + (0,0,1.5))
		self.chassis.setR(0)

	def tiltDumper(self, direction):
		if direction in [-1., 1.]:
			self.dumperCon.enableAngularMotor(True, .4 * direction, 10000000.)
		elif direction == 0.:
			self.dumperCon.enableAngularMotor(True, .0, 1000000.)
		else:
			print "[WRN] Truck.py:tiltDumper(direction): Direction is none of [1., 0., -1.]"

	def getChassisNp(self):
		return self.chassis.getNp()
	def getChassis(self):
		return self.chassis
	def getSpeed(self):
		return self.vehicle.getCurrentSpeedKmHour()
	def getTrailerHitchPoint(self):
		return self.parser.getTrailerHitchPoint()
