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
        tuning.setMaxSuspensionTravelCm(40.0)
        tuning.setMaxSuspensionForce(40000.0) # 1500 kg * 10 N/kg + a little extra
        tuning.setSuspensionStiffness(20.0)
        tuning.setSuspensionDamping(3.0)
        tuning.setSuspensionCompression(5.0)
        tuning.setFrictionSlip(1.5)
        
        self.wheels = []
        
        for i in range(0, 4):
            pos = self.chassis.getPos()
            rideHeight = -2.7
            
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
            npWheelMdl.setRenderModeWireframe()
            if i % 2 == 0:
                npWheelMdl.setH(180.0) # We need to turn around the meshes of wheel 0 and 2, the left ones
            
            wheel = self.vehicle.createWheel()
            wheel.setNode(npBody.node())
            wheel.setChassisConnectionPointCs(pos)
            if i < 2:
                wheel.setFrontWheel(True)

            wheel.setWheelDirectionCs(Vec3(0, 0, -1))
            wheel.setWheelAxleCs(Vec3(1, 0, 0))
            wheel.setWheelRadius(.45)
            wheel.setRollInfluence(0.5)
            
            self.wheels.append(VWheel(npWheelMdl, npBody, wheel))
        
    def update(self):
        if self._accel:
            pass
        if self._brake:
            pass
        
        self._accel = False
        self._brake = False
        self._steer = 0
        
    def accel(self):
        self._accel = True
        self.vehicle.applyEngineForce(1600.0, 2)
        self.vehicle.applyEngineForce(1600.0, 3)
    
    def brake(self):
        self._brake = True
        if self.vehicle.getCurrentSpeedKmHour() > 1:
            self.vehicle.applyEngineForce(0, 2)
            self.vehicle.applyEngineForce(0, 3)
            self.vehicle.setBrake(200.0, 2)
            self.vehicle.setBrake(200.0, 3)
        else:
            self.vehicle.applyEngineForce(-1000.0, 2)
            self.vehicle.applyEngineForce(-1000.0, 3)
    
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
        self.chassis.setPos(self.chassis.getPos() + (0,0,1.5))
        self.chassis.setR(0)

    def getChassisNp(self):
        return self.chassis.getNp()
    def getChassis(self):
        return self.chassis
