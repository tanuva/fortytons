# -*- coding: utf-8 -*-
'''
Created on 05.08.2011

@author: marcel
'''

import math

#from WireGeom import WireGeom
from TuningGui import TuningGui
from VComponent import *
from direct.directtools.DirectGeometry import LineNodePath
from panda3d.core import *
from panda3d.bullet import *

class Truck:
    '''
    The player truck.
    '''

    # steering
    physMaxAngle = 45.0 # The absolute maximum angle
    curAngle = 0.0
    maxAngle = physMaxAngle # The maximum steering angle at the current speed (speed-sensitive)
    rate = 1.1

    # engine
    _maxrpm = 2520
    _idlerpm = 600
    _currpm = 1000
    _gas = 0.0      # Gas pedal. Range: 0.0 - 1.0
    _brake = 0.0    # Brake pedal.

    # gearbox
    _gbStates = { 0: 'p', 1: 'r', 2: 'n', 3: 'd' }
    _gbRatios = { 0: 6.29, 1: 6.29, 2: 3.48, 3: 2.10, 4: 1.38, 5: 1.00, 6: 0.79 }
    _gbState = 0
    _gbGear = 1 # 0 is reverse, default to first gear
    _rearAxRatio = 3.636

    def __init__(self, chassismesh, wheelmesh, pos, SCALE, maskTrucks, world):
        '''
        Loads the chassismesh, sets the truck up and ignites the engine.
        '''

        self._steer = 0
        self._accel = False
        self._brake = False
        self.world = world

        # eggmesh: center-side 1m, center-front 2.5m, center-top 1.7m, height exhaust: 0.1m
        # chassis box: .51m high, cabin box 1.18m high (without exhaust tips)
        # platform: 3.15m x 2m x 0.6m (l,w,h)

        # === Chassis ===
        npBody = render.attachNewNode(BulletRigidBodyNode('truckBox'))
        # TransformState: compensate for the exhausts sticking out of the top
        npBody.node().addShape(BulletBoxShape(Vec3(1, 2.5, .51/2.0)), TransformState.makePos(Vec3(0, 0, -.65)))
        npBody.node().addShape(BulletBoxShape(Vec3(1, .75, 1.18/2.0)), TransformState.makePos(Vec3(0, 1.75, .2)))
        npBody.node().setMass(3362.0)
        npBody.node().setDeactivationEnabled(False)
        npBody.setPos(pos)
        self.world.attachRigidBody(npBody.node())

        npTruckMdl = npBody.attachNewNode(loader.loadModel(chassismesh).node())
        self.chassis = VComponent(npTruckMdl, npBody)

        # === Platform / Dumper ===
        npDump = npBody.attachNewNode(BulletRigidBodyNode("dumpBox"))
        npDump.node().addShape(BulletBoxShape(Vec3(1., 3.15/2., 0.6/2.)))
        npDump.node().setMass(300.0)
        npDump.node().setDeactivationEnabled(False)
        npDump.setPos(pos + (0, -.925, -2.1))
        self.world.attachRigidBody(npDump.node())

        npDumpMdl = npDump.attachNewNode(loader.loadModel("../../data/mesh/mulde.egg").node())
        self.dump = VComponent(npDumpMdl, npDump)

        # === Connect Chassis and Dumper ===
        #BulletHingeConstraint (BulletRigidBodyNode const node_a, BulletRigidBodyNode const node_b,
        #                       Point3 const pivot_a, Point3 const pivot_b,
        #                       Vec3 const axis_a, Vec3 const axis_b,
        #                       bool use_frame_a)
        con = BulletHingeConstraint(npBody.node(), npDump.node(),
                                    Point3(0, -2.5, -.4), Point3(0, -3.15/2., -.4),
                                    Vec3(1,0,0), Vec3(1,0,0), True)
        con.setAxis(Vec3(1,0,0))
        con.setLimit(0, 50)
        con.setDebugDrawSize(2.0)
        self.world.attachConstraint(con)
        self.dumperCon = con
        # Keep the dumper down
        self.dumperCon.enableAngularMotor(True, -5., 300.)

        # === BulletVehicle setup ===
        self.vehicle = BulletVehicle(self.world, npBody.node())
        self.vehicle.setCoordinateSystem(ZUp)
        self.world.attachVehicle(self.vehicle)
        self.tuningGui = TuningGui(self.vehicle.getTuning())

        tuning = self.vehicle.getTuning()

        # === We need rolling devices! ===
        self.wheels = []

        for i in range(0, 4):
            rideHeight = -0.3
            pos = Point3(0, 0, rideHeight)

            if i == 0:
                pos += (-.85, 1.8, rideHeight)
            if i == 1:
                pos += (.85, 1.8, rideHeight)
            if i == 2:
                pos += (-.85, -1.5, rideHeight)
            if i == 3:
                pos += (.85, -1.5, rideHeight)

            # Prepare bullet nodes
            npBody = render.attachNewNode(BulletRigidBodyNode('wheelBox'))
            npBody.node().setMass(25.0)
            npBody.setPos(pos)
            self.world.attachRigidBody(npBody.node())

            npWheelMdl = npBody.attachNewNode(loader.loadModel(wheelmesh).node())
            if i % 2 == 0:
                npWheelMdl.setH(180.0) # We need to turn around the meshes of wheel 0 and 2, the left ones

            wheel = self.vehicle.createWheel()
            wheel.setNode(npBody.node())
            wheel.setChassisConnectionPointCs(pos)

            wheel.setWheelDirectionCs(Vec3(0, 0, -1))
            wheel.setWheelAxleCs(Vec3(1, 0, 0))
            wheel.setWheelRadius(.45)
            isPowered = False

            # suspension setup
            if i in range(0, 2): # [0, 1]
                # front axle
                wheel.setFrontWheel(True)
                wheel.setMaxSuspensionTravelCm(35.0)
                wheel.setMaxSuspensionForce(60000.0) # 3362 kg * 10 N/kg + some extra
                wheel.setSuspensionStiffness(20.0)
                wheel.setWheelsDampingRelaxation(2.)
                wheel.setWheelsDampingCompression(5.)
                wheel.setFrictionSlip(1.5)
                wheel.setRollInfluence(0.3)

            if i in range(2, 4): # [2, 3]
                # rear axle
                wheel.setMaxSuspensionTravelCm(40.0)
                wheel.setMaxSuspensionForce(60000.0)
                wheel.setSuspensionStiffness(35.0)
                wheel.setWheelsDampingRelaxation(2.)
                wheel.setWheelsDampingCompression(5.)
                wheel.setFrictionSlip(1.5)
                wheel.setRollInfluence(0.3)
                isPowered = True

            self.wheels.append(VWheel(npWheelMdl, npBody, wheel, isPowered))

        # =========================
        # === Setup the trailer ===
        npTrailer = render.attachNewNode(BulletRigidBodyNode('trailerBox'))
        npTrailer.node().addShape(BulletBoxShape(Vec3(1, 3.15/2., .27/2.0)), TransformState.makePos(Vec3(0,-.5, .15/2.)))
        npTrailer.node().setMass(800.0)
        npTrailer.node().setDeactivationEnabled(False)
        npTrailer.setPos(self.chassis.getPos() + (0,-5,0))
        self.world.attachRigidBody(npTrailer.node())

        npTrailerMdl = npTrailer.attachNewNode(loader.loadModel("../../data/mesh/trailer.egg").node())
        self.tChassis = VComponent(npTrailerMdl, npTrailer)

        self.trailer = BulletVehicle(self.world, npTrailer.node())
        self.trailer.setCoordinateSystem(ZUp)
        self.world.attachVehicle(self.trailer)

        tuning = self.trailer.getTuning()
        tuning.setMaxSuspensionTravelCm(40.0)
        tuning.setMaxSuspensionForce(40000.0) # 1500 kg * 10 N/kg + a little extra
        tuning.setSuspensionStiffness(20.0)
        tuning.setSuspensionDamping(3.0)
        tuning.setSuspensionCompression(5.0)
        tuning.setFrictionSlip(1.5)

        # === We need rolling devices! ===
        self.tWheels = []

        for i in range(0, 4):
            pos = Point3(0,0,0)
            rideHeight = 0

            if i == 0:
                pos += (-.85, 0, rideHeight)
            if i == 1:
                pos += (.85, 0, rideHeight)
            if i == 2:
                pos += (-.85, -1, rideHeight)
            if i == 3:
                pos += (.85, -1, rideHeight)

            # Prepare bullet nodes
            npBody = render.attachNewNode(BulletRigidBodyNode('tWheelBox'))
            npBody.node().setMass(25.0)
            npBody.setPos(pos)
            self.world.attachRigidBody(npBody.node())

            npWheelMdl = npBody.attachNewNode(loader.loadModel(wheelmesh).node())
            if i % 2 == 0:
                npWheelMdl.setH(180.0) # We need to turn around the meshes of wheel 0 and 2, the left ones

            wheel = self.trailer.createWheel()
            wheel.setNode(npBody.node())
            wheel.setChassisConnectionPointCs(pos)

            wheel.setWheelDirectionCs(Vec3(0, 0, -1))
            wheel.setWheelAxleCs(Vec3(1, 0, 0))
            wheel.setWheelRadius(.45)
            wheel.setRollInfluence(0.3)

            self.tWheels.append(VWheel(npWheelMdl, npBody, wheel, False))

        # === Connect truck and trailer ===
        # Truck hook point: (0, -2.511, -.515)
        # Trailer hook poi: (0, 2.086, .075)
        #BulletConeTwistConstraint (BulletRigidBodyNode const node_a, BulletRigidBodyNode const node_b, TransformState const frame_a, TransformState const frame_b)
        t1 = TransformState.makePosHpr(Point3(0, -2.511, -.515), Vec3(0,0,0))
        t2 = TransformState.makePosHpr(Point3(0, 2.086, .075), Vec3(0, 0, 0))
        hitch = BulletConeTwistConstraint(self.chassis.getBody().node(), self.tChassis.getBody().node(), t1, t2)
        hitch.setLimit(170, 40, 30)
        self.world.attachConstraint(hitch)

        # === Put a dumper onto the trailer ===
        nptDump = npTrailer.attachNewNode(BulletRigidBodyNode("tdumpBox"))
        nptDump.node().addShape(BulletBoxShape(Vec3(1., 3.15/2., 0.6/2.)))
        nptDump.node().setMass(300.0)
        nptDump.node().setDeactivationEnabled(False)
        nptDump.setPos(Point3(0, -.5, .5))
        self.world.attachRigidBody(nptDump.node())

        nptDumpMdl = nptDump.attachNewNode(loader.loadModel("../../data/mesh/mulde.egg").node())
        self.tdump = VComponent(nptDumpMdl, npTrailer)

        # === Connect trailer and dumper ===
        #BulletHingeConstraint (BulletRigidBodyNode const node_a, BulletRigidBodyNode const node_b,
        #                       Point3 const pivot_a, Point3 const pivot_b,
        #                       Vec3 const axis_a, Vec3 const axis_b,
        #                       bool use_frame_a)
        tcon = BulletHingeConstraint(npTrailer.node(), nptDump.node(),
                                    Point3(0, -3.15/2, .1), Point3(0, -3.15/2., .1),
                                    Vec3(1,0,0), Vec3(1,0,0), True)
        tcon.setAxis(Vec3(1,0,0))
        tcon.setLimit(0, 50)
        tcon.setDebugDrawSize(2.0)
        self.world.attachConstraint(tcon)
        # Keep the dumper down
        tcon.enableAngularMotor(True, -5., 300.)

    def update(self, dt):
        self.steer()

        # FIXME Do we have to abs() here?
        drot = abs((self.vehicle.getWheel(2).getDeltaRotation() + self.vehicle.getWheel(3).getDeltaRotation()) / 2)
        rotspd = drot * (1./dt) # Average of the rear wheels' rotation speed (revs per second)
        rotspd *= 60 # convert to revs per minute

        # Calculate the rpm value the engine should have at our current speed
        realrpm = rotspd * self._gbRatios[self._gbGear] * self._rearAxRatio

        # Do some "clutch" work
        if realrpm < self._idlerpm:
            self._currpm = self._idlerpm
        else:
            self._currpm = realrpm

        #print "%i <> %i" % (realrpm, self._currpm)

        # Idle gas
        if realrpm < self._idlerpm and not self._brake == 1 and self._gas < 0.4:
            self.accel(600, .4)
        else:
            self.accel()
            self.brake()

    def accel(self, rpm = -1., gas = -1.):
        if rpm == -1.:
            rpm = self._currpm
        if gas == -1.:
            gas = self._gas

        # switch some gears
        if self._gbState == 3:
            """self._calcAccelForce(rpm, gas, self._gbGear) < self._calcAccelForce(rpm, gas, self._getPrevGear()) or"""
            """self._calcAccelForce(rpm, gas, self._gbGear) < self._calcAccelForce(rpm, gas, self._getNextGear()) or"""

            if rpm < 800.:
                self._gbGear = self._getPrevGear()
            elif rpm > 1600.:
                self._gbGear = self._getNextGear()

        force = 0.

        if self._gbState == 1 or self._gbState == 3:
            force = self._calcAccelForce(rpm, gas, self._gbGear)

        if self._gbState == 3:
            self.vehicle.applyEngineForce(force, 2)
            self.vehicle.applyEngineForce(force, 3)
        elif self._gbState == 1:
            self.vehicle.applyEngineForce(force * -1., 2)
            self.vehicle.applyEngineForce(force * -1., 3)

    def _calcAccelForce(self, rpm, gas, gear):
        force = 0.

        if rpm >= 600. and rpm < 1151.:
            force = (1./3.) * rpm + 450.
        elif rpm >= 1151. and rpm < 1601.:
            force = 500.
        elif rpm >= 1601. and rpm <= 2521.:
            force = -.234 * (rpm - 1600.) + 500.

        # Take the gas pedal's position into account
        force *= gas

        # Gearbox reduces RPM by ratio, therefore increases torque by ratio
        # RPM / 6.32 ==> Nm * 6.32
        force *= self._gbRatios[gear] * self._rearAxRatio

        return force

    def brake(self):
        # We don't check self._gbState here, braking should always work...
        self.vehicle.setBrake(200.0 * self._brake, 2)
        self.vehicle.setBrake(200.0 * self._brake, 3)

    def setGas(self, gas):
        if gas <= 1. and gas >= 0.:
            self._gas = gas
        else:
            print "Truck.py:setGas(gas) out of range! (0 < x < 1)"

    def setBrake(self, brake):
        if brake <= 1. and brake >= 0.:
            self._brake = brake
        else:
            print "Truck.py:setBrake(brake) out of range! (0 < x < 1)"

    def shiftUp(self):
        if self._gbState < 3:
            self._gbState += 1

        # Switch to reverse or first if appropriate
        if self._gbState == 1:
            self._gbGear = 0
        else:
            self._gbGear = 1

    def shiftDown(self):
        if self._gbState > 0:
            self._gbState -= 1

        # Switch to reverse or first if appropriate
        if self._gbState == 1:
            self._gbGear = 0
        else:
            self._gbGear = 1

    def _getNextGear(self):
        if self._gbGear < len(self._gbRatios) - 1:  # subtract the reverse gear!
            return self._gbGear + 1
        else:
            return self._gbGear

    def _getPrevGear(self):
        if self._gbGear > 1:
            return self._gbGear - 1
        else:
            return self._gbGear

    def getGbState(self):
        return self._gbStates[self._gbState]

    def steerLeft(self):
        self._steer = 1
    def steerRight(self):
        self._steer = -1
    def steerStraight(self):
        self._steer = 0

    def steer(self):
        # We are speed sensitive
        speed = self.vehicle.getCurrentSpeedKmHour()
        if speed > 0 and speed < 90:
            self.maxAngle = (-.5) * speed + 45 # Graph this on WolframAlpha to make it obvious :)
        elif speed > 90:
            self.maxAngle = 1.0

        if self._steer == 1 and self.curAngle < self.maxAngle:
            if self.curAngle < 0:
                self.curAngle += 2.0 * self.rate
            else:
                self.curAngle += self.rate
        elif self._steer == -1 and self.curAngle > self.maxAngle * -1:
            if self.curAngle > 0:
                self.curAngle -= 2.0 * self.rate
            else:
                self.curAngle -= self.rate
        else: # self._steer == 0
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
        return self._currpm

    def getGear(self):
        return self._gbGear

    def reset(self):
        self.chassis.setPos(self.chassis.getPos() + (0,0,1.5))
        self.chassis.setR(0)

    def dumperUp(self):
        self.dumperCon.enableAngularMotor(True, .2, 300.)

    def dumperStop(self):
        self.dumperCon.enableAngularMotor(True, .0, 300.)

    def dumperDown(self):
        self.dumperCon.enableAngularMotor(True, -.2, 300.)

    def getChassisNp(self):
        return self.chassis.getNp()
    def getChassis(self):
        return self.chassis
    def getSpeed(self):
        return self.vehicle.getCurrentSpeedKmHour()
