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

class FollowerCameraController:
    """
    Gently keeps the camera behind the target.
    """

    height = 4
    radius = 15
    curHDiff = 0

    i = 0
    error = Vec3(0,0,0)

    def __init__(self, world, camera, target):
        self.render = render
        self.world = world
        self.cam = camera
        self.target = target
        self.cam.setPos(self.target, Vec3(0, -self.radius, self.height))

    def update(self, task):
        # Calculate our desired position, then use a PID-controller to get there
        relTargetPos = Vec3(0, -self.radius, self.height)

        tmp = self.cam.getPos()
        self.cam.setPos(self.target, relTargetPos)
        absTargetPos = self.cam.getPos()
        self.cam.setPos(tmp)

        # http://en.wikipedia.org/wiki/PID_controller
        # http://www.engin.umich.edu/group/ctm/PID/PID.html
        # Kx: modifying factors: proportional, integral and derivative
        # error = targetPos - curPos
        # dt: the time difference
        # u = Kp * error + Ki * integrate(error, dt) + Kd * (de / dt)

        self._printAsInt(absTargetPos)

        Kp = 0.05
        Ki = 0.05
        Kd = .001
        lastError = self.error
        self.error = absTargetPos - self.cam.getPos()

        # linear pid, x axis
        prop = Kp * self.error[0]
        intgr = Ki * self.error[0] * globalClock.getDt()
        derv = Kd * (lastError[0] - self.error[0]) / globalClock.getDt()
        corrForce = Vec3(prop + intgr + derv, 0, 0)

        # y axis
        prop = Kp * self.error[1]
        intgr = Ki * self.error[1] * globalClock.getDt()
        derv = Kd * (lastError[1] - self.error[1]) / globalClock.getDt()
        corrForce[1] = prop + intgr + derv
        # z axis
        # more or less statically set as targetheight + our height offset
        newCamPos = self.cam.getPos() + corrForce
        newCamPos[2] = self.target.getPos()[2] + self.height

        #print self.cam.getPos(self.target) # prints correct relative coordinates, just FYI
        self.cam.setPos(newCamPos)
        self.cam.lookAt(self.target)
        #self.cam.lookAt(self.target.getPos(self.cam) + Vec3(0, 0, 1.5)) # works
        return task.cont

    def _printAsInt(self, vec):
        if self.i % 40 == 0:
            print "(", int(vec[0]), int(vec[1]), int(vec[2]), ")"
        self.i += 1

    def mwheelup(self):
        pass

    def mwheeldown(self):
        pass

    def _rotateVector(self, vec, deg):
        # x' = x*cos q - y*sin q
        # y' = x*sin q + y*cos q
        # z' = z

        rad = deg * math.pi / 180.
        out = Vec3()
        out[0] = vec[0] * math.cos(rad) - vec[1] * math.sin(rad)
        out[1] = vec[0] * math.sin(rad) + vec[1] * math.cos(rad)
        out[2] = vec[2]
        return out
