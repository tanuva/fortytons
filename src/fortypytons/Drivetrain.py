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

	# engine
	_maxrpm = 2520
	_idlerpm = 600
	_currpm = 1000
	_gasPedal = 0.0		# Range: 0.0 - 1.0
	_brakePedal = 0.0

	# gearbox
	_gbState = 'p'
	_gbGear = 0 # 1 is reverse, 2 is first gear, default to neutral

	def __init__(self, vehicle, parser):
		self.parser = parser
		p = parser # A VehicleDOMParser instance we can get our data from
		self._vehicle = vehicle
		self._idlerpm = p.get(["drivetrain", "idleRpm"])
		self._maxrpm = p.get(["drivetrain", "maxRpm"])
		self._funcs = p.get(["drivetrain", "torque"]).values()
		self._gbRatios = self.cleanGbRatios(p.get(["drivetrain", "gears"]))
		self._powAxleRatio = p.get(["drivetrain", "powAxleRatio"])

	def cleanGbRatios(self, dic):
		"""
		Convert the dictionary keys to int, put the values (gbRatios) into a sorted array.
		"""

		out = []
		tmp = [int(key) for key in dic.keys()]

		# convert the keys from string to int, preserving order
		for key in sorted(tmp):
			out.append(dic[str(key)]["ratio"])

		return out

	def setGas(self, gas):
		if gas <= 1. and gas >= 0.:
			self._gasPedal = gas
		else:
			print "Truck.py:setGas(gas) out of range! (0 < x < 1)"

	def setBrake(self, brake):
		if brake <= 1. and brake >= 0.:
			self._brakePedal = brake
		else:
			print "Truck.py:setBrake(brake) out of range! (0 < x < 1)"

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

	def _shiftReverse(self):
		self._gbGear = 1

	def getGbState(self):
		return self._gbState

	def getRpm(self):
		return self._currpm

	def getGear(self):
		return self._gbGear

	def shiftDrive(self):
		if not self._gbState == 'd':
			self._gbState = 'd'
			self._gbGear = 2

	def shiftNeutral(self):
		if not self._gbState == 'n':
			self._gbState = 'n'
			self.gbGear = 0

	def shiftReverse(self):
		if not self._gbState == 'r':
			self._gbState = 'r'
			self._gbGear = 1

	def shiftPark(self):
		if not self._gbState == 'p':
			self._gbState = 'p'
			self._gbGear = 0

	def update(self, dt):
		drot = abs((self._vehicle.getWheel(2).getDeltaRotation() + self._vehicle.getWheel(3).getDeltaRotation()) / 2)
		rotspd = drot * (1./dt) # Average of the rear wheels' rotation speed (revs per second)
		rotspd *= 60 # convert to revs per minute

		# Calculate the rpm value the engine should have at our current speed
		realrpm = rotspd * self._gbRatios[self._gbGear] * self._powAxleRatio

        # Do some "clutch" work
		if realrpm < self._idlerpm:
			self._currpm = self._idlerpm
		else:
			self._currpm = realrpm

        #print "%i <> %i" % (realrpm, self._currpm)

        # Idle gas
		if self._currpm < self._idlerpm \
		and (self._gbState == 'd' or self._gbState == 'r') \
		and not self._brakePedal == 1 \
		and self._gasPedal < 0.4:
			self.accel(600, .4)
		elif self._gbState == 'p':
			self._parkingBrake()
		else:
			self._accel()
			self._brake()

	def _accel(self, rpm = -1., gas = -1.):
		if rpm == -1.:
			rpm = self._currpm
		if gas == -1.:
			gas = self._gasPedal

		if self._gbState == 'r' or self._gbState == 'd':
			# switch some gears
			if self._gbState == 'd':
				if rpm < 800.:
					self._gbGear = self._getPrevGear()
				elif rpm > 1600.:
					self._gbGear = self._getNextGear()
			else:
				self._shiftReverse()

			force = self._calcAccelForce(rpm, gas, self._gbGear)
			self._vehicle.applyEngineForce(force, 2)
			self._vehicle.applyEngineForce(force, 3)

	def _brake(self):
		p = self.parser

		# We don't check self._gbState here, braking should always work...
		for axIndex in p.get(["axles"]):
			if p.get(["axles", axIndex, "powered"]):
				self._vehicle.setBrake(25.0 * self._brakePedal, int(axIndex))
				self._vehicle.setBrake(25.0 * self._brakePedal, int(axIndex) + 1)

	def _parkingBrake(self):
		p = self.parser

		for axIndex in p.get(["axles"]):
			self._vehicle.setBrake(800., int(axIndex))
			self._vehicle.setBrake(800., int(axIndex) + 1)

	def _calcAccelForce(self, rpm, gas, gear):
		force = 0.

		for func in self._funcs:
			if rpm >= func["lo"] and rpm < func["hi"]:
				force = eval(func["function"])

        # Take the gas pedal's position into account
		force *= gas

        # Gearbox reduces RPM by ratio, therefore increases torque by ratio
        # RPM / 6.32 ==> Nm * 6.32
		force *= self._gbRatios[gear] * self._powAxleRatio

		return force
