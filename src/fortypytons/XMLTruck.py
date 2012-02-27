# -*- coding: utf-8 -*-
'''
Created on 16.10.2011

@author: marcel
'''

from panda3d.core import *
from panda3d.bullet import *
from XMLVehicle import XMLVehicle
from Drivetrain import AutomaticDt
from SoundController import SoundController
from Util import Util

class XMLTruck(XMLVehicle):
	def __init__(self, xmlfile, datadir, spawnpos, world):
		super(XMLTruck, self).__init__(xmlfile, datadir, spawnpos, world)
		p = self.parser # For readability...
		self.hitchConstraint = None
		self.hitchedTrailer = None

		# ===== Sound =====
		self.sound = SoundController(p.getEngineRpmIdle(),
									p.getEngineRpmMax() * 1./4.,
									p.getEngineRpmMax() * 2./4.,
									p.getEngineRpmMax() * 3./4.)

		# ===== Steering =====
		self.physMaxAngle = p.getSteeringAngleMax()	# The absolute maximum angle possible
		self.maxAngle = self.physMaxAngle			# The maximum steering angle at the current speed (speed-sensitive)
		self.rate = p.getSteeringRate()
		self.curAngle = 0.0
		self._steerDir = 0	# -1, 0, 1: Sets the direction of steering

		# ===== Select a drivetrain =====
		if p.getDrivetrainType() == "automatic":
			self.drivetrain = AutomaticDt(self.vehicle, self.parser)
		else:
			print "[WRN] The selected drivetrain type is unknown, choosing automatic!"
			self.drivetrain = AutomaticDt(self.vehicle, self.parser)


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
		if direction >= -1 and direction <= 1:
			self._steerDir = direction
		else:
			print "[WRN] XMLTruck:steer(): Invalid direction parameter."

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

	def update(self, dt):
		self._steer()
		self.drivetrain.update(dt)
		self._applyAirDrag()
		self._makeSound()
		if not self.hitchedTrailer == None:
			self.hitchedTrailer.update(dt, self.curAngle)

		for axle in range(0, self.parser.getAxleCount()):
			if self.parser.isAxleSteerable(axle):
				self.vehicle.setSteeringValue(self.curAngle * self.parser.getAxleSteeringFactor(axle), 2 * axle)
				self.vehicle.setSteeringValue(self.curAngle * self.parser.getAxleSteeringFactor(axle), 2 * axle + 1)

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

		relFVector = self.components[0].getBodyNp().getRelativeVector(render, Point3(0, force, 0))
		self.components[0].getBodyNp().node().applyCentralForce(relFVector);

	def _makeSound(self):
		self.sound.playEngineSound(self.getRpm(), self.drivetrain.getGasPedal())

	def getRpm(self):
		return self.drivetrain.getRpm()

	def getGear(self):
		return self.drivetrain.getGear()

	def reset(self):
		self.components[0].getBodyNp().setPos(self.components[0].getBodyNp().getPos() + (0,0,1.5))
		self.components[0].setR(0)

		if not self.hitchedTrailer == None:
			self.hitchedTrailer.getChassis().setPos(self.hitchedTrailer.getChassis().getPos() + (0,0,1.5))
			self.hitchedTrailer.getChassis().setR(0)

	def control(self, conIndex, direction):
		if not direction in [-1, 0, 1]:
			raise ValueError("direction is none of [-1, 0, 1]")
		
		if conIndex == 0:
			if direction in [-1, 1]:
				self.constraints[conIndex].getConstraint().enableAngularMotor(True, .4 * direction, 10000000.)
			elif direction == 0:
				self.constraints[conIndex].getConstraint().enableAngularMotor(True, .0, 1000000.)
			else:
				print "[WRN] XMLTruck:control0(direction): Direction is none of [1., 0., -1.]"

	def couple(self, vehicles):
		""" Checks if another vehicle is within 1 unit (meter) range of our hitch. If yes, it will be connected to us. """
		if self.hitchConstraint == None:
			ourHitchAbsolute = Util.getAbsolutePos(self.getTrailerHitchPoint(), self.getChassis().getBodyNp())

			for vehicle in vehicles:
				otherHitchAbsolute = Util.getAbsolutePos(vehicle.getTrailerHitchPoint(), vehicle.getChassis().getBodyNp())

				if not self == vehicle and vehicle.getType() == "trailer" \
					and Util.getDistance(ourHitchAbsolute, otherHitchAbsolute) <= 1:
					self.hitchConstraint = self.createCouplingJoint(self.getTrailerHitchPoint(),
												vehicle.getTrailerHitchPoint(), vehicle.getChassis().getBodyNp().node())
					self.hitchedTrailer = vehicle
		else:
			self.world.removeConstraint(self.hitchConstraint)
			self.hitchConstraint = None
			self.hitchedTrailer = None

	def createCouplingJoint(self, ourHitch, otherHitch, otherChassisNode):
		#BulletConeTwistConstraint (BulletRigidBodyNode const node_a, BulletRigidBodyNode const node_b,
		#							TransformState const frame_a, TransformState const frame_b)
		ourFrame = TransformState.makePosHpr(ourHitch, Vec3(0,0,0))
		otherFrame = TransformState.makePosHpr(otherHitch, Vec3(0,0,0))
		hitchConstraint = BulletConeTwistConstraint(self.getChassis().getBodyNp().node(), otherChassisNode, ourFrame, otherFrame)
		hitchConstraint.setLimit(170, 40, 30)
		self.world.attachConstraint(hitchConstraint)
		return hitchConstraint
