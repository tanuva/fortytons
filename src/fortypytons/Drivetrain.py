# -*- coding: utf-8 -*-

'''
Created on 4.10.2011

@author: marcel
'''

from panda3d.core import *
from panda3d.bullet import *

class AutomaticDt:
	"""
	Manages everything between the engine and BulletVehicle.setEngineForce()
	"""

	def __init__(self, vehicle, parser):
		self.parser = parser
		p = parser # A VehicleDOMParser instance we can get our data from
		self._vehicle = vehicle
		self._idlerpm = p.getEngineRpmIdle()
		self._maxrpm = p.getEngineRpmMax()
		self._funcs = p.getTorqueFuncs()
		self._gbRatios = p.getGearRatios()
		self._powAxleRatio = p.getPoweredAxleRatio()

		# engine
		self._currpm = 1000
		self._gasPedal = 0.0	# Range: 0.0 - 1.0
		self._brakePedal = 0.0


		# TODO switch reverse and neutral, this is fuckin unintuitive!

		# gearbox
		self._gbState = 'p'
		self._gbGear = 1 # 0 is reverse, 2 is first gear, default to neutral

	def setGas(self, gas):
		if gas <= 1. and gas >= 0.:
			self._gasPedal = gas
		else:
			print "Drivetrain:setGas(gas) out of range! (0 < x < 1)"

	def setBrake(self, brake):
		if brake <= 1. and brake >= 0.:
			self._brakePedal = brake
		else:
			print "Drivetrain:setBrake(brake) out of range! (0 < x < 1)"

	def _getNextGear(self):
		if self._gbGear < len(self._gbRatios) - 2:
			return self._gbGear + 1
		else:
			return self._gbGear

	def _getPrevGear(self):
		if self._gbGear > 2:
			return self._gbGear - 1
		else:
			return self._gbGear

	def _shiftGearUp(self):
		if self._gbState == 'd':
			self._gbGear = self._getNextGear()

	def _shiftGearDown(self):
		if self._gbState == 'd':
			self._gbGear = self._getPrevGear()

	def getGbState(self):
		return self._gbState

	def getRpm(self):
		return self._currpm

	def getGear(self):
		return self._gbGear

	def getGasPedal(self):
		return self._gasPedal

	def shiftDrive(self):
		if not self._gbState == 'd':
			self._gbState = 'd'
			self._gbGear = 2

	def shiftNeutral(self):
		if not self._gbState == 'n':
			self._gbState = 'n'
			self.gbGear = 1

	def shiftReverse(self):
		if not self._gbState == 'r':
			self._gbState = 'r'
			self._gbGear = 0

	def shiftPark(self):
		if not self._gbState == 'p':
			self._gbState = 'p'
			self._gbGear = 0

	def update(self, dt):
		# Average the delta rotation value for all powered wheels
		drot = 0.
		poweredWheelCount = 0

		for axIndex in range(0, self.parser.getAxleCount()):
			if self.parser.axleIsPowered(axIndex):
				drot += self._vehicle.getWheel(2 * axIndex).getDeltaRotation()
				drot += self._vehicle.getWheel(2 * axIndex + 1).getDeltaRotation()
				poweredWheelCount += 2

		drot = abs(drot) / poweredWheelCount
		rotspd = drot * (1./dt) # Average of the rear wheels' rotation speed (revs per second)
		rotspd *= 60 # convert to revs per minute

		# Calculate the rpm value the engine should have at our current speed
		# Must be absolute as reverse would result in negative rpm otherwise
		realrpm = abs(rotspd * self._gbRatios[self._gbGear] * self._powAxleRatio)

		# Do some "clutch" work
		if realrpm < self._idlerpm:
			self._currpm = self._idlerpm
		else:
			self._currpm = realrpm

		# Switching into reverse while going forward won't brake and go backward automatically. Thats not possible
		# in the real thing (tm) anyway.

		# Idle gas management (Automatically engage the clutch when switched to "Drive" or "Reverse")
		if self._gbState == 'p':
			self._parkingBrake()
		else:
			self._releaseParkingBrake()

		if realrpm < self._idlerpm \
		and (self._gbState == 'd' or self._gbState == 'r') \
		and not self._brakePedal == 1 and self._gasPedal < 0.2:
			self._accel(600., .2)

		else:
			self._accel()

		# Braking must always work
		self._brake()

	def _accel(self, rpm = -1., gas = -1.):
		if rpm == -1.:
			rpm = self._currpm
		if gas == -1.:
			gas = self._gasPedal

		if self._gbState == 'r' or self._gbState == 'd':
			# switch some gears
			# Don't consider reverse here since there's only one rev gear.
			if self._gbState == 'd':
				if rpm < 800.:
					self._gbGear = self._getPrevGear()
				elif rpm > 1600.:
					self._gbGear = self._getNextGear()

			# Calculate the acceleration force
			force = 0.

			for func in self._funcs:
				if rpm >= func["lo"] and rpm < func["hi"]:
					force = eval(func["function"])
					break

			# Take the gas pedal's position into account
			force *= gas

			# Gearbox reduces RPM by ratio, therefore increases torque by ratio
			# RPM / 6.32 ==> Nm * 6.32
			force *= self._gbRatios[self._gbGear] * self._powAxleRatio

			# Use the force!
			for axIndex in range(0, self.parser.getAxleCount()):
				if self.parser.axleIsPowered(axIndex):
					self._vehicle.applyEngineForce(force, 2 * axIndex)
					self._vehicle.applyEngineForce(force, 2 * axIndex + 1)

	def _brake(self):
		p = self.parser

		# We don't check self._gbState here, braking should always work...
		for axIndex in range(0, p.getAxleCount()):
			if p.axleIsPowered(axIndex):
				self._vehicle.setBrake(p.getBrakingForce() * self._brakePedal, 2 * axIndex)
				self._vehicle.setBrake(p.getBrakingForce() * self._brakePedal, 2 * axIndex + 1)

	def _parkingBrake(self):
		p = self.parser

		for axIndex in range(0, p.getAxleCount()):
			self._vehicle.setBrake(p.getParkingBrakeForce(), 2 * axIndex)
			self._vehicle.setBrake(p.getParkingBrakeForce(), 2 * axIndex + 1)

	def _releaseParkingBrake(self):
		p = self.parser

		for axIndex in range(0, p.getAxleCount()):
			self._vehicle.setBrake(0, 2 * axIndex)
			self._vehicle.setBrake(0, 2 * axIndex + 1)
