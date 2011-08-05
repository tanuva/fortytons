# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

from fortypytons.WireGeom import WireGeom
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
        # Set up the GeoMipTerrain
        self.terrain = GeoMipTerrain("terrain")
        self.terrain.setHeightfield("../../data/terrain.png")
         
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
        
        # Generate it.
        self.terrain.generate()
        
        self.taskMgr.add(self.renderTask, "renderTask")
        self.taskMgr.add(self.drawLinesTask, "drawLinesTask")
        
        self.setupTruck("truck", "../../data/mesh/kipper_v4.egg", Point3(.5, 2.5, 2))
        
        # Mesh für kollision nehmen?
        #self.das_block = render.attachNewNode(loader.loadModel("../../data/mesh/das_block.X").node())
        #self.das_block.setScale(0.01)
        #self.das_block.setPos(.5, 2.5, 2.5)
        
        # We need something to stop us from falling off into -infinity!
        cm = CardMaker("ground")
        cm.setFrame(-20, 20, -20, 20)
        ground = render.attachNewNode(cm.generate())
        #ground.setRenderModeWireframe()
        texture = Texture("grass")
        texture.read(Filename("../../data/mesh/vegetati.png"))
        texture.setWrapU(Texture.WMRepeat)
        texture.setWrapV(Texture.WMRepeat)
        ground.setTexture(texture)
        ground.setPos(0, 0, 0)
        ground.lookAt(0, 0, -1)
        groundGeom = OdePlaneGeom(self.space, Vec4(0, 0, 1, 0))
        groundGeom.setCollideBits(self.maskTrucks | self.maskWheel)
        groundGeom.setCategoryBits(BitMask32(0x00000002))
        

        
        # We are going to be drawing some lines between the anchor points and the joints
        self.lines = LineNodePath(parent = self.render, thickness = 3.0, colorVec = Vec4(1, 0, 0, 1))
 
    def renderTask(self, task):
        """ Do stuff. """
        self.camera.setPos(self.camPos)
        self.camera.lookAt(self.trucks[-1][0]) # Look at the most recently loaded truck
        #self.camera.lookAt(self.das_block)
        
        self.terrain.update()
        
        # Update object positions
        self.space.autoCollide() # Setup the contact joints
        self.world.step(globalClock.getDt()*SCALE)
        for np, body in self.trucks:
            np.setPosQuat(render, body.getPosition(), Quat(body.getQuaternion()))
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
        npTruckMdl.attachNewNode(WireGeom().generate('box', extents=(2, 5, 1.8)).node())
        
        self.trucks.append((npTruckMdl, tBody))
        
        #-----------------------------------
        # Let's try getting hold of a wheel
        npWheelMdl = self.render.attachNewNode(self.loader.loadModel("../../data/mesh/rad.egg").node())
        npWheelMdl.setPos(2.5, 0, 3)
        npWheelMdl.setRenderModeWireframe()
        wBody = OdeBody(self.world)
        wMass = OdeMass()
        wMass.setCylinderTotal(25*SCALE, 2, 0.45, 0.35) # mass, direction, radius, length
        wBody.setMass(wMass)
        wBody.setPosition(npWheelMdl.getPos(self.render))
        wBody.setQuaternion(npWheelMdl.getQuat(self.render))
        
        wGeom = OdeCylinderGeom(self.space, 0.45, 0.35)
        wGeom.setCollideBits(self.maskWheel)
        wGeom.setCategoryBits(BitMask32(0x00000001))
        wGeom.setBody(wBody)
        wire = npWheelMdl.attachNewNode(WireGeom().generate('cylinder', radius=0.45, length=0.35).node())
        npWheelMdl.setH(180.0)
        wire.setR(90.0)
        self.trucks.append((npWheelMdl, wBody))
        
        self.testj = OdeBallJoint(self.world)
        self.testj.attach(wBody, tBody)
        self.testj.setAnchor(5, 0, 5)
        #self.suspFr = OdeHinge2Joint(self.world)
        
        
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
    
if __name__ == '__main__':
    app = Main()
    app.run()
