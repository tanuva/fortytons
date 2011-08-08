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
        npBody.node().addShape(BulletBoxShape(Vec3(1, 2.5, 1.8/2.0)))
        npBody.node().setMass(1500.0)
        npBody.setPos(pos)
        self.world.attachRigidBody(npBody.node())
        debug = BulletDebugNode('truckDebug')
        debug.setVerbose(True)
        render.attachNewNode(debug).show()
        self.world.setDebugNode(debug)
        
        npTruckMdl = npBody.attachNewNode(loader.loadModel(chassismesh).node())
        npTruckMdl.setRenderModeWireframe()
        
        self.chassis = VComponent(npTruckMdl, npBody)
        
        self.wheels = []
        
        for i in range(0, 4):
            pos = self.chassis.getPos()
            print pos
            
            if i == 0:
                pos += (-.85, 1.8, -1.2)
            if i == 1:
                pos += (.85, 1.8, -1.2)
            if i == 2:
                pos += (-.85, -1.5, -1.2)
            if i == 3:
                pos += (.85, -1.5, -1.2)
            
            # Make the chassismesh ready for showtime
            
            
            
            
            # Prepare bullet nodes
            npBody = render.attachNewNode(BulletRigidBodyNode('wheelBox')) 
            npBody.node().addShape(BulletCylinderShape(.45, .35, XUp))
            npBody.node().setMass(25.0)
            npBody.setPos(pos)
            self.world.attachRigidBody(npBody.node())
            debug = BulletDebugNode('wheelDebug')
            debug.setVerbose(True)
            render.attachNewNode(debug).show()
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
        
        # We are going to be drawing some lines between the anchor points and the joints
        self.lines = LineNodePath(parent = render, thickness = 3.0, colorVec = Vec4(1, 0, 0, 1))
    
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