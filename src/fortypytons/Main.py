# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

from Truck import Truck
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import DirectButton
from direct.directtools.DirectGeometry import LineNodePath
from panda3d.core import *
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup, OdeBallJoint, OdeHinge2Joint
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom, OdeCylinderGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat
import math


#SCALE = 10e-3
#SCALE = (10e-2)*2
SCALE = 1.0

class Main(ShowBase):
    trucks = []
    maskTrucks = BitMask32.bit(1)
    maskWheel = BitMask32.bit(2)
    camPos = Point3(8, -7, 3) # Good for egg truck
    #self.camPos = Point3(12, 2.5, 3)
    #self.camPos = Point3(20, -30, 8) # overview
    datadir = "../../data/"
    accel, brake, left, right = False, False, False, False
    
    def __init__(self):
        ShowBase.__init__(self)

        # Initialize ODE
        # Setup our physics world
        self.world = OdeWorld()
        self.world.setGravity(0, 0, -9.81*SCALE)
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
                                      scale = .05, pos = (Point3(0, 0, -.2) + guiOffset), command = self.zMinus)
        
        # keyboard hooks
        self.accept('arrow_up', self.arrowKeys, ["arrow_up", True])
        self.accept('arrow_down', self.arrowKeys, ["arrow_down", True])
        self.accept('arrow_left', self.arrowKeys, ["arrow_left", True])
        self.accept('arrow_right', self.arrowKeys, ["arrow_right", True])
        self.accept('arrow_up-up', self.arrowKeys, ["arrow_up", False])
        self.accept('arrow_down-up', self.arrowKeys, ["arrow_down", False])
        self.accept('arrow_left-up', self.arrowKeys, ["arrow_left", False])
        self.accept('arrow_right-up', self.arrowKeys, ["arrow_right", False])
        
        # register the render task for ODE updating
        self.taskMgr.doMethodLater(0.1, self.renderTask, "renderTask")
        
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
        
        # Generate it.
        self.terrain.generate()
        
        self.trucks.append(Truck(self.datadir + "mesh/kipper.egg",
                                 self.datadir + "mesh/rad.egg",
                                 Point3(0, 0, 3), SCALE, self.maskTrucks,
                                 self.world, self.space))
        
        # Mesh für kollision nehmen?
        #self.das_block = render.attachNewNode(loader.loadModel(self.datadir + "chassismesh/das_block.X").node())
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
 
    def renderTask(self, task):
        """ Do stuff. """
        self.camera.setPos(self.camPos)
        self.camera.lookAt(self.trucks[0].getChassisNp()) # Look at the most recently loaded truck
        #self.camera.lookAt(self.das_block)
        
        self.terrain.update()
        
        # Update object positions
        self.space.autoCollide() # Setup the contact joints
        self.world.step(globalClock.getDt()*SCALE)
        self.contactgroup.empty()
        
        for truck in self.trucks:
            truck.update()
        
        # Apply forces to the truck
        if self.accel:
            self.trucks[0].accel()
        if self.brake:
            self.trucks[0].brake()
        if self.right:
            self.trucks[0].steerRight()
        if self.left:
            self.trucks[0].steerLeft()
        return Task.cont
    
    def drawLinesTask(self, task):
        """ Deprecated. Maybe we need this somewhere in the future """
        # Draws lines between the smiley and frowney.
        self.lines.reset()
        self.lines.drawLines([[(self.trucks[0][0].getX(), self.trucks[0][0].getY(), self.trucks[0][0].getZ()),
                              (5, 0, 5)],
                              [(5, 0, 5),
                              (self.trucks[1][0].getX(), self.trucks[1][0].getY(), self.trucks[1][0].getZ())]])
        self.lines.create()
        return Task.cont
        
    def arrowKeys(self, keyname, isPressed): # args = [keyname, isPressed]
        """ This should go into a separate class at some point. """
        if isPressed:
            if keyname == "arrow_up":
                self.accel = True
            if keyname == "arrow_down":
                self.brake = True
            if keyname == "arrow_left":
                self.left = True
            if keyname == "arrow_right":
                self.right = True
        else:
            if keyname == "arrow_up":
                self.accel = False
            if keyname == "arrow_down":
                self.brake = False
            if keyname == "arrow_left":
                self.left = False
            if keyname == "arrow_right":
                self.right = False

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
