# -*- coding: utf-8 -*-
'''
Created on 16.10.2011

@author: marcel
'''

import math
from Drivetrain import AutomaticDt
from VehicleDOMParser import VehicleDOMParser
from VComponent import *
from panda3d.core import *
from panda3d.bullet import *

class XMLTruck:
	def __init__(self, xmlfile, datadir, spawnpos, world):
		self.datadir = datadir
		self.world = world
		self.parser = VehicleDOMParser(self.datadir + xmlfile)
		p = self.parser # Will get ugly otherwise...

		# ===== Steering =====
		self.physMaxAngle = p.get(["steering", "maxAngle"])	# The absolute maximum angle possible
		self.maxAngle = self.physMaxAngle 					# The maximum steering angle at the current speed (speed-sensitive)
		self.rate = p.get(["steering", "rate"])
		self.curAngle = 0.0
		self._steerDir = 0	# -1, 0, 1: Sets the direction of steering

		# ===== Chassis =====
		npBody = render.attachNewNode(BulletRigidBodyNode('truckBox'))
		npTruckMdl = npBody.attachNewNode(loader.loadModel(self.datadir + p.get("mesh")).node())

		# Configure the collision shapes
		for index in p.get(["colShapes"]).keys():
			if p.get(["colShapes", index, "type"]) == "box":
				offset = p.get(["colShapes", index, "offset"])
				size = Vec3(p.get(["colShapes", index, "width"])/2,
							p.get(["colShapes", index, "length"])/2,
							p.get(["colShapes", index, "height"])/2)
				npBody.node().addShape(BulletBoxShape(size), TransformState.makePos(offset))

		npBody.node().setMass(p.get(["weight"]))
		npBody.node().setDeactivationEnabled(False)
		npBody.setPos(spawnpos + p.get(["spawnheight"]))
		self.world.attachRigidBody(npBody.node())
		self.chassis = VComponent(npTruckMdl, npBody)

        # ===== BulletVehicle setup =====
		self.vehicle = BulletVehicle(self.world, npBody.node())
		self.vehicle.setCoordinateSystem(ZUp)
		self.world.attachVehicle(self.vehicle)

		# ===== Select a drivetrain =====
		if p.get(["drivetrain", "type"]) == "automatic":
			self.drivetrain = AutomaticDt(self.vehicle, self.parser)
		else:
			print "[WRN] The selected drivetrain type is unknown, choosing automatic!"

		# ===== Dumper =====

		# ===== Wheels =====
		self.wheels = []

		# Find out how many axles we have
		axCount = len(p.get(["axles"]).keys())

		for axIndex in range(0, axCount):
			axPos = p.get(["axles", axIndex, "position"])
			axWidth = p.get(["axles", axIndex, "width"])
			rideHeight = p.get(["rideheight"])
			isPowered = p.get(["axles", axIndex, "powered"])

			for wheelIndex in range(0, 2):
				# Wheel 0 is left, 1 is the right one
				# Prepare the wheel's position vector
				pos = Point3(axWidth/2., axPos, rideHeight)

				# Prepare the wheel's bullet node
				npWheel = render.attachNewNode(BulletRigidBodyNode('wheelBox'))
				npWheel.node().setMass(p.get(["wheel", "weight"]))
				npWheel.setPos(pos)
				self.world.attachRigidBody(npWheel.node())

				# Load the wheel mesh
				npWheelMdl = npWheel.attachNewNode(loader.loadModel(self.datadir + p.get(["wheel", "mesh"])).node())
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
				wheel.setWheelRadius(p.get(["wheel", "radius"]))

				# suspension setup
				wheel.setFrontWheel(p.get(["axles", axIndex, "steerable"]))
				wheel.setMaxSuspensionTravelCm(p.get(["axles", axIndex, "suspension", "maxTravel"]))
				wheel.setMaxSuspensionForce(p.get(["axles", axIndex, "suspension", "maxForce"]))
				wheel.setSuspensionStiffness(p.get(["axles", axIndex, "suspension", "stiffness"]))
				wheel.setWheelsDampingRelaxation(p.get(["axles", axIndex, "suspension", "dampingRelax"]))
				wheel.setWheelsDampingCompression(p.get(["axles", axIndex, "suspension", "dampingCompression"]))
				wheel.setFrictionSlip(p.get(["axles", axIndex, "suspension", "frictionSlip"]))
				wheel.setRollInfluence(p.get(["axles", axIndex, "suspension", "rollInfluence"]))

				self.wheels.append(VWheel(npWheelMdl, npWheel, wheel, isPowered))

	def update(self, dt):
		self._steer()
		self.drivetrain.update(dt)

	def setGas(self, gas):
		if gas <= 1. and gas >= 0.:
			self.drivetrain.setGas(gas)
		else:
			print "Truck.py:setGas(gas) out of range! (0 < x < 1)"

	def setBrake(self, brake):
		if brake <= 1. and brake >= 0.:
			self.drivetrain.setBrake(brake)
		else:
			print "Truck.py:setBrake(brake) out of range! (0 < x < 1)"

	def getGbState(self):
		return self.drivetrain.getGbState()

	def shiftDrive(self):
		self.drivetrain.shiftDrive()

	def shiftNeutral(self):
		self.drivetrain.shiftNeutral()

	def shiftReverse(self):
		self.drivetrain.shiftReverse()

	def shiftPark(self):
		self.drivetrain.shiftPark()

	def steer(self, direction):
		if direction in [-1, 0, 1]:
			self._steerDir = direction
		else:
			print "[WRN] Truck.py:steer(): Invalid direction parameter."

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

	def getRpm(self):
		return self.drivetrain.getRpm()

	def getGear(self):
		return self.drivetrain.getGear()

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
