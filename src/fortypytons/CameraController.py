# -*- coding: utf-8 -*-

'''
Created on 26.08.2011

@author: marcel
'''

import math
from panda3d.core import *
from panda3d.bullet import *

class FlyingCameraController:
    height = 4
    radius = 10

    def __init__(self, world, camera, target):
        self.world = world
        self.cam = camera
        self.target = target
        self.bodyNp = render.attachNewNode(BulletRigidBodyNode("cameraBody"))
        self.bodyNp.node().addShape(BulletSphereShape(0.5))
        self.bodyNp.node().setMass(0.1)
        self.bodyNp.setPos(self.target.getPos() + Point3(0,0, self.height))
        self.world.attachRigidBody(self.bodyNp.node())
        self.cam.reparentTo(self.bodyNp)

        # Keep us on a sphere around the target
        self.con = BulletSphericalConstraint(self.bodyNp.node(), self.target.node(), Point3(0,self.radius,0), Point3(0,.5,0))
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

        # Make us weightless
        self.bodyNp.node().applyCentralForce(Vec3(0,0, 9.81 * self.bodyNp.node().getMass()))

        # Get ourselves on the right height
        curPos = self.bodyNp.getPos()[2]
        futurePos = curPos + (1. * self.bodyNp.node().getLinearVelocity()[2])
        targetPos = self.height
        upForce = (targetPos - futurePos) * 1.
        self.bodyNp.node().applyCentralForce(Vec3(0,0, upForce))
        print self.bodyNp.getPos(), upForce

        # Adjust the circular position
        # radius = sqrt(x) + sqrt(y)
        # We want to stay on a certain radius around the target. Therefore, use x = y as thruster.
        """xpos, ypos = self.bodyNp.getPos()[0], self.bodyNp.getPos()[1]
        xvel, yvel = self.bodyNp.node().getLinearVelocity()[0], self.bodyNp.node().getLinearVelocity()[1]

        curPos = self.sqrt(xpos) + self.sqrt(ypos)
        futurePos = curPos + self.sqrt(1. * xvel) + self.sqrt(1. * yvel)
        targetPos = self.radius
        corrForce = (targetPos - futurePos) * 1.

        component = math.pow(corrForce/2, 2)
        corrForce = Vec3(component, component, 0)
        print self.bodyNp.getPos(), corrForce"""

    def sqrt(self, val):
        if val < 0:
            return -math.sqrt(abs(val))
        else:
            return math.sqrt(val)
