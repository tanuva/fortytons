# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

import math

from WireGeom import WireGeom
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import DirectButton
from direct.directtools.DirectGeometry import LineNodePath
from panda3d.core import *
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdeBallJoint, OdeHinge2Joint
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom, OdeCylinderGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat


#SCALE = 10e-3
SCALE = (10e-2)*2

class Main(ShowBase):
    trucks = []
    maskTrucks = BitMask32.bit(1)
    maskWheel = BitMask32.bit(2)
    camPos = Point3(8, -7, 3) # Good for egg truck
    #self.camPos = Point3(12, 2.5, 3)
    #self.camPos = Point3(20, -30, 8) # overview
    datadir = "../../data/"
    
    def __init__(self):
        ShowBase.__init__(self)

        # Initialize ODE
        # Setup our physics world
        self.world = OdeWorld()
        self.world.setGravity(0, 0, -9.81)
        # The surface table is needed for autoCollide
        self.world.initSurfaceTable(1)
        self.world.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
         
        # Create a space and add a contactgroup to it to add the contact joints
        self.space = OdeSimpleSpace()
        self.space.setAutoCollideWorld(self.world)
        self.contactgroup = OdeJointGroup()
        self.space.setAutoCollideJointGroup(self.contactgroup)
        
        # We need some gui
        guiOffset = Point3(.8, 0, .8)
        self.btnXplus = DirectButton(text = "X+",
                                     scale = .05, pos = (Point3(0, 0, 0) + guiOffset), command = self.xPlus)
        self.btnXminus = DirectButton(text = "X-",
                                      scale = .05, pos = (Point3(0, 0, -.1) + guiOffset), command = self.xMinus)
        self.btnYplus = DirectButton(text = "Y+",
                                     scale = .05, pos = (Point3(.1, 0, 0) + guiOffset), command = self.yPlus)
        self.btnYminus = DirectButton(text = "Y-",
                                      scale = .05, pos = (Point3(.1, 0, -.1) + guiOffset), command = self.yMinus)
        self.btnZplus = DirectButton(text = "Z+",
                                     scale = .05, pos = (Point3(.2, 0, 0) + guiOffset), command = self.zPlus)
        self.btnZminus = DirectButton(text = "Z-",        
                                      scale = .05, pos = (Point3(.2, 0, -.1) + guiOffset), command = self.zMinus)
        self.btnAccel = DirectButton(text = "Accel",        
                                      scale = .05, pos = (Point3(0, 0, -.2) + guiOffset), command = self.accel)
        
        # Set up the GeoMipTerrain
        self.terrain = GeoMipTerrain("terrain")
        self.terrain.setHeightfield(self.datadir + "tex/terrain.png")
         
        # Set terrain properties
        self.terrain.setBlockSize(32)
        self.terrain.setNear(20)
        self.terrain.setFar(100)
        self.terrain.setFocalPoint(base.camera)
        
        self.terrainNp = self.terrain.getRoot()
        self.terrainNp.reparentTo(render)
        self.terrainNp.setSz(5)
        self.terrainNp.setPos(-128, -128, 0)
        self.terrainNp.setRenderModeWireframe()
        
        test = render.attachNewNode(loader.loadModel(self.datadir + "mesh/rad.egg").node())
        test.setRenderModeWireframe()
        test.setPos(3,0,2)
        
        # Generate it.
        self.terrain.generate()
        
        self.taskMgr.add(self.renderTask, "renderTask")
        #self.taskMgr.add(self.drawLinesTask, "drawLinesTask")
        
        self.setupTruck("truck", self.datadir + "mesh/kipper.egg", Point3(0, 0, 3))
        
        # Mesh für kollision nehmen?
        #self.das_block = render.attachNewNode(loader.loadModel(self.datadir + "mesh/das_block.X").node())
        #self.das_block.setScale(0.01)
        #self.das_block.setPos(.5, 2.5, 2.5)
        
        # We need something to stop us from falling off into -infinity!
        cm = CardMaker("ground")
        cm.setFrame(-20, 20, -20, 20)
        ground = render.attachNewNode(cm.generate())
        #ground.setRenderModeWireframe()
        texture = Texture("grass")
        texture.read(Filename(self.datadir + "tex/vegetati.png"))
        texture.setWrapU(Texture.WMRepeat)
        texture.setWrapV(Texture.WMRepeat)
        ground.setTexture(texture)
        ground.setPos(0, 0, 0)
        ground.lookAt(0, 0, -1)
        groundGeom = OdePlaneGeom(self.space, Vec4(0, 0, 1, 0))
        groundGeom.setCollideBits(self.maskTrucks | self.maskWheel)
        groundGeom.setCategoryBits(BitMask32(0x00000002))
        
        self.accel = False
        
        # We are going to be drawing some lines between the anchor points and the joints
        self.lines = LineNodePath(parent = self.render, thickness = 3.0, colorVec = Vec4(1, 0, 0, 1))
 
    def renderTask(self, task):
        """ Do stuff. """
        self.camera.setPos(self.camPos)
        self.camera.lookAt(self.trucks[0][0]) # Look at the most recently loaded truck
        #self.camera.lookAt(self.das_block)
        
        self.terrain.update()
        
        # Update object positions
        if self.accel:
            self.trucks[0][1].addForce(0,200,0)
        self.space.autoCollide() # Setup the contact joints
        self.world.step(globalClock.getDt()*SCALE)
        for np, body, wire in self.trucks:
            np.setPosQuat(body.getPosition(), Quat(body.getQuaternion()))
            wire.setPosQuat(body.getPosition(), Quat(body.getQuaternion()))
            #wire.setPos(body.getPosition())
            
            if body == self.trucks[0][1]:
                np.setZ(np.getZ()+0.1) # fix the geom/model offset temporarily
        self.contactgroup.empty()
        return Task.cont
    
    def drawLinesTask(self, task):
        # Draws lines between the smiley and frowney.
        self.lines.reset()
        self.lines.drawLines([[(self.trucks[0][0].getX(), self.trucks[0][0].getY(), self.trucks[0][0].getZ()),
                              (5, 0, 5)],
                              [(5, 0, 5),
                              (self.trucks[1][0].getX(), self.trucks[1][0].getY(), self.trucks[1][0].getZ())]])
        self.lines.create()
        return Task.cont
    
    def setupTruck(self, name, mesh, pos):
        """ Loads mesh and sets it up. Very specific for now. """
        
        npTruckMdl = self.render.attachNewNode(loader.loadModel(mesh).node())
        npTruckMdl.setPos(pos)
        npTruckMdl.setRenderModeWireframe()        
        # eggmesh: center-side 1m, center-front 2.5m, center-top 1.7m, height exhaust: 0.1m
        #npTruckCol.node().addSolid(CollisionBox(Point3(0,0,0), 1, 2.5, 1.7/2))
        #npTruckCol.setZ(-.1) # Compensate for exhausts sticking out
        
        # Create the body and set the mass
        tBody = OdeBody(self.world)
        tMass = OdeMass()
        tMass.setBoxTotal(1500*SCALE, 2, 5, 1.8)
        tBody.setMass(tMass)
        tBody.setPosition(npTruckMdl.getPos(self.render))
        tBody.setQuaternion(npTruckMdl.getQuat(self.render))
        # Create a BoxGeom
        tGeom = OdeBoxGeom(self.space, 2, 5, 1.8)
        tGeom.setCollideBits(self.maskTrucks)
        tGeom.setCategoryBits(BitMask32(0x00000001))
        tGeom.setBody(tBody)
        # Make us visible
        wire = render.attachNewNode(WireGeom().generate('box', extents=(2, 5, 1.8)).node())
        
        self.trucks.append((npTruckMdl, tBody, wire))
        
        #-----------------------------------
        # Let's try getting hold of a wheel
        npWheelMdl = self.render.attachNewNode(self.loader.loadModel(self.datadir + "mesh/rad.egg").node())
        npWheelMdl.setPos(.85, 1.8, 1.9)
        npWheelMdl.setR(90.0)
        #npWheelMdl.setH(180.0)
        npWheelMdl.setRenderModeWireframe()
        frBody = OdeBody(self.world)
        frMass = OdeMass()
        frMass.setCylinderTotal(25*SCALE, 2, 0.45, 0.35) # mass, direction, radius, length
        frBody.setMass(frMass)
        frBody.setPosition(npWheelMdl.getPos(self.render))
        frBody.setQuaternion(npWheelMdl.getQuat(self.render))
        
        frGeom = OdeCylinderGeom(self.space, 0.45, 0.35)
        frGeom.setCollideBits(self.maskTrucks)
        frGeom.setCategoryBits(BitMask32(0x00000001))
        frGeom.setBody(frBody)
        wire = render.attachNewNode(WireGeom().generate('cylinder', radius=0.45, length=0.35).node())
        self.trucks.append((npWheelMdl, frBody, wire))
        
        self.suspFr = OdeHinge2Joint(self.world)
        self.suspFr.attach(tBody, frBody)
        self.suspFr.setParamLoStop(0, -math.pi/8)
        self.suspFr.setParamHiStop(0, math.pi/8)
        self.suspFr.setAxis1(0,0,1)
        self.suspFr.setAxis2(1,0,0)
        self.suspFr.setAnchor(.85, 1.8, 1.9)
        
        #---------------------------------
        # And another wheel
        npWheelMdl = self.render.attachNewNode(self.loader.loadModel(self.datadir + "mesh/rad.egg").node())
        npWheelMdl.setPos(-.85, 1.5, 1.9)
        npWheelMdl.setR(90.0)
        npWheelMdl.setH(180.0)
        npWheelMdl.setRenderModeWireframe()
        flBody = OdeBody(self.world)
        flMass = OdeMass()
        flMass.setCylinderTotal(25*SCALE, 2, 0.45, 0.35) # mass, direction, radius, length
        flBody.setMass(flMass)
        flBody.setPosition(npWheelMdl.getPos(self.render))
        flBody.setQuaternion(npWheelMdl.getQuat(self.render))
        
        flGeom = OdeCylinderGeom(self.space, 0.45, 0.35)
        flGeom.setCollideBits(self.maskTrucks)
        flGeom.setCategoryBits(BitMask32(0x00000001))
        flGeom.setBody(flBody)
        wire = render.attachNewNode(WireGeom().generate('cylinder', radius=0.45, length=0.35).node())
        self.trucks.append((npWheelMdl, flBody, wire))
        
        self.suspFl = OdeHinge2Joint(self.world)
        self.suspFl.attach(tBody, flBody)
        self.suspFl.setAxis1(0,0,1)
        self.suspFl.setAxis2(1,0,0)
        self.suspFl.setParamLoStop(0, -math.pi/8)
        self.suspFl.setParamHiStop(0, math.pi/8)
        self.suspFl.setAnchor(-.85, 1.5, 1.9)
        
        #---------------------------------
        # And another wheel
        npWheelMdl = self.render.attachNewNode(self.loader.loadModel(self.datadir + "mesh/rad.egg").node())
        npWheelMdl.setPos(.85, -1.5, 1.9)
        npWheelMdl.setR(90.0)
        npWheelMdl.setRenderModeWireframe()
        rrBody = OdeBody(self.world)
        rrMass = OdeMass()
        rrMass.setCylinderTotal(25*SCALE, 2, 0.45, 0.35) # mass, direction, radius, length
        rrBody.setMass(rrMass)
        rrBody.setPosition(npWheelMdl.getPos(self.render))
        rrBody.setQuaternion(npWheelMdl.getQuat(self.render))
        
        rrGeom = OdeCylinderGeom(self.space, 0.45, 0.35)
        rrGeom.setCollideBits(self.maskTrucks)
        rrGeom.setCategoryBits(BitMask32(0x00000001))
        rrGeom.setBody(rrBody)
        wire = render.attachNewNode(WireGeom().generate('cylinder', radius=0.45, length=0.35).node())
        self.trucks.append((npWheelMdl, rrBody, wire))
        
        self.suspRr = OdeHinge2Joint(self.world)
        self.suspRr.attach(tBody, rrBody)
        self.suspRr.setAxis1(0,0,1)
        self.suspRr.setAxis2(1,0,0)
        self.suspRr.setParamLoStop(0, 0)
        self.suspRr.setParamHiStop(0, 0)
        self.suspRr.setAnchor(.85, -1.5, 1.9)
        
        #---------------------------------
        # And another wheel
        npWheelMdl = self.render.attachNewNode(self.loader.loadModel(self.datadir + "mesh/rad.egg").node())
        npWheelMdl.setPos(-.85, -1.5, 1.9)
        npWheelMdl.setR(90.0)
        npWheelMdl.setH(180.0)
        npWheelMdl.setRenderModeWireframe()
        rlBody = OdeBody(self.world)
        rlMass = OdeMass()
        rlMass.setCylinderTotal(25*SCALE, 2, 0.45, 0.35) # mass, direction, radius, length
        rlBody.setMass(rlMass)
        rlBody.setPosition(npWheelMdl.getPos(self.render))
        rlBody.setQuaternion(npWheelMdl.getQuat(self.render))
        
        rlGeom = OdeCylinderGeom(self.space, 0.45, 0.35)
        rlGeom.setCollideBits(self.maskTrucks)
        rlGeom.setCategoryBits(BitMask32(0x00000001))
        rlGeom.setBody(rlBody)
        wire = render.attachNewNode(WireGeom().generate('cylinder', radius=0.45, length=0.35).node())
        self.trucks.append((npWheelMdl, rlBody, wire))
        
        self.suspRl = OdeHinge2Joint(self.world)
        self.suspRl.attach(tBody, rlBody)
        self.suspRl.setAxis1(0,0,1)
        self.suspRl.setAxis2(1,0,0)
        self.suspRl.setParamLoStop(0, 0)
        self.suspRl.setParamHiStop(0, 0)
        self.suspRl.setAnchor(-.85, -1.5, 1.9)
        
    def xPlus(self):
        self.camPos.setX(self.camPos.getX()+1.0)
    def yPlus(self):
        self.camPos.setY(self.camPos.getY()+1.0)
    def xMinus(self):
        self.camPos.setX(self.camPos.getX()-1.0)
    def yMinus(self):
        self.camPos.setY(self.camPos.getY()-1.0)
    def zPlus(self):
        self.camPos.setZ(self.camPos.getZ()+1.0)
    def zMinus(self):
        self.camPos.setZ(self.camPos.getZ()-1.0)
    def accel(self):
        if self.accel: self.accel = False
        else: self.accel = True
        print self.accel
    
if __name__ == '__main__':
    app = Main()
    app.run()
