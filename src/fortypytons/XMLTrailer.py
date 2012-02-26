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

	def update(self, dt, truckSteerDir):
		self._steer(truckSteerDir)

	def setBrake(self, brake):
		if brake <= 1. and brake >= 0.:
			self.drivetrain.setBrake(brake)
		else:
			print "XMLTrailer:setBrake(brake) out of range! (0 < x < 1)"

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

	def tiltDumper(self, direction):
		if direction >= -1 and direction <= 1:
			self.dumperCon.enableAngularMotor(True, .4 * direction, 10000000.)
		elif direction == 0:
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
	def getType(self):
		return self.parser.getType()
