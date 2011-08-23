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
    curAngle = 0.0
    maxAngle = 45.0
    rate = 1.1

    def __init__(self, chassismesh, wheelmesh, pos, SCALE, maskTrucks, world):
        '''
        Loads the chassismesh, sets the truck up and ignites the engine.
        '''
        
        self._steer = 0
        self._accel = False
        self._brake = False
        self.world = world
        
        # eggmesh: center-side 1m, center-front 2.5m, center-top 1.7m, height exhaust: 0.1m
        #npTruckCol.node().addSolid(CollisionBox(Vec3(0,0,0), 1, 2.5, 1.7/2))
        #npTruckCol.setZ(-.1) # Compensate for exhausts sticking out
        
        # Load the chassismesh
        npBody = render.attachNewNode(BulletRigidBodyNode('truckBox')) 
        # TransformState: compensate for the exhausts sticking out of the top
        npBody.node().addShape(BulletBoxShape(Vec3(1, 2.5, 1.8/2.0)), TransformState.makePos(Vec3(0, 0, -.1)))
        npBody.node().setMass(1500.0*SCALE)
        npBody.node().setDeactivationEnabled(False)
        npBody.setPos(pos)
        self.world.attachRigidBody(npBody.node())
        
        npTruckMdl = npBody.attachNewNode(loader.loadModel(chassismesh).node())
        npTruckMdl.setRenderModeWireframe()
        self.chassis = VComponent(npTruckMdl, npBody)

        self.vehicle = BulletVehicle(self.world, npBody.node())
        self.vehicle.setCoordinateSystem(ZUp)
        self.world.attachVehicle(self.vehicle)
        self.tuningGui = TuningGui(self.vehicle.getTuning())

        tuning = self.vehicle.getTuning()
        tuning.setMaxSuspensionTravelCm(35.0)
        tuning.setMaxSuspensionForce(40000.0) # 1500 kg * 10 N/kg + a little extra
        tuning.setSuspensionStiffness(100.0)
        tuning.setSuspensionDamping(3.0)
        tuning.setSuspensionCompression(5.0)
        tuning.setFrictionSlip(1.0)
        
        self.wheels = []
        
        for i in range(0, 4):
            pos = self.chassis.getPos()
            rideHeight = -2.6
            
            if i == 0:
                pos += (-.85, 1.8, rideHeight)
                #anchor = pos - (0.175, 0, 0)
            if i == 1:
                pos += (.85, 1.8, rideHeight)
                #anchor = pos + (0.175, 0, 0) # We want the anchor at the inside of the wheel, not in the center
            if i == 2:
                pos += (-.85, -1.5, rideHeight)
                #anchor = pos - (0.175, 0, 0)
            if i == 3:
                pos += (.85, -1.5, rideHeight)
                #anchor = pos + (0.175, 0, 0) # We want the anchor at the inside of the wheel, not in the center

            anchor = pos

            # Prepare bullet nodes
            npBody = render.attachNewNode(BulletRigidBodyNode('wheelBox')) 
            #npBody.node().addShape(BulletCylinderShape(.45, .35, XUp))
            npBody.node().setMass(25.0)
            npBody.setPos(pos)
            self.world.attachRigidBody(npBody.node())
            
            npWheelMdl = npBody.attachNewNode(loader.loadModel(wheelmesh).node())
            npWheelMdl.setRenderModeWireframe()
            if i % 2 == 0:
                npWheelMdl.setH(180.0) # We need to turn around the meshes of wheel 0 and 2, the left ones
            
            wheel = self.vehicle.createWheel()
            wheel.setNode(npBody.node())
            wheel.setChassisConnectionPointCs(Point3(anchor))
            if i < 2:
                wheel.setFrontWheel(True)

            wheel.setWheelDirectionCs(Vec3(0, 0, -1))
            wheel.setWheelAxleCs(Vec3(1, 0, 0))
            wheel.setWheelRadius(.45)
            wheel.setRollInfluence(0.1)
            
            self.wheels.append(VWheel(npWheelMdl, npBody, wheel))
        
        # Construct the front axle
        #npAx1 = render.attachNewNode(BulletRigidBodyNode("axle1"))
        #npAx1.node().addShape(BulletBoxShape(Vec3(0.5, 0.1, 0.1)))
        #npAx1.node().setMass(30.0*SCALE)
        #npAx1.setPos(pos + (0, 1.9, -1.1))
        #self.world.attachRigidBody(npAx1.node())
        
        # Left spring
        #t1 = TransformState.makePosHpr(pos + (-0.5, 1.9, -1.0), Vec3(0,-90, 0))
        #t2 = TransformState.makePosHpr(pos + (-0.5, 1.9, -1.1), Vec3(0, 90, 0))
        """t1 = TransformState.makePos(pos + (-0.5, 1.9, -1.0))
        t2 = TransformState.makePos(pos + (-0.5, 1.9, -1.1))
        cAx1 = BulletSliderConstraint(npBody.node(), npAx1.node(),
                                      t1, t2,
                                      True)
        cAx1.setLowerLinearLimit(0.05)
        cAx1.setUpperLinearLimit(0.2)
        cAx1.setLowerAngularLimit(0)
        cAx1.setUpperAngularLimit(0)
        cAx1.setDebugDrawSize(2.0)
        #cAx1.enableFeedback(True)
        self.world.attachConstraint(cAx1)"""
        """npAx1.ls()
        c = BulletHingeConstraint(npAx1.node(), self.wheels[1].getNp().node(),
                                  Point3(-.5, 1.9, -1.0),
                                  Point3(-.35/2.0, 0, 0),
                                  Vec3(0,0,1), Vec3(0,0,1))
        self.world.attachConstraint(c)"""
        
        # We are going to be drawing some lines between the anchor points and the joints
        #self.lines = LineNodePath(parent = render, thickness = 3.0, colorVec = Vec4(1, 0, 0, 1))
    
    def update(self):
        if self._accel:
            pass
        if self._brake:
            pass
        
        self._accel = False
        self._brake = False
        self._steer = 0
        
        #self.lines.reset()
        #self.lines.drawLines([[(self.trucks[0][0].getX(), self.trucks[0][0].getY(), self.trucks[0][0].getZ()),
        #                      (5, 0, 5)],
        #                      [(5, 0, 5),
        #                      (self.trucks[1][0].getX(), self.trucks[1][0].getY(), self.trucks[1][0].getZ())]])
        #self.lines.create()
    
    def accel(self):
        self._accel = True
        self.vehicle.applyEngineForce(800.0, 2)
        self.vehicle.applyEngineForce(800.0, 3)
    
    def brake(self):
        self._brake = True
        if self.vehicle.getCurrentSpeedKmHour() > 1:
            self.vehicle.applyEngineForce(0, 2)
            self.vehicle.applyEngineForce(0, 3)
            self.vehicle.setBrake(600.0, 2)
            self.vehicle.setBrake(600.0, 3)
        else:
            self.vehicle.applyEngineForce(-400.0, 2)
            self.vehicle.applyEngineForce(-400.0, 3)
    
    def steerLeft(self):
        self._steer = 1
    def steerRight(self):
        self._steer = -1
    def steerStraight(self):
        self._steer = 0

    def steer(self):
        if self._steer == 1 and self.curAngle < self.maxAngle:
            if self.curAngle < 0:
                self.curAngle += 2.0 * self.rate
            else:
                self.curAngle += self.rate
        if self._steer == -1 and self.curAngle > self.maxAngle * -1:
            if self.curAngle > 0:
                self.curAngle -= 2.0 * self.rate
            else:
                self.curAngle -= self.rate
        if self._steer == 0:
            # steer straight
            if self.curAngle > 0:
                self.curAngle -= 2.0 * self.rate
            if self.curAngle < 0:
                self.curAngle += 2.0 * self.rate

        self.vehicle.setSteeringValue(self.curAngle, 0)
        self.vehicle.setSteeringValue(self.curAngle, 1)
        
    def update(self, dt):
        self.steer()

    def reset(self):
        self.chassis.setPos(self.chassis.getPos() + (0,0,3))
        self.chassis.setR(0)

    def getChassisNp(self):
        return self.chassis.getNp()
    def getChassis(self):
        return self.chassis
