# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

from Truck import Truck
from CameraController import *
from KeyConfig import KeyConfig
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.gui.DirectGui import DirectButton, DirectLabel, DirectSlider
from panda3d.core import *
from panda3d.bullet import *
from pandac.PandaModules import WindowProperties

#SCALE = 10e-3
#SCALE = (10e-2)*2
SCALE = 1.0

class Main(ShowBase):
    trucks = []
    maskTrucks = BitMask32.bit(1)
    maskWheel = BitMask32.bit(2)
    datadir = "../../data/"
    accel, brake, left, right = False, False, False, False

    def __init__(self):
        ShowBase.__init__(self)
        base.setFrameRateMeter(True)
        base.disableMouse() # Dragging the mouse will make strange things happen otherwise
        # Hide the cursor
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        # Enable anti aliasing
        render.setAntialias(AntialiasAttrib.MAuto)

        # Set up our physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))

        # We need some gui
        self.lblSpeedo = DirectLabel(text = "xxx", scale = .1, pos = Point3(1.2, 0, -.9))
        self.lblGearState = DirectLabel(text = "xxx", scale = .1, pos = Point3(1.2, 0, -.97))
        self.lblGear = DirectLabel(text = "xxx", scale = .1, pos = Point3(1., 0, -.97))
        self.lblRpmSlider = DirectSlider(scale = .5, pos = Point3(1, 0, -.8), range=(0,3000), value=0, pageSize=0)

        self.accept("f9", self.toggleDebug)
        self.accept("f10", base.toggleWireframe)
        self.accept("f11", base.toggleTexture)
        self.accept("f12", base.screenshot, ["40tons"])

        # render in wireframe by default for now
        #base.toggleWireframe()

        # Enable shad(er|ow) generation
        render.setShaderAuto()

        # Let there be light!
        plight = PointLight('plight')
        plight.setColor(VBase4(0.95, 0.95, 1., 1.))
        plight.setShadowCaster(True, 512, 512)
        plnp = render.attachNewNode(plight)
        plnp.setPos(10, -20, 100)
        render.setLight(plnp)

        amblight = AmbientLight('amblight')
        amblight.setColor(VBase4(0.4, 0.4, 0.4, 1))
        amblightNp = render.attachNewNode(amblight)
        render.setLight(amblightNp)

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
        self.terrain.setBlockSize(128)
        #self.terrain.setNear(20)
        #self.terrain.setFar(200)
        #self.terrain.setFocalPoint(base.camera)
        self.terrain.setBruteforce(True)
        self.terrain.getRoot().reparentTo(self.terBodyNp)

        self.terrainNp = self.terrain.getRoot()
        self.terrainNp.setSz(height)
        self.terrainNp.setPos(-offset, -offset, -height / 2.0)
        # Generate it.
        self.terrain.generate()

        # Paint it
        terTex = loader.loadTexture(self.datadir + "tex/vegetati.png")
        terTex.setAnisotropicDegree(2)
        self.terrainNp.setTexture(terTex)
        self.terrainNp.setTexScale(TextureStage.getDefault(), 16., 16.)

        # Build our bridge
        p0 = Point3(-11, -6.5, 3.5 - height/2.)
        p2 = Point3(-8.5,  -6.5, 3.5 - height/2.)
        p1 = Point3(-10.5,7.5, 3.5 - height/2.)
        p3 = Point3(-7,   7.5, 3.5 - height/2.)
        mesh = BulletTriangleMesh()
        mesh.addTriangle(p0, p1, p2)
        mesh.addTriangle(p1, p2, p3)
        self.bridgeNp = self.terBodyNp.attachNewNode(BulletRigidBodyNode("bridgeBody"))
        self.bridgeNp.node().addShape(BulletTriangleMeshShape(mesh, dynamic=False))
        self.world.attachRigidBody(self.bridgeNp.node())

        # Configure the debug node
        self.debug = render.attachNewNode(BulletDebugNode('debug'))
        self.debug.node().showWireframe(True)
        self.debug.node().showConstraints(True)
        self.debug.node().showBoundingBoxes(False)
        self.debug.node().showNormals(False)
        self.world.setDebugNode(self.debug.node())
        #self.debug.show()

        self.trucks.append(Truck(self.datadir + "mesh/truck.egg",
                                 self.datadir + "mesh/wheel.egg",
                                 Vec3(0, 0, 2.), SCALE, self.maskTrucks,
                                 self.world))

        # Register truck functions
        # Truck should do this by itself! (or advertise keys it wants to use? better approach...)
        self.keyconf = KeyConfig(self)
        self.keyconf.loadConfig("neo2.conf")
        self.keyconf.setHook("gas", self.trucks[0].setGas, [1.], [0.])
        self.keyconf.setHook("brake", self.trucks[0].setBrake, [1.], [0.])
        self.keyconf.setHook("steerLeft", self.trucks[0].steer, [1], [0])
        self.keyconf.setHook("steerRight", self.trucks[0].steer, [-1], [0])
        self.keyconf.setHook("dumperUp", self.trucks[0].tiltDumper, [1.], [0.])
        self.keyconf.setHook("dumperDown", self.trucks[0].tiltDumper, [-1.], [0.])
        self.keyconf.setHook("reset", self.trucks[0].reset)
        self.keyconf.setHook("shiftPark", self.trucks[0].shiftPark)
        self.keyconf.setHook("shiftReverse", self.trucks[0].shiftReverse)
        self.keyconf.setHook("shiftNeutral", self.trucks[0].shiftNeutral)
        self.keyconf.setHook("shiftDrive", self.trucks[0].shiftDrive)

        self.camcon = ManualCameraController(self.world, self.camera, self.trucks[0].getChassis().getBody())
        taskMgr.add(self.camcon.update, 'CameraController', priority=10)
        self.accept("wheel_up", self.camcon.mwheelup)
        self.accept("wheel_down", self.camcon.mwheeldown)

        # register the physics update task
        self.taskMgr.doMethodLater(1./60., self.physicsTask, "physicsTask", priority=5)
        # register the render task
        self.taskMgr.doMethodLater(0.1, self.renderTask, "renderTask", priority=9)

    def physicsTask(self, task):
        # We do 5 substeps per task frame, amount chosen by fair dice roll ;)
        self.world.doPhysics(task.delayTime, 10, task.delayTime/10.)

        if len(self.trucks) > 0:
            self.trucks[0].update(task.delayTime)
        return task.again

    def renderTask(self, task):
        """ Do stuff. """
        self.terrain.update()

        # Update the truck's speedometer
        self.lblSpeedo["text"] = "%i" % abs(self.trucks[0].getSpeed())
        self.lblGearState["text"] = self.trucks[0].getGbState()
        self.lblRpmSlider["value"] = self.trucks[0].getRpm()

        if self.trucks[0].getGear() == 0:
            self.lblGear["text"] = 'n'
        elif self.trucks[0].getGear() == 1:
            self.lblGear["text"] = 'r'
        else:
            self.lblGear["text"] = "%i" % (self.trucks[0].getGear() - 1)

        #self.lblGear["text"] = "%i" % self.trucks[0].getGear()

        return Task.cont

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
