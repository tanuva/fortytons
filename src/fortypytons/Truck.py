# -*- coding: utf-8 -*-
'''
Created on 05.08.2011

@author: marcel
'''

import math

from WireGeom import WireGeom
from VComponent import *
from direct.directtools.DirectGeometry import LineNodePath
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdeBallJoint, OdeHinge2Joint
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom, OdeCylinderGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat

class Truck:
    '''
    The player truck.
    '''

    def __init__(self, chassismesh, wheelmesh, pos, SCALE, maskTrucks, world, space):
        '''
        Loads the chassismesh, sets the truck up and ignites the engine.
        '''
        
        self._steer = 0
        self._accel = False
        self._brake = False
        self.world = world
        self.space = space
        
        # eggmesh: center-side 1m, center-front 2.5m, center-top 1.7m, height exhaust: 0.1m
        #npTruckCol.node().addSolid(CollisionBox(Point3(0,0,0), 1, 2.5, 1.7/2))
        #npTruckCol.setZ(-.1) # Compensate for exhausts sticking out
        
        # Load the chassismesh
        npTruckMdl = render.attachNewNode(loader.loadModel(chassismesh).node())
        npTruckMdl.setPos(pos)
        npTruckMdl.setRenderModeWireframe()
        
        # Make us visible
        wire = render.attachNewNode(WireGeom().generate('box', extents=(2, 5, 1.8)).node())
                
        # Create the body and set the mass
        body = OdeBody(self.world)
        mass = OdeMass()
        mass.setBoxTotal(1500*SCALE, 2, 5, 1.8)
        body.setMass(mass)
        body.setPosition(npTruckMdl.getPos(render))
        body.setQuaternion(npTruckMdl.getQuat(render))

        # Create a BoxGeom
        geom = OdeBoxGeom(self.space, 2, 5, 1.8)
        geom.setCollideBits(maskTrucks)
        geom.setCategoryBits(BitMask32(0x00000001))
        geom.setBody(body)
        
        self.chassis = VComponent(npTruckMdl, wire, mass, body, geom)
        
        self.wheels = []
        
        for i in range(0, 4):
            pos = self.chassis.getNp().getPos()
            
            if i == 0:
                pos += (-.85, 1.8, -1.2)
            if i == 1:
                pos += (.85, 1.8, -1.2)
            if i == 2:
                pos += (-.85, -1.5, -1.2)
            if i == 3:
                pos += (.85, -1.5, -1.2)
            
            # Make the chassismesh ready for showtime
            npWheelMdl = render.attachNewNode(loader.loadModel(wheelmesh).node())
            npWheelMdl.setPos(pos)
            npWheelMdl.setRenderModeWireframe()
            npWheelMdl.setR(90.0)
            
            if i % 2 == 0:
                npWheelMdl.setH(180.0) # We need to turn around the meshes of wheel 0 and 2, the left ones
            
            # Add a helper object to be able to see the physics happening
            wire = render.attachNewNode(WireGeom().generate('cylinder', radius=0.45, length=0.35).node())
            
            # Prepare ODE body, mass and geom
            frBody = OdeBody(self.world)
            frMass = OdeMass()
            frMass.setCylinderTotal(25*SCALE, 2, 0.45, 0.35) # mass, direction, radius, length
            frBody.setMass(frMass)
            frBody.setPosition(npWheelMdl.getPos(render))
            frBody.setQuaternion(npWheelMdl.getQuat(render))
            frGeom = OdeCylinderGeom(self.space, 0.45, 0.35)
            frGeom.setCollideBits(maskTrucks)
            frGeom.setCategoryBits(BitMask32(0x00000001))
            frGeom.setBody(frBody)
            
            
            # Setup the suspension
            anchor = pos
            if i % 2 == 0:
                anchor = pos + (0.175, 0, 0) # We want the anchor at the inside of the wheel, not in the center
            else:
                anchor = pos - (0.175, 0, 0)
            
            suspFr = OdeHinge2Joint(self.world)
            suspFr.attach(self.chassis.getBody(), frBody)
            suspFr.setAxis1(0,0,1)
            suspFr.setAxis2(1,0,0)
            suspFr.setAnchor(anchor)
            #suspFr.setParamSuspensionERP(0, 0.999)
            #suspFr.setParamSuspensionCFM(0, 1000)
            
            if i < 2:
                suspFr.setParamLoStop(0, -math.pi/6) # Only the front wheels are able to turn
                suspFr.setParamHiStop(0, math.pi/6)
            else:
                suspFr.setParamLoStop(0, 0)
                suspFr.setParamHiStop(0, 0)
            
            self.wheels.append(VWheel(npWheelMdl, wire, frMass, frBody, frGeom, suspFr))
        
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