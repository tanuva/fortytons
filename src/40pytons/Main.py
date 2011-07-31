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
    def __init__(self):
        ShowBase.__init__(self)
        base.enableParticles()
        
        # Load the environment model.
        self.env = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.env.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.env.setScale(0.25, 0.25, 0.25)
        self.env.setPos(-8, 42, 0)
        
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
        # Load and transform the panda actor.
        self.pandaActor = Actor("models/panda-model", {"walk": "models/panda-walk4"})
        self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.reparentTo(self.render)
        self.pandaActor.setPos(-1,0,0)
        # Loop its animation.
        self.pandaActor.loop("walk")

        
        
        mask_floor = BitMask32.bit(1)
        self.env.setCollideMask(mask_floor)
        self.pandaActor.setCollideMask(mask_floor)
        
        # Visible truck parts
        self.truck = loader.loadModel("../../data/mesh/kipper_v4.egg")
        self.truck.reparentTo(self.render)
        self.truck.setCollideMask(BitMask32.allOff())
        self.truck.setPos(0,0,1.5)
        self.truck.setP(-90.0)
        self.truck.setH(-90.0)
        
        # Physical truck parts
        self.phyroot = NodePath("PhysicsNode") # The physics root node
        self.phyroot.reparentTo(self.render)
        
        #base.physicsMgr.attachPhysicalNode(ActorNode("../../data/mesh/kipper_v4.egg"))
        self.truckNp = self.phyroot.attachNewNode(ActorNode("../../data/mesh/kipper_v4.egg"))
        self.truck.reparentTo(self.truckNp)
        self.truckNp.node().getPhysicsObject().setMass(1500*SCALE)
        
        # "fromObject" or collision nodepath
        self.truckColNp = self.truckNp.attachNewNode(CollisionNode("agentCollisionNode"))
        self.truckColNp.node().addSolid(CollisionSphere(0,0,1.5,1.5))
        self.truckColNp.node().setFromCollideMask(mask_floor)
        self.truckColNp.node().setIntoCollideMask(BitMask32.allOff())
        self.truckColNp.show()
        
        #base.cTrav.addCollider(self.truckNp, self.pusher)
        
        # We need some downforce
        self.gravity = ForceNode("world-forces")
        self.gravityFnp = render.attachNewNode(self.gravity)
        self.gravityForce = LinearVectorForce(0,0,-9.81*SCALE)
        self.gravity.addForce(self.gravityForce)
        base.physicsMgr.addLinearForce(self.gravityForce)
        
        
        #self.flaeche = loader.loadModel("../../data/mesh/flaeche.egg")
        #self.flaeche.reparentTo(self.render)
        #self.flaeche.setPos(0,0,3)

        # Physics: collision handling
        self.pusher = PhysicsCollisionHandler()
        self.pusher.addCollider(self.truckColNp, self.truckNp)
        
        base.cTrav = CollisionTraverser()
        base.cTrav.addCollider(self.truckColNp, self.pusher)
        base.cTrav.showCollisions(base.render)
        
        base.physicsMgr.attachPhysicalNode(self.truckNp.node())
        
        # lift us up a little
        self.truckNp.setZ(8)
 
    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        angleDegrees = task.time * 2.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont
    
if __name__ == '__main__':
    app = MyApp()
    app.run()
