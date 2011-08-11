# -*- coding: utf-8 -*-
'''
Created on 05.08.2011

@author: marcel
'''

import math

from WireGeom import WireGeom
from VComponent import *
from direct.directtools.DirectGeometry import LineNodePath
from panda3d.core import *
from panda3d.bullet import *

class Truck:
    '''
    The player truck.
    '''

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
        npBody.setPos(pos)
        self.world.attachRigidBody(npBody.node())
        
        npTruckMdl = npBody.attachNewNode(loader.loadModel(chassismesh).node())
        npTruckMdl.setRenderModeWireframe()
        
        self.chassis = VComponent(npTruckMdl, npBody)
        
        self.wheels = []
        
        for i in range(0, 4):
            pos = self.chassis.getPos()
            
            if i == 0:
                pos += (-.85, 1.8, -1.2)
            if i == 1:
                pos += (.85, 1.8, -1.2)
            if i == 2:
                pos += (-.85, -1.5, -1.2)
            if i == 3:
                pos += (.85, -1.5, -1.2)
            
            # Prepare bullet nodes
            npBody = render.attachNewNode(BulletRigidBodyNode('wheelBox')) 
            npBody.node().addShape(BulletCylinderShape(.45, .35, XUp))
            npBody.node().setMass(25.0)
            npBody.setPos(pos)
            self.world.attachRigidBody(npBody.node())
            debug = BulletDebugNode('wheelDebug')
            debug.setVerbose(True)
            npBody.attachNewNode(debug).show()
            self.world.setDebugNode(debug)
            
            npWheelMdl = npBody.attachNewNode(loader.loadModel(wheelmesh).node())
            npWheelMdl.setRenderModeWireframe()
            
            if i % 2 == 0:
                npWheelMdl.setH(180.0) # We need to turn around the meshes of wheel 0 and 2, the left ones
            
            # Setup the suspension
            anchor = pos
            if i % 2 == 0:
                anchor = pos + (0.175, 0, 0) # We want the anchor at the inside of the wheel, not in the center
            else:
                anchor = pos - (0.175, 0, 0)
            
            self.wheels.append(VWheel(npWheelMdl, npBody))
        
        # Construct the front axle
        npAx1 = render.attachNewNode(BulletRigidBodyNode("axle1"))
        npAx1.node().addShape(BulletBoxShape(Vec3(0.5, 0.1, 0.1)))
        npAx1.node().setMass(30.0*SCALE)
        npAx1.setPos(pos + (0, 1.9, -1.1))
        self.world.attachRigidBody(npAx1.node())
        
        dbgAx1 = BulletDebugNode("axle1")
        dbgAx1.setVerbose(True)
        npAx1.attachNewNode(dbgAx1).show()
        self.world.setDebugNode(dbgAx1)
        
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
        self.chassis.update()
        for wheel in self.wheels:
            wheel.update()
        
        if self._accel:
            self.wheels[2].accel(300.0)
            self.wheels[3].accel(300.0)
        
        if self._brake:
            self.wheels[2].brake(800.0)
            self.wheels[3].brake(800.0)
        
        if self._steer != 0:
            self.wheels[0].steer(self._steer, 500.0) # steer == -1 for left
            self.wheels[1].steer(self._steer, 500.0) # steer ==  1 for right
        else:
            # steer straight
            self.wheels[0].center()
            self.wheels[1].center()
        
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
    
    def brake(self):
        self._brake = True
    
    def steerLeft(self):
        self._steer = -1
    
    def steerRight(self):
        self._steer = 1
        
    def getChassisNp(self):
        return self.chassis.getNp()
    def getChassis(self):
        return self.chassis
