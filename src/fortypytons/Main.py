# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

import sys
from Truck import Truck
from XMLTruck import XMLTruck
from XMLTrailer import XMLTrailer
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
    vehicles = []
    datadir = "../../data/"
    accel, brake, left, right = False, False, False, False

    def __init__(self):
        ShowBase.__init__(self)
        base.setFrameRateMeter(True)
        base.disableMouse() # Disable panda's default mouse control
        # Hide the cursor
        props = WindowProperties()
        props.setCursorHidden(True)
        base.win.requestProperties(props)

        # Disable sound for now
        base.disableAllAudio() # Doesn't work oO

        # Enable anti aliasing
        render.setAntialias(AntialiasAttrib.MAuto)

        # Set up our physics world
        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -9.81))

        # We need some gui
        self.lblGearState = DirectLabel(text = "X", scale = .1, pos = Point3(1.2, 0, -.97))
        self.lblGear = DirectLabel(text = "X", scale = .1, pos = Point3(1., 0, -.97))
        self.lblRpmSlider = DirectSlider(scale = .5, pos = Point3(1, 0, -.8), range=(0,3000), value=0, pageSize=0)

        # speedometer
        self.lblSpeedo = TextNode("speedometer")
        self.lblSpeedo.setText("000")
        self.lblSpeedo.setFont(loader.loadFont(self.datadir + "gui/lcd-normal.ttf"))
        self.lblSpeedo.setSlant(-.1)
        self.lblSpeedo.setAlign(TextNode.ARight)
        self.lblSpeedo.setTextColor(0, 0, 0, 1)
        self.lblSpeedoNp = aspect2d.attachNewNode(self.lblSpeedo)
        self.lblSpeedoNp.setScale(0.08)
        self.lblSpeedoNp.setPos(Point3(1.25, 0, -.9))

        self.accept("f9", self.toggleDebug)
        self.accept("f10", base.toggleWireframe)
        self.accept("f11", base.toggleTexture)
        self.accept("f12", base.screenshot, ["40tons"])

        # render in wireframe by default for now
        #base.toggleWireframe()

        # Enable shad(er|ow) generation
        render.setShaderAuto()

        # Let there be light!
        dlight = DirectionalLight('dlight')
        dlight.setColor(VBase4(1., 1., 1., 1))
        #dlight.setShadowCaster(True, 512, 512)
        dlnp = render.attachNewNode(dlight)
        dlnp.setHpr(0, -60, 0)
        render.setLight(dlnp)

        amblight = AmbientLight('amblight')
        amblight.setColor(VBase4(0.4, 0.4, 0.4, 1))
        amblightNp = render.attachNewNode(amblight)
        render.setLight(amblightNp)

        # TODO Load the skybox
        #tex = loader.loadCubeMap(self.datadir + "tex/skyrender#.png")
        #skyboxNp = self.camera.attachNewNode(loader.loadModel("box").node())
        #skyboxNp.setBin("background", 0);
        #skyboxNp.setDepthWrite(False);
        #skyboxNp.setCompass()
        #skyboxNp.setTexture(tex)
        #skyboxNp.setLightOff()
        #skyboxNp.setShaderOff()

        terrainFile = self.datadir + "tex/inclined.png"

        self.terBodyNp = render.attachNewNode(BulletRigidBodyNode("terrainBody"))
        img = PNMImage(Filename(terrainFile))
        offset = img.getXSize() / 2.0 - 0.5 # Used for the GeoMipTerrain
        height = 10.0
        self.terBodyNp.node().addShape(BulletHeightfieldShape(img, height, ZUp))
        self.terBodyNp.node().setDebugEnabled(False)
        self.terBodyNp.setPos(0,0, height / 2.0)
        self.world.attachRigidBody(self.terBodyNp.node())

        # Set up the GeoMipTerrain
        self.terrain = GeoMipTerrain("terrainNode")
        self.terrain.setHeightfield(terrainFile)
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

        self.vehicles.append(XMLTruck("vehicles/atego/vehicle.xml", self.datadir, Vec3(0,0,0), self.world))
        self.vehicles.append(XMLTruck("vehicles/atego/vehicle.xml", self.datadir, Vec3(4,5,0), self.world))
        self.vehicles.append(XMLTrailer("vehicles/dumper trailer/vehicle.xml", self.datadir, Vec3(0,-6,0), self.world))

        # Register truck functions
        # Truck should do this by itself! (or advertise keys it wants to use? better approach...)
        self.keyconf = KeyConfig(self)
        self.keyconf.loadConfig("neo2.conf")
        self.keyconf.setHook("gas", self.vehicles[0].setGas, [1.], [0.])
        self.keyconf.setHook("brake", self.vehicles[0].setBrake, [1.], [0.])
        self.keyconf.setHook("steerLeft", self.vehicles[0].steer, [1], [0])
        self.keyconf.setHook("steerRight", self.vehicles[0].steer, [-1], [0])
        self.keyconf.setHook("reset", self.vehicles[0].reset)
        self.keyconf.setHook("shiftPark", self.vehicles[0].shiftPark)
        self.keyconf.setHook("shiftReverse", self.vehicles[0].shiftReverse)
        self.keyconf.setHook("shiftNeutral", self.vehicles[0].shiftNeutral)
        self.keyconf.setHook("shiftDrive", self.vehicles[0].shiftDrive)
        self.keyconf.setHook("couple", self.vehicles[0].couple, [self.vehicles])
        self.keyconf.setHook("control0Up", self.vehicles[0].control, [0, 1.], [0, 0.])
        self.keyconf.setHook("control0Down", self.vehicles[0].control, [0, -1.], [0, 0.])
        self.keyconf.setHook("control1Up", self.vehicles[0].control, [1, 1.], [1, 0.])
        self.keyconf.setHook("control1Down", self.vehicles[0].control, [1, -1.], [1, 0.])
        self.keyconf.setHook("control2Up", self.vehicles[0].control, [2, 1.], [2, 0.])
        self.keyconf.setHook("control2Down", self.vehicles[0].control, [2, -1.], [2, 0.])
        self.keyconf.setHook("control3Up", self.vehicles[0].control, [3, 1.], [3, 0.])
        self.keyconf.setHook("control3Down", self.vehicles[0].control, [3, -1.], [3, 0.])
        self.keyconf.setHook("control4Up", self.vehicles[0].control, [4, 1.], [4, 0.])
        self.keyconf.setHook("control4Down", self.vehicles[0].control, [4, -1.], [4, 0.])

        self.camcon = FollowerCameraController(self.world, self.camera, self.vehicles[0].getChassis().getBodyNp())
        taskMgr.add(self.camcon.update, 'CameraController', priority=10)
        self.keyconf.setHook("switchCamera", self.switchCamera)
        self.accept("wheel_up", self.camcon.mwheelup)
        self.accept("wheel_down", self.camcon.mwheeldown)

        self.accept('escape', sys.exit)
        self.accept("i", base.bufferViewer.toggleEnable)

        # register the physics update task
        self.taskMgr.doMethodLater(1./60., self.physicsTask, "physicsTask", priority=5)
        # register the render task
        self.taskMgr.doMethodLater(0.1, self.renderTask, "renderTask", priority=9)

    def physicsTask(self, task):
        self.world.doPhysics(task.delayTime, 10, task.delayTime/10.)

        if len(self.vehicles) > 0:
            for truck in self.vehicles:
                if truck.getType() == "truck":
                    truck.update(task.delayTime)
        return task.again

    def renderTask(self, task):
        """ Do stuff. """
        self.terrain.update()

        # Update the truck's speedometer
        self.lblSpeedoNp.node().setText("%i" % abs(self.vehicles[0].getSpeed()))
        self.lblGearState["text"] = self.vehicles[0].getGbState()
        self.lblRpmSlider["value"] = self.vehicles[0].getRpm()

        if self.vehicles[0].getGear() == 0:
            self.lblGear["text"] = 'r'
        elif self.vehicles[0].getGear() == 1:
            self.lblGear["text"] = 'n'
        else:
            self.lblGear["text"] = "%i" % (self.vehicles[0].getGear() - 1)

        return Task.cont

    def toggleDebug(self):
        if self.debug.isHidden():
            self.debug.show()
        else:
            self.debug.hide()

    def switchCamera(self):
        if isinstance(self.camcon, CockpitCameraController):
            self.camcon = ManualCameraController(self.world, self.camera, self.vehicles[0].getChassis().getBodyNp())
            taskMgr.remove("CameraController")
            taskMgr.add(self.camcon.update, 'CameraController', priority=10)
            self.accept("wheel_up", self.camcon.mwheelup)
            self.accept("wheel_down", self.camcon.mwheeldown)
        elif isinstance(self.camcon, ManualCameraController):
            self.camcon = FollowerCameraController(self.world, self.camera, self.vehicles[0].getChassis().getBodyNp())
            taskMgr.remove("CameraController")
            taskMgr.add(self.camcon.update, 'CameraController', priority=10)
            self.accept("wheel_up", self.camcon.mwheelup)
            self.accept("wheel_down", self.camcon.mwheeldown)
        else:
            self.camcon = CockpitCameraController(self.world, self.camera, self.vehicles[0].getChassis().getBodyNp())
            taskMgr.remove("CameraController")
            taskMgr.add(self.camcon.update, 'CameraController', priority=10)
            self.accept("wheel_up", self.camcon.mwheelup)
            self.accept("wheel_down", self.camcon.mwheeldown)

if __name__ == '__main__':
    app = Main()
    app.run()
