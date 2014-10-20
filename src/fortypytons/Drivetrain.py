# -*- coding: utf-8 -*-

'''
Created on 4.10.2011

@author: marcel
'''

from panda3d.core import *
from panda3d.bullet import *

from DebugGui import DebugGui

class Engine:
	""" This is the Engine Control Unit (ECU) """
	def __init__(self, idleRpm, maxRpm, torqueFuncs):
		self._idleRpm = idleRpm
		self._maxRpm = maxRpm
		self._torqueFuncs = torqueFuncs
		self._curRpm = idleRpm
		self._clutchState = 1.
		self._gas = 0.
		self.gui = DebugGui()

	def applyTorque(self, torque, dt):
		# TODO: this is bullshit - really?
		self._curRpm += torque * dt

	def _getTorque(self, gas, rpm):
		for func in self._torqueFuncs:
			if rpm >= func["lo"] and rpm < func["hi"]:
				# Take internal resistance (motor brake effect) into account
				resistance = 0.5 * self._curRpm# * (1. - gas)
				return eval(func["function"]) * gas - resistance

		# This really should never happen!
		print "[wrn] Drivetrain:Engine:_getTorque(): no matching torque curve for %s rpm!" % (rpm)
		return 0.

	def getTorque(self):
		return self._getTorque(self._gas, self._curRpm)

	def getRpm(self):
		return self._curRpm

	def update(self, dt, gas, inputRpm):
		""" Calculates the engine's behaviour depending on the rpm on the driveshaft and the gas pedal. """

		self._gas = gas

		if self._clutchState == 1.:
			self._curRpm = inputRpm

		# Keep ourselves alive
		if self._curRpm < (self._idleRpm * 0.9):
			self._gas = min(gas + 0.3, 1.0)
			self._curRpm = self._idleRpm
		elif self._curRpm >= (self._maxRpm * 0.9):
			print "Engine.update: overrevving, setting gas = 0.!"
			self._gas = 0.

		# Do some work!
		self.applyTorque(self._getTorque(self._gas, self._curRpm), dt)
		#self.gui.update("rpm: " + repr(int(self._curRpm)) _
		#	+ "\ntrq: " + repr(int(self.getTorque())))

	def closeClutch(self):
		self._clutchState = 1.

	def openClutch(self):
		self._clutchState = 0.

	def calcTorque(self, dt, outputRpm, inputRpm, inputTorque):
		factor = 0

		if inputRpm > 0.:
			factor = 1 - (outputRpm / inputRpm)
			#print "f", factor
			if factor < 0:
				factor = 0
			if factor > 1:
				factor = 1

		if inputRpm > outputRpm:
			if not outputRpm == 0:
				factor = inputRpm / outputRpm * -1.
			else:
				factor = 1
		else:
			if not inputRpm == 0:
				factor = outputRpm / inputRpm
			else:
				factor = 1

		return inputTorque * self._clutchState * factor

# =================================================================
class AutomaticGearbox:
	def __init__(self, ratios, axleRatio):
		self._ratios = ratios
		self._axleRatio = axleRatio
		self._gear = 1
		self._gbState = 'p'

	def _getNextGear(self):
		if self._gear < len(self._gbRatios) - 2:
			return self._gear + 1
		else:
			return self._gear

	def _getPrevGear(self):
		if self._gear > 2:
			return self._gear - 1
		else:
			return self._gear

	def _shiftGearUp(self):
		if self._gbState == 'd':
			self._gear = self._getNextGear()

	def _shiftGearDown(self):
		if self._gbState == 'd':
			self._gear = self._getPrevGear()

	def getGbState(self):
		return self._gbState

	def getGear(self):
		return self._gear

	def getPreRpm(self, inputRpm):
		return abs(inputRpm * self._ratios[self._gear] * self._axleRatio)

	def getPreTorque(self, inputRpm):
		if self._ratios[self._gear] == 0:
			return 0
		else:
			return inputRpm / self._axleRatio / self._ratios[self._gear]

	def getPostRpm(self, engineRpm):
		if self._ratios[self._gear] == 0:
			return 0
		else:
			return abs(engineRpm / self._axleRatio / self._ratios[self._gear])

	def getPostTorque(self, engineTorque):
		return engineTorque * self._ratios[self._gear] * self._axleRatio

	def shiftDrive(self):
		if not self._gbState == 'd':
			self._gbState = 'd'
			self._gear = 2

	def shiftNeutral(self):
		if not self._gbState == 'n':
			self._gbState = 'n'
			self._gear = 1

	def shiftReverse(self):
		if not self._gbState == 'r':
			self._gbState = 'r'
			self._gear = 0

	def shiftPark(self):
		self.shiftNeutral()

		if not self._gbState == 'p':
			self._gbState = 'p'

# =============================================================
class Drivetrain:
	def __init__(self, vehicle, parser):
		self.parser = parser
		self.gui = DebugGui()

		self._idleRpm = self.parser.getEngineRpmIdle()
		self._maxRpm = self.parser.getEngineRpmMax()
		self._torqueFuncs = self.parser.getTorqueFuncs()
		self._curRpm = self._idleRpm
		self._curTorque = 0.

		self._gasPedal = 0.0	# Range: 0.0 - 1.0
		self._brakePedal = 0.0

		self._vehicle = vehicle
		self._gearbox = AutomaticGearbox(self.parser.getGearRatios(), self.parser.getPoweredAxleRatio())

	# === Engine Stuff ===
	def __getTorque(self, gas):
		for func in self._torqueFuncs:
			if self._curRpm >= func["lo"] and self._curRpm < func["hi"]:
				# Take internal resistance (motor brake effect) into account
				resistance = 0.5 * self._curRpm# * (1. - gas)
				rpm = self._curRpm # Used by "function"
				return eval(func["function"]) * gas - resistance

		# This really should never happen!
		print "[wrn] Drivetrain:Engine:_getTorque(): no matching torque curve for %s rpm!" % (self._curRpm)
		return 0.

	def __calcOutputTorque(self, dt, outputRpm, inputRpm, inputTorque):
		factor = 0

		if inputRpm > 0.:
			factor = 1 - (outputRpm / inputRpm)
			#print "f", factor
			if factor < 0:
				factor = 0
			if factor > 1:
				factor = 1

		if inputRpm > outputRpm:
			if not outputRpm == 0:
				factor = inputRpm / outputRpm * -1.
			else:
				factor = 1
		else:
			if not inputRpm == 0:
				factor = outputRpm / inputRpm
			else:
				factor = 1

		return inputTorque * factor

	def __updateEngine(self, dt, inputRpm):
		if self._gearbox.getGbState() == "d" and self._curRpm > self._idleRpm:
			self._curRpm = inputRpm

		virtualGas = self._gasPedal

		# Keep ourselves alive
		if self._curRpm < (self._idleRpm):
			virtualGas = min(self._gasPedal + 0.6, 1.0)
			#self._curRpm = self._idleRpm
		elif self._curRpm >= (self._maxRpm * 0.9):
			print "Engine.update: overrevving, setting gas = 0.!"
			virtualGas = 0.

		# Apply torque as functions in vehicle.xml specify
		self._curTorque = self.__getTorque(virtualGas)

		# Do some work!
		# TODO: this is bullshit - really?
		self._curRpm += self._curTorque * dt
		self.gui.update("rpm: " + repr(int(self._curRpm))
			+ "\ntrq: " + repr(int(self._curTorque)))

	# === Drivetrain Stuff ===
	def _calcWheelRpm(self, dt):
		# Average the delta rotation value for all powered wheels
		drot = 0.
		poweredAxleCount = 0

		for axIndex in range(0, self.parser.getAxleCount()):
			if self.parser.axleIsPowered(axIndex):
				# TODO only consider wheels that have ground contact
				drot += self._vehicle.getWheel(2 * axIndex).getDeltaRotation()
				drot += self._vehicle.getWheel(2 * axIndex + 1).getDeltaRotation()
				poweredAxleCount += 1

		drot = abs(drot) / (2 * poweredAxleCount)
		wheelRpm = drot * (1./dt) # Average of the rear wheels' rotation speed (revs per second)
		wheelRpm *= 60 # convert to revs per minute

		return wheelRpm

	def update(self, dt):
		# input: wheels -> engine
		inputRpm = self._calcWheelRpm(dt) # effectively is inputRpm approx. the postGearRpm from the last frame
		preGearRpm = self._gearbox.getPreRpm(inputRpm)
		self.__updateEngine(dt, preGearRpm)

		# output: engine -> wheels
		postGearRpm = self._gearbox.getPostRpm(self._curRpm)
		postGearTorque = self._gearbox.getPostTorque(self._curTorque)
		outputTorque = self.__calcOutputTorque(dt, postGearRpm, inputRpm, postGearTorque)
		#print "wheel torque: ", outputTorque

		if self._gearbox.getGbState() == "p":
			for axIndex in range(0, self.parser.getAxleCount()):
				self._vehicle.setBrake(self.parser.getParkingBrakeForce() * self._brakePedal, 2 * axIndex)
				self._vehicle.setBrake(self.parser.getParkingBrakeForce() * self._brakePedal, 2 * axIndex + 1)
		else:
			# Use the force!
			for axIndex in range(0, self.parser.getAxleCount()):
				if self.parser.axleIsPowered(axIndex):
					self._vehicle.applyEngineForce(outputTorque, 2 * axIndex)
					self._vehicle.applyEngineForce(outputTorque, 2 * axIndex + 1)
			
			# Strong the dark side is in you
			for axIndex in range(0, self.parser.getAxleCount()):
				self._vehicle.setBrake(self.parser.getBrakingForce() * self._brakePedal, 2 * axIndex)
				self._vehicle.setBrake(self.parser.getBrakingForce() * self._brakePedal, 2 * axIndex + 1)

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

	def getRpm(self):
		return self._curRpm
	def getGasPedal(self):
		return self._gasPedal
	def getGbState(self):
		return self._gearbox.getGbState()
	def getGear(self):
		return self._gearbox.getGear()
	def shiftDrive(self):
		self._gearbox.shiftDrive()
	def shiftNeutral(self):
		self._gearbox.shiftNeutral()
	def shiftReverse(self):
		self._gearbox.shiftReverse()
	def shiftPark(self):
		self._gearbox.shiftPark()

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
			self._gbGear = 1

	def shiftReverse(self):
		if not self._gbState == 'r':
			self._gbState = 'r'
			self._gbGear = 0

	def shiftPark(self):
		self.shiftNeutral()

		if not self._gbState == 'p':
			self._gbState = 'p'

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
		elif self._gbState == 'n':
			self._accel(0., 0.)
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
