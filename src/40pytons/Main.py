# -*- coding: utf-8 -*-

'''
Created on 11.07.2011

@author: marcel
'''

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from direct.gui.DirectGui import DirectButton
from panda3d.core import *
from panda3d.physics import *
from pandac.PandaModules import OdeWorld, OdeSimpleSpace, OdeJointGroup
from pandac.PandaModules import OdeBody, OdeMass, OdeBoxGeom, OdePlaneGeom
from pandac.PandaModules import BitMask32, CardMaker, Vec4, Quat


SCALE = 10e-3
#SCALE = 10e-2

class Main(ShowBase):
    truckNps = []
    truckColNps = []
    maskTrucks = BitMask32.bit(1)
    maskTest = BitMask32.bit(2)
    camPos = Point3(8, -7, 3) # Good for egg truck
    #self.camPos = Point3(12, 2.5, 3)
    #self.camPos = Point3(20, -30, 8) # overview
    
    def __init__(self):    
        ShowBase.__init__(self)

        # Initialize ODE
        # Setup our physics world
        world = OdeWorld()
        world.setGravity(0, 0, -9.81)
        # The surface table is needed for autoCollide
        world.initSurfaceTable(1)
        world.setSurfaceEntry(0, 0, 150, 0.0, 9.1, 0.9, 0.00001, 0.0, 0.002)
         
        # Create a space and add a contactgroup to it to add the contact joints
        space = OdeSimpleSpace()
        space.setAutoCollideWorld(world)
        contactgroup = OdeJointGroup()
        space.setAutoCollideJointGroup(contactgroup)
        
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
        
        taskMgr.add(self.updateTask, "update")
        self.taskMgr.add(self.positionCameraTask, "SpinCameraTask")

        # Physics: collision handling
        self.pusher = PhysicsCollisionHandler()
        base.cTrav = CollisionTraverser()
        base.cTrav.showCollisions(base.render)
        
        #self.setupPanda("panda", "models/panda-model", Point3(-2,3,3))
        self.setupTruck("truck", "../../data/mesh/kipper_v4.egg", Point3(.5, 2.5, 1))
        
        # Mesh für kollision nehmen?
        self.das_block = render.attachNewNode(loader.loadModel("../../data/mesh/das_block.X").node())
        self.das_block.setScale(0.01)
        self.das_block.setPos(.5, 2.5, 2.5)
        self.blockCol = self.das_block.attachNewNode(CollisionNode("block_collision"))
        self.blockCol.node().addSolid(CollisionBox(Point3(0,0,0), 2.51, 1.1, 0.6))
        self.blockCol.node().setIntoCollideMask(BitMask32.allOff())
        self.blockCol.node().setFromCollideMask(self.maskTrucks)
        self.blockCol.show()
        
        # into
        floor = render.attachNewNode(CollisionNode("floor"))
        floor.node().addSolid(CollisionPlane(Plane(Vec3(0, 0, 1), Point3(0, 0, 0))))
        floor.node().setIntoCollideMask(self.maskTrucks | self.maskTest)
        floor.show()
        
        # into
        cubeNp = render.attachNewNode(ActorNode("cubeActor"))
        #cubeNp.node().getPhysicsObject().setMass(0) # Has no mass
        cubeNp.setPos(-.5, -.5, .5)
        cubeNpCol = cubeNp.attachNewNode(CollisionNode("cubeCollision"))
        cubeNpCol.node().addSolid(CollisionBox(Point3(0,0,.1), .5, .5, .5))
        cubeNpCol.node().setFromCollideMask(0)
        cubeNpCol.node().setIntoCollideMask(self.maskTest)
        cubeNpCol.show()
        
        npSphere = render.attachNewNode(ActorNode("sphereActor"))
        npSphere.node().getPhysicsObject().setMass(10)
        base.physicsMgr.attachPhysicalNode(npSphere.node())
        npSphereCol = npSphere.attachNewNode(CollisionNode("sphereCollision"))
        npSphereCol.setPos(-.5, -.5, 2)
        npSphereCol.node().addSolid(CollisionSphere(0,0, .5, .5))
        npSphereCol.node().setFromCollideMask(self.maskTest)
        npSphereCol.node().setIntoCollideMask(0)
        self.pusher.addCollider(npSphereCol, npSphere)
        base.cTrav.addCollider(npSphereCol, self.pusher)
        npSphereCol.show()
        
        # We need some downforce
        self.gravity = ForceNode("world-forces")
        self.gravityFnp = render.attachNewNode(self.gravity)
        self.gravityForce = LinearVectorForce(0,0,-9.81*SCALE)
        self.gravity.addForce(self.gravityForce)
        base.physicsMgr.addLinearForce(self.gravityForce)
 
    def positionCameraTask(self, task):
        """ Keep the camera in position. """
        self.camera.setPos(self.camPos)
        self.camera.lookAt(self.truckNps[-1]) # Look at the most recently loaded truck
        #self.camera.lookAt(self.das_block)
        return Task.cont
    
    def updateTask(self, task):
        #self.terrain.update()
        return task.cont
    
    def setupTruck(self, name, mesh, pos):
        """ Loads mesh and sets it up. Very specific for now. """
        
        npTruck = self.render.attachNewNode(ActorNode(name))
        npTruckMdl = npTruck.attachNewNode(loader.loadModel(mesh).node())
        
        if npTruckMdl.node() == None:
            print "Could not load mesh:", mesh
            return
        
        npTruck.setPos(pos)
        #npTruckMdl.setH(-90.0)
        #npTruckMdl.setScale(0.01)
        npTruckMdl.setRenderModeWireframe()
        npTruckMdl.setCollideMask(BitMask32.allOff())

        npTruck.node().getPhysicsObject().setMass(1500*SCALE)

        npTruckCol = npTruck.attachNewNode(CollisionNode(name))        
        # eggmesh: center-side 1m, center-front 2.5m, center-top 1.7m, height exhaust: 0.1m
        #npTruckCol.node().addSolid(CollisionBox(Point3(0,0,0), 1, 2.5, 1.7/2))
        #npTruckCol.setZ(-.1) # Compensate for exhausts sticking out
        npTruckCol.node().addSolid(CollisionSphere(0,-1.25,0, 1))
        npTruckCol.node().addSolid(CollisionSphere(0, 1.25,0, 1))
        npTruckCol.node().setIntoCollideMask(BitMask32.allOff())
        npTruckCol.node().setFromCollideMask(self.maskTrucks)
        npTruckCol.show()
        
        base.physicsMgr.attachPhysicalNode(npTruck.node())
        self.pusher.addCollider(npTruckCol, npTruck)
        base.cTrav.addCollider(npTruckCol, self.pusher)
        
        self.truckNps.append(npTruck)
        self.truckColNps.append(npTruckCol)
    
    def setupPanda(self, name, mesh, pos):
        npTruck = self.render.attachNewNode(ActorNode(name))
        npTruckMdl = npTruck.attachNewNode(loader.loadModel(mesh).node())
        
        if npTruckMdl.node() == None:
            print "Could not load mesh:", mesh
            return
        
        npTruck.setPos(pos)
        npTruckMdl.setCollideMask(BitMask32.allOff())
        
        npTruck.node().getPhysicsObject().setMass(10*SCALE)
        
        npTruckCol = npTruck.attachNewNode(CollisionNode(name))
        # center-top 0,335m, center-front 0,991m, center-seite 0,391m
        npTruckCol.node().addSolid(CollisionSphere(0,0, 2,2))
        npTruckCol.node().setIntoCollideMask(BitMask32.allOff())
        npTruckCol.node().setFromCollideMask(self.maskTrucks)
        npTruckCol.show()
        base.physicsMgr.attachPhysicalNode(npTruck.node())
        
        self.pusher.addCollider(npTruckCol, npTruck)
        base.cTrav.addCollider(npTruckCol, self.pusher)
        
        self.truckNps.append(npTruck)
        self.truckColNps.append(npTruckCol)
        
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
