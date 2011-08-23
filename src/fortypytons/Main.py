# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

from Truck import Truck
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import DirectButton, DirectLabel
from panda3d.core import *
from panda3d.bullet import *

#SCALE = 10e-3
#SCALE = (10e-2)*2
SCALE = 1.0

class Main(ShowBase):
    trucks = []
    maskTrucks = BitMask32.bit(1)
    maskWheel = BitMask32.bit(2)
    #camPos = Point3(8, -7, 3) # Good for egg truck
    camPos = Point3(13, -12, 3)
    #self.camPos = Point3(20, -30, 8) # overview
    datadir = "../../data/"
    accel, brake, left, right = False, False, False, False
    
    def __init__(self):
        ShowBase.__init__(self)
        base.setFrameRateMeter(True)
        
        # Set up our physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))
        
        # We need some gui
        guiOffset = Point3(.8, 0, .8)
        self.btnXplus = DirectButton(text = "X+", scale = .05, pos = (Point3(0, 0, 0) + guiOffset),
                                     command = self.xPlus)
        self.btnXminus = DirectButton(text = "X-", scale = .05, pos = (Point3(0, 0, -.1) + guiOffset),
                                      command = self.xMinus)
        self.btnYplus = DirectButton(text = "Y+", scale = .05, pos = (Point3(.1, 0, 0) + guiOffset),
                                     command = self.yPlus)
        self.btnYminus = DirectButton(text = "Y-", scale = .05, pos = (Point3(.1, 0, -.1) + guiOffset),
                                      command = self.yMinus)
        self.btnZplus = DirectButton(text = "Z+", scale = .05, pos = (Point3(.2, 0, 0) + guiOffset),
                                     command = self.zPlus)
        self.btnZminus = DirectButton(text = "Z-", scale = .05, pos = (Point3(.2, 0, -.1) + guiOffset),
                                      command = self.zMinus)
        self.btnDebug = DirectButton(text = "Debug", scale = .05, pos = (Point3(0, 0, -.2) + guiOffset),
                                     command = self.toggleDebug)
        self.btnReset = DirectButton(text = "Reset", scale = .05, pos = (Point3(.2, 0, -.2) + guiOffset),
                                     command = self.resetTruck)
        self.lblSpeedo = DirectLabel(text = "xxx", scale = .1, pos = Point3(1.2, 0, -.9))
        
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
        
        self.terBodyNp = render.attachNewNode(BulletRigidBodyNode("terrainBody"))
        img = PNMImage(Filename(self.datadir + "tex/inclined.png"))
        offset = img.getXSize() / 2.0 - 0.5 # Used for the GeoMipTerrain
        height = 10.0
        self.terBodyNp.node().addShape(BulletHeightfieldShape(img, height, ZUp))
        self.terBodyNp.node().setDebugEnabled(False)
        self.terBodyNp.setPos(0,0, height / 2.0)
        self.world.attachRigidBody(self.terBodyNp.node())
        
        # Set up the GeoMipTerrain
        self.terrain = GeoMipTerrain("terrainNode")
        self.terrain.setHeightfield(self.datadir + "tex/inclined.png")
        self.terrain.setBlockSize(32)
        self.terrain.setNear(20)
        self.terrain.setFar(100)
        self.terrain.setFocalPoint(base.camera)
        self.terrain.getRoot().reparentTo(self.terBodyNp)
        
        self.terrainNp = self.terrain.getRoot()
        self.terrainNp.setSz(height)
        self.terrainNp.setPos(-offset, -offset, -height / 2.0)
        self.terrainNp.setRenderModeWireframe()
        # Generate it.
        self.terrain.generate()
        
        # for testing
        """shpStand = BulletBoxShape(Vec3(0.5, 0.5, 1.0))
        stand = BulletRigidBodyNode('Box')
        stand.addShape(shpStand)
        npStand = render.attachNewNode(stand)
        npStand.setPos(0, 0, 1.0)
        self.world.attachRigidBody(npStand.node()) """

        self.debug = render.attachNewNode(BulletDebugNode('debug'))
        self.debug.node().showWireframe(True)
        self.debug.node().showConstraints(True)
        self.debug.node().showBoundingBoxes(False)
        self.debug.node().showNormals(False)
        self.world.setDebugNode(self.debug.node())
        self.debug.show()
        
        self.trucks.append(Truck(self.datadir + "mesh/kipper.egg",
                                 self.datadir + "mesh/rad.egg",
                                 Vec3(0, 0, 2.), SCALE, self.maskTrucks,
                                 self.world))

        # TESTING
        """npBox = render.attachNewNode(BulletRigidBodyNode('Box'))
        boxS = BulletBoxShape(Vec3(.5, .5, .5))
        npBox.node().addShape(boxS)
        npBox.node().setDeactivationEnabled(False)
        npBox.setPos(2, -4, 3)
        self.world.attachRigidBody(npBox.node())
        
        npbox2 = render.attachNewNode(BulletRigidBodyNode('Box2'))
        box2S = BulletBoxShape(Vec3(.5, .5, .5))
        npbox2.node().addShape(box2S)
        npbox2.node().setDeactivationEnabled(False)
        npbox2.node().setMass(5)
        npbox2.setPos(2, -4, 1)
        self.world.attachRigidBody(npbox2.node())
        
        t1 = TransformState.makePosHpr(Point3(0,0,0), Vec3(0,0,90))
        t2 = TransformState.makePosHpr(Point3(0,0,0), Vec3(0,0,0))
        con = BulletSliderConstraint(npBox.node(), npbox2.node(), t1, t2, True)
        con.setLowerLinearLimit(0.05)
        con.setUpperLinearLimit(3)
        con.setLowerAngularLimit(0)
        con.setUpperAngularLimit(0)
        con.setDebugDrawSize(2.0)
        #con.enableFeedback(True)
        self.world.attachConstraint(con)"""
 
    def renderTask(self, task):
        """ Do stuff. """
        self.camera.setPos(self.camPos)
        #self.camera.lookAt(0,0,0)
        self.camera.lookAt(self.trucks[0].getChassisNp()) # Look at first loaded truck
        
        self.terrain.update()

        # Update object positions
        self.world.doPhysics(globalClock.getDt()*SCALE)
        # Update the truck's speedometer
        self.lblSpeedo["text"] = "%i" % self.trucks[0].getSpeed()
        
        # Apply forces to the truck
        if len(self.trucks) > 0:
            self.trucks[0].update(globalClock.getDt())

        return Task.cont
        
    def arrowKeys(self, keyname, isPressed): # args = [keyname, isPressed]
        """ This should go into a separate class at some point. """
        if isPressed:
            if keyname == "arrow_up":
                self.trucks[0].accel()
            if keyname == "arrow_down":
                self.trucks[0].brake()
            if keyname == "arrow_left":
                self.trucks[0].steerLeft()
            if keyname == "arrow_right":
                self.trucks[0].steerRight()
        else:
            if keyname == "arrow_up":
                self.trucks[0].neutral()
            if keyname == "arrow_down":
                self.trucks[0].neutral()
            if keyname == "arrow_left":
                self.trucks[0].steerStraight()
            if keyname == "arrow_right":
                self.trucks[0].steerStraight()

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

    def toggleDebug(self):
        if self.debug.isHidden():
            self.debug.show()
        else:
            self.debug.hide()

    def resetTruck(self):
        self.trucks[0].reset()
    
if __name__ == '__main__':
    app = Main()
    app.run()
