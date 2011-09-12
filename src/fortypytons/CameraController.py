# -*- coding: utf-8 -*-

'''
Created on 26.08.2011

@author: marcel
'''

import math
from panda3d.core import *
from panda3d.bullet import *

class ManualCameraController:
    """
    Allows free movement of the camera around the target using the mouse.
    """
    distance = 10
    rot = 180.
    inc = math.pi/4.

    def __init__(self, world, camera, target):
        self.world = world
        self.cam = camera
        self.target = target

    def update(self, task):
        relPos = self.cam.getPos(self.target)
        if base.mouseWatcherNode.hasMouse():
            relMousePos = base.mouseWatcherNode.getMouseX(), base.mouseWatcherNode.getMouseY()

            self.rot += relMousePos[0] * 10.
            self.inc += relMousePos[1] * 10.

            # MAKE MOUSE WHEEL MOVE BACK AND FORTH

            # Move us around the target in spherical coordinates:
            # distance: radius
            # inc: angle between Z+ and the camera (roughly inclination)
            # rot: angle between X+ and the camera (rotation)
            x = self.distance * math.sin(self.deg2rad(self.inc)) * math.cos(self.deg2rad(self.rot))
            y = self.distance * math.sin(self.deg2rad(self.inc)) * math.sin(self.deg2rad(self.rot))
            z = self.distance * math.cos(self.deg2rad(self.inc))

            self.cam.setPos(self.target.getPos() + Point3(x,-y,z)) # Invert y to imitate aircraft pitch control
            base.win.movePointer(0, base.win.getXSize() / 2, base.win.getYSize() / 2) # Reset the pointer to the window's center

        # Make the camera look at the target again.
        self.cam.lookAt(self.target)
        return task.cont

    def mwheelup(self):
        if self.distance > 8:
            self.distance -= .5

    def mwheeldown(self):
        self.distance += .5

    def deg2rad(self, deg):
        return deg * math.pi / 180.

class FlyingCameraController:
    height = 4
    radius = 10
    targetSpd = Vec3(0,0,0)

    def __init__(self, world, camera, target):
        self.world = world
        self.cam = camera
        self.target = target
        self.bodyNp = render.attachNewNode(BulletRigidBodyNode("cameraBody"))
        self.bodyNp.node().setCollisionResponse(False)
        self.bodyNp.node().addShape(BulletSphereShape(0.5))
        self.bodyNp.node().setMass(0.1)
        self.bodyNp.node().setLinearDamping(.5)
        self.bodyNp.node().setGravity(Vec3(0,0,0)) # Make us weightless
        self.bodyNp.setPos(self.target.getPos() + Point3(0,0, self.height))
        self.world.attachRigidBody(self.bodyNp.node())
        self.cam.reparentTo(self.bodyNp)

        # Keep us on a sphere around the target
        self.con = BulletSphericalConstraint(self.bodyNp.node(), self.target.node(), Point3(0,self.radius,0), Point3(0,0,0))
        self.world.attachConstraint(self.con)

    def update(self):
        self.bodyNp.lookAt(self.target)
        #self.bodyNp.setR(0)

        # adapted thrust control logic from: http://opende.sourceforge.net/wiki/index.php/HOWTO_thrust_control_logic
        """
        curVel = *(Vec3*)dBodyGetLinearVelocity( b );
        curPos = *(Vec3*)dBodyGetPosition( b );
        futurePos = curPos + LOOKAHEAD * curVel;
        desiredPos = YOUR_TARGET_HERE;
        applyForce = (futurePos - desiredPos) * SENSITIVITY;
        clampLength( applyForce, MAX_FORCE );
        dBodyAddForce( b, applyForce );
        """

        # Get ourselves on the right height
        curPos = self.bodyNp.getPos()[2]
        futurePos = curPos + (1. * self.bodyNp.node().getLinearVelocity()[2])
        targetPos = self.height + self.target.getPos()[2]
        upForce = (targetPos - futurePos) * 1.
        self.bodyNp.node().applyCentralForce(Vec3(0,0, upForce))
        #print self.bodyNp.getPos(), upForce

        # Adjust the circular position

        # BEFORE COMMIT UNSELF TARGETSPEED

        lastSpd = self.targetSpd
        self.targetSpd = self.target.node().getLinearVelocity()
        self.targetSpd[2] = 0 # Height handling is not our task.
        self.targetSpd *= .5

        self.bodyNp.node().applyCentralForce(-self.targetSpd)
        print self.targetSpd

    def sqrt(self, val):
        if val < 0:
            return -math.sqrt(abs(val))
        else:
            return math.sqrt(val)
