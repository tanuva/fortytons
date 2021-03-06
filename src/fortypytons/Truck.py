# -*- coding: utf-8 -*-
'''
Created on 05.08.2011

@author: marcel
'''

import math

#from WireGeom import WireGeom
from TuningGui import TuningGui
from Drivetrain import AutomaticDt
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
    _steerDir = 0       # -1, 0, 1: Sets the direction of steering

    def __init__(self, chassismesh, wheelmesh, pos, SCALE, maskTrucks, world):
        '''
        Loads the chassismesh, sets the truck up and ignites the engine.
        '''

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

        self.drivetrain = AutomaticDt(self.vehicle)

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
