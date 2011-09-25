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
            y = self.distance * math.sin(self.deg2rad(self.inc)) * math.sin(self.deg2rad(self.rot)) * (-1.) # Invert y to imitate aircraft pitch control
            z = self.distance * math.cos(self.deg2rad(self.inc))

            self.cam.setPos(self.target.getPos() + Point3(x, y, z))
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
    """
    Gently keeps the camera behind the target.
    """

    height = 4
    radius = 15
    curHDiff = 0

    def __init__(self, world, camera, target):
        self.world = world
        self.cam = camera
        self.target = target
        self.bodyNp = self.target.attachNewNode(BulletRigidBodyNode("cameraBody"))
        self.bodyNp.node().setCollisionResponse(False)
        self.bodyNp.node().addShape(BulletSphereShape(0.5))
        self.bodyNp.node().setMass(0.1)
        #self.bodyNp.node().setLinearDamping(.5) # Is this really needed?
        self.bodyNp.setPos(self.target, Point3(0,-self.radius, self.height))
        self.world.attachRigidBody(self.bodyNp.node())
        self.cam.reparentTo(self.bodyNp)

        # Keep us on a sphere around the target
        self.con = BulletSphericalConstraint(self.bodyNp.node(), self.target.node(), Point3(0,self.radius,0), Point3(0,0,0))
        self.world.attachConstraint(self.con)

    def update(self, task):
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

        # Make us weightless
        self.bodyNp.node().applyCentralForce(Vec3(0,0, 9.81 * self.bodyNp.node().getMass()))

        relCurPos = self.bodyNp.getPos(self.target)

        # TODO Take target pitch into account!

        # Get ourselves on the right height
        futurePos = relCurPos[2] + (1. * self.bodyNp.node().getLinearVelocity()[2])
        targetPos = self.height
        corrForce = (targetPos - futurePos) * 4.
        self.bodyNp.node().applyCentralForce(Vec3(0,0, corrForce))

        # Adjust the circular position
        # Using the same code as above, abusing "thrust control" for the (rougly) one-dimensional rotation around the target.
        lastHDiff = self.curHDiff
        self.curHDiff = self._getHeadingDiff(self.bodyNp.getH(), self.target.getH())

        curH = self.bodyNp.getH()
        rotSpd = self.curHDiff - lastHDiff
        futureH = (curH + (.5 * rotSpd)) % 360
        targetH = self.target.getH(self.bodyNp)
        #targetH = 0
        corrForce = self._getHeadingDiff(targetH, futureH) * .01
        corrForce = self._vecRotate((corrForce, 0), self.bodyNp.getH())
        self.bodyNp.node().applyCentralForce(Vec3(corrForce[0], corrForce[1], 0))

        print targetH, "-", futureH, "=", corrForce

        self.bodyNp.lookAt(self.target)
        return task.cont

    def _vecRotate(self, vec, deg):
        """ Rotates vec by deg. """
        deg *= math.pi / 180.

        return (vec[0] * math.cos(deg) - vec[1] * math.sin(deg),
                vec[0] * math.sin(deg) - vec[1] * math.cos(deg))

    def _getHeadingDiff(self, h1, h2):
        diff = h1 - h2
        if abs(diff) > 180.:
            diff = (h1 + diff) % 360. - (h2 + diff) % 360.
        return diff

