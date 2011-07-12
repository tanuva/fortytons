'''
Created on 11.07.2011

@author: marcel
'''

from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from direct.actor.Actor import Actor
from panda3d.core import *

from math import pi, sin, cos

class MyApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Load the environment model.
        self.environ = self.loader.loadModel("models/environment")
        # Reparent the model to render.
        self.environ.reparentTo(self.render)
        # Apply scale and position transforms on the model.
        self.environ.setScale(0.25, 0.25, 0.25)
        self.environ.setPos(-8, 42, 0) # Add the spinCameraTask procedure to the task manager.
        # Tasks are executed every frame
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
        
        # Load and transform the panda actor.
        self.pandaActor = Actor("models/panda-model", {"walk": "models/panda-walk4"})
        self.pandaActor.setScale(0.005, 0.005, 0.005)
        self.pandaActor.reparentTo(self.render)
        self.pandaActor.setPos(-1,0,0)
        # Loop its animation.
        self.pandaActor.loop("walk")
 
        self.cvmgr = ConfigVariableManager.getGlobalPtr()
        #print('Server specified in config file: ', model-path.getValue())
        
        self.truck = loader.loadModel("../../data/mesh/kipper_v4.egg")
        self.truck.reparentTo(self.render)
        self.truck.setPos(2,0,2)
        
        self.truck.setP(-90.0)
        self.truck.setH(-90.0)
        self.truck.setSx(1.5)
        self.truck.setSy(1.5)
        self.truck.setSz(1.5)
        
        #self.flaeche = loader.loadModel("../../data/mesh/flaeche.egg")
        #self.flaeche.reparentTo(self.render)
        #self.flaeche.setPos(0,0,3)

        
        
 
    # Define a procedure to move the camera.
    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (pi / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20.0 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return Task.cont
    
    
    
if __name__ == '__main__':
    app = MyApp()
    app.run()