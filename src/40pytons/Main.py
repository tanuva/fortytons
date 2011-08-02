'''
Created on 11.07.2011

@author: marcel
'''

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import *
from panda3d.physics import *

from math import pi, sin, cos

#SCALE = 10e-3
SCALE = 10e-2

class MyApp(ShowBase):
    truckNps = []
    truckColNps = []
    maskTrucks = BitMask32.bit(1)
    
    def __init__(self):
        ShowBase.__init__(self)
        base.enableParticles()
        
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
        #self.terrainNp.setCollideMask(BitMask32.allOff())
        
        # Add a task to keep updating the terrain
        taskMgr.add(self.updateTask, "update")
        
        # Generate it.
        self.terrain.generate()
        
        
        self.taskMgr.add(self.positionCameraTask, "SpinCameraTask")

        # Physics: collision handling
        self.pusher = PhysicsCollisionHandler()
        base.cTrav = CollisionTraverser()
        base.cTrav.showCollisions(base.render)
        
        #self.setupPanda("panda", "models/panda-model", Point3(-2,3,3))
        self.setupTruck("truck", "../../data/mesh/kipper_v4.x", Point3(.7,0,1.1))
        
        cube = render.attachNewNode(CollisionNode("truckCollision"))
        cube.setPos(-.5, -.5, .5)
        cube.node().addSolid(CollisionBox(Point3(0,0,0), .5, .5, .5))
        cube.show()
        
        # We need some downforce
        self.gravity = ForceNode("world-forces")
        self.gravityFnp = render.attachNewNode(self.gravity)
        self.gravityForce = LinearVectorForce(0,0,-9.81*SCALE)
        self.gravity.addForce(self.gravityForce)
        #base.physicsMgr.addLinearForce(self.gravityForce)
 
    def positionCameraTask(self, task):
        """ Keep the camera in position. """
        self.camera.setPos(3, -5, 2)
        self.camera.lookAt(self.truckNps[-1]) # Look at the most recently loaded truck
        #self.camera.lookAt(self.truckNps[0])
        return Task.cont
    
    def updateTask(self, task):
        self.terrain.update()
        return task.cont
    
    def setupTruck(self, name, mesh, pos):
        """ Loads mesh and sets it up. Very specific for now. """
        
        npTruck = self.render.attachNewNode(ActorNode(name))
        npTruckMdl = npTruck.attachNewNode(loader.loadModel(mesh).node())
        
        if npTruckMdl.node() == None:
            print "Could not load mesh:", mesh
            return
        
        npTruck.setPos(pos)
        npTruckMdl.setH(-90.0)
        npTruckMdl.setScale(0.01)
        npTruckMdl.setCollideMask(BitMask32.allOff())
        
        npTruck.node().getPhysicsObject().setMass(1500*SCALE)
        
        npTruckCol = npTruck.attachNewNode(CollisionNode(name))
        # center-top 0,335m, center-front 0,991m, center-side 0,391m
        npTruckCol.node().addSolid(CollisionBox(Point3(0,0,0), 0.391, 0.991, 0.335))
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
        #npTruckMdl.setH(-90.0)
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
    
if __name__ == '__main__':
    app = MyApp()
    app.run()
