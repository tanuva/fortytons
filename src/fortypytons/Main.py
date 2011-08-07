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
from panda3d.bullet import BulletWorld, BulletPlaneShape, BulletRigidBodyNode, BulletBoxShape, BulletDebugNode

#SCALE = 10e-3
SCALE = (10e-2)*2
#SCALE = 1.0

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
        
        # Set up our physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        
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
        self.terrain.setBlockSize(32)
        self.terrain.setNear(20)
        self.terrain.setFar(100)
        self.terrain.setFocalPoint(base.camera)
        
        self.terrainNp = self.terrain.getRoot()
        self.terrainNp.reparentTo(render)
        self.terrainNp.setSz(5)
        self.terrainNp.setPos(-128, -128, 0)
        self.terrainNp.setRenderModeWireframe()
        self.terrainNp.hide()
        # Generate it.
        self.terrain.generate()
        
        self.trucks.append(Truck(self.datadir + "mesh/kipper.egg",
                                 self.datadir + "mesh/rad.egg",
                                 Vec3(0, 0, 3), SCALE, self.maskTrucks,
                                 self.world))
        
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
        
        shpGround = BulletPlaneShape(Vec3(0, 0, 1), 0)
        npGround = BulletRigidBodyNode('Ground')
        npGround.addShape(shpGround)
        npGround = render.attachNewNode(npGround)
        npGround.setPos(0, 0, 0)
        self.world.attachRigidBody(npGround.node())
        
        # for testing
        shpStand = BulletBoxShape(Vec3(0.5, 0.5, 0.5))
        stand = BulletRigidBodyNode('Box')
        stand.addShape(shpStand)
        npStand = render.attachNewNode(stand)
        npStand.setPos(0, 0, 0.5)
        self.world.attachRigidBody(npStand.node())
        dbgStand = BulletDebugNode('Debug')
        dbgStand.setVerbose(False)
        npDbgStand = render.attachNewNode(dbgStand)
        npDbgStand.show()
        self.world.setDebugNode(dbgStand)
 
    def renderTask(self, task):
        """ Do stuff. """
        self.camera.setPos(self.camPos)
        self.camera.lookAt(0,0,0)
        #self.camera.lookAt(self.trucks[0].getChassisNp()) # Look at the most recently loaded truck
        #self.camera.lookAt(self.das_block)
        
        self.terrain.update()
        
        # Update object positions
        self.world.doPhysics(globalClock.getDt()*SCALE)
        
        # Apply forces to the truck
        if len(self.trucks) > 0:
            if self.accel:
                self.trucks[0].accel()
            if self.brake:
                self.trucks[0].brake()
            if self.right:
                self.trucks[0].steerRight()
            if self.left:
                self.trucks[0].steerLeft()
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
