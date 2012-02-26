# -*- coding: utf-8 -*-
'''
Created on 16.10.2011

@author: marcel
'''

import math
from Drivetrain import AutomaticDt
from VehicleDOMParser import *
from VComponent import *
from Util import Util
from panda3d.core import *
from panda3d.bullet import *

class XMLTruck:
	hitchJoint = None

	def __init__(self, xmlfile, datadir, spawnpos, world):
		self.datadir = datadir
		self.world = world
		self.parser = VehicleDOMParser.createDOMParser(self.datadir + xmlfile)

		if self.parser == None:
			print "[ERR] XMLTruck: The xml file seems to have an unknown vehicle type set."

		p = self.parser # Will get ugly otherwise...

		# ===== Steering =====
		self.physMaxAngle = p.getSteeringAngleMax()	# The absolute maximum angle possible
		self.maxAngle = self.physMaxAngle 					# The maximum steering angle at the current speed (speed-sensitive)
		self.rate = p.getSteeringRate()
		self.curAngle = 0.0
		self._steerDir = 0	# -1, 0, 1: Sets the direction of steering

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

		# ===== Select a drivetrain =====
		if p.getDrivetrainType() == "automatic":
			self.drivetrain = AutomaticDt(self.vehicle, self.parser)
		else:
			print "[WRN] The selected drivetrain type is unknown, choosing automatic!"
			self.drivetrain = AutomaticDt(self.vehicle, self.parser)

		# ===== Dumper =====

		# ===== Wheels =====
		self.wheels = []

		for axIndex in range(0, p.getAxleCount()):
			axPos = p.getAxlePosition(axIndex)
			axWidth = p.getAxleWidth(axIndex)
			rideHeight = p.getRideheight()
			isPowered = p.axleIsPowered(axIndex)

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

				self.wheels.append(VWheel(npWheelMdl, npWheel, wheel, isPowered))

	def update(self, dt):
		self._steer()
		self.drivetrain.update(dt)
		self._applyAirDrag()

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

		for i in range(0, self.parser.getAxleCount()):
			if self.parser.axleIsSteerable(i):
				self.vehicle.setSteeringValue(self.curAngle, 2 * i)
				self.vehicle.setSteeringValue(self.curAngle, 2 * i + 1)

	def _applyAirDrag(self):
		# air density 0.0012 g/cm3 (at sea level and 20 °C)
		# cw-Value: 0.8 for a "truck", 0.5 for a modern 40 ton "with aero-kit" (see wikipedia), choosing 0.4 for now.
		# force = (density * cw * A * vel) / 2
		force = 0.0012 * 0.4 \
				* (self.parser.getDimensions()[0] * self.parser.getDimensions()[1]) \
				* (self.getSpeed() / 3.6) \
				/ 2

		# Its a braking force, after all
		force *= -1.

		relFVector = self.npBody.getRelativeVector(render, Point3(0, force, 0))
		self.npBody.node().applyCentralForce(relFVector);

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

	def couple(self, vehicles):
		""" Checks if another vehicle is within 1 unit (meter) range of our hitch. If yes, it will be connected to us. """
		if self.hitchJoint == None:
			ourHitchAbsolute = Util.getAbsolutePos(self.getTrailerHitchPoint(), self.getChassisNp())

			for vehicle in vehicles:
				otherHitchAbsolute = Util.getAbsolutePos(vehicle.getTrailerHitchPoint(), vehicle.getChassisNp())

				if not self == vehicle and Util.getDistance(ourHitchAbsolute, otherHitchAbsolute) <= 1:
					self.createCouplingJoint(self.getTrailerHitchPoint(),
											vehicle.getTrailerHitchPoint(), vehicle.getChassis().getBody().node())

		else:
			self.world.removeConstraint(self.hitchJoint)
			self.hitchJoint = None

	def createCouplingJoint(self, ourHitch, otherHitch, otherChassisNode):
		#BulletConeTwistConstraint (BulletRigidBodyNode const node_a, BulletRigidBodyNode const node_b,
		#							TransformState const frame_a, TransformState const frame_b)
		ourFrame = TransformState.makePosHpr(ourHitch, Vec3(0,0,0))
		otherFrame = TransformState.makePosHpr(otherHitch, Vec3(0,0,0))
		hitch = BulletConeTwistConstraint(self.getChassis().getBody().node(), otherChassisNode, ourFrame, otherFrame)
		hitch.setLimit(170, 40, 30)
		self.world.attachConstraint(hitch)
		self.hitchJoint = hitch

	def getChassisNp(self):
		return self.chassis.getNp()
	def getChassis(self):
		return self.chassis
	def getSpeed(self):
		return self.vehicle.getCurrentSpeedKmHour()
	def getTrailerHitchPoint(self):
		return self.parser.getTrailerHitchPoint()
