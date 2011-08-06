# -*- coding: utf-8 -*-
'''
Created on 05.08.2011

@author: marcel
'''

import math

from WireGeom import WireGeom
from VComponent import *
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
            suspFr = OdeHinge2Joint(self.world)
            suspFr.attach(self.chassis.getBody(), frBody)
            suspFr.setAxis1(0,0,1)
            suspFr.setAxis2(1,0,0)
            suspFr.setAnchor(pos)
            
            if i < 2:
                suspFr.setParamLoStop(0, -math.pi/6) # Only the front wheels are able to turn
                suspFr.setParamHiStop(0, math.pi/6)
            else:
                suspFr.setParamLoStop(0, 0)
                suspFr.setParamHiStop(0, 0)
            
            self.wheels.append(VWheel(npWheelMdl, wire, frMass, frBody, frGeom, suspFr))
    
    def update(self):
        self.chassis.update()
        for wheel in self.wheels:
            wheel.update()
    
    def accel(self):
        self.chassis.addForce(0,1400,1550)
    
    def brake(self):
        self.chassis.addForce(0,-1800,1550)
    
    def getChassisNp(self):
        return self.chassis.getNp()
    def getChassis(self):
        return self.chassis