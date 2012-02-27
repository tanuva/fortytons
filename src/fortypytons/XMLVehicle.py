# -*- coding: utf-8 -*-
'''
Created on 27.02.2012

@author: marcel
'''

import math
from VehicleDOMParser import *
from VComponent import *
from Util import Util
from panda3d.core import *
from panda3d.bullet import *

class XMLVehicle(object):
	def __init__(self, xmlfile, datadir, spawnpos, world):
		self.components = []
		self.constraints = []

		self.datadir = datadir
		self.world = world
		self.parser = VehicleDOMParser(self.datadir + xmlfile)
		p = self.parser # Will get ugly otherwise...

		# ===== Load meshes and collision shapes =====
		for meshId in range(0, p.getMeshCount()):
			bodyNp = render.attachNewNode(BulletRigidBodyNode('truck' + str(meshId)))

			if meshId == 0:
				bodyNp.setPos(spawnpos + p.getSpawnheight())
			else:
				parentComp = self.components[p.getMeshParent(meshId)]
				bodyNp.setPos(parentComp.getBodyNp().getPos() + p.getMeshOffset(meshId))

			bodyNp.node().setMass(p.getWeight(meshId))
			bodyNp.node().setDeactivationEnabled(False)
			
			self.world.attachRigidBody(bodyNp.node())
			meshNp = bodyNp.attachNewNode(loader.loadModel(self.datadir + p.getMeshFilename(meshId)).node())

			# ===== Configure the collision shapes =====
			for shape in p.getColShapes(meshId):
				if shape["type"] == "box":
					size = Vec3(shape["width"]/2, shape["length"]/2, shape["height"]/2)
					bodyNp.node().addShape(BulletBoxShape(size), TransformState.makePos(shape["offset"]))
				else:
					print "[WRN] XMLTruck: got a non-box collision shape, not supported yet."

			self.components.append(VComponent(meshNp, bodyNp))

		# ===== Constraints =====
		for conIndex in range(0, p.getConstraintCount()):
			if p.getConstraintType(conIndex) == "hinge":
				con = BulletHingeConstraint(self.components[p.getConstraintMesh1(conIndex)].getBodyNp().node(),
											self.components[p.getConstraintMesh2(conIndex)].getBodyNp().node(),
											p.getConstraintPoint1(conIndex), p.getConstraintPoint2(conIndex),
											p.getConstraintFrame1(conIndex), p.getConstraintFrame2(conIndex), True)
				con.setAxis(p.getConstraintAxis(conIndex))
				limits = p.getConstraintLimits(conIndex)
				con.setLimit(limits[0], limits[1])
				con.setDebugDrawSize(2.0)
				self.world.attachConstraint(con)
				self.constraints.append(VConstraint(con, p.isConstraintControllable(conIndex)))
			else:
				print "[WRN] Constraint %i has unknown type %s" % (conIndex, p.getConstraintType(conIndex))

		# ===== BulletVehicle setup =====
		self.vehicle = BulletVehicle(self.world, self.components[0].getBodyNp().node())
		self.vehicle.setCoordinateSystem(ZUp)
		self.world.attachVehicle(self.vehicle)

		# ===== Wheels =====
		self.wheels = []

		for axIndex in range(0, p.getAxleCount()):
			axPos = p.getAxlePosition(axIndex)
			axWidth = p.getAxleWidth(axIndex)
			rideHeight = p.getMeshOffset(0)[2] # Use the first mesh offset's z component (which should be the chassis)
			isPowered = p.axleIsPowered(axIndex)

			for wheelIndex in range(0, 2):
				# Wheel 0 is left, 1 is the right one
				# Prepare the wheel's position vector
				pos = Point3(axWidth/2., axPos, rideHeight)

				# Prepare the wheel's bullet node
				wheelNp = render.attachNewNode(BulletRigidBodyNode('wheelBox'))
				wheelNp.node().setMass(p.getWheelWeight())
				wheelNp.setPos(pos)
				self.world.attachRigidBody(wheelNp.node())

				# Load the wheel mesh
				meshNp = wheelNp.attachNewNode(loader.loadModel(self.datadir + p.getWheelMesh()).node())
				if wheelIndex == 0:
					# We need to turn around the mesh of the left wheel
					meshNp.setH(180.0)
					# And invert it's x position (from right to left side)
					pos[0] *= -1.

				# Add the wheel to the BulletVehicle
				wheel = self.vehicle.createWheel()
				wheel.setNode(wheelNp.node())
				wheel.setChassisConnectionPointCs(pos)

				wheel.setWheelDirectionCs(Vec3(0, 0, -1))
				wheel.setWheelAxleCs(Vec3(1, 0, 0))
				wheel.setWheelRadius(p.getWheelRadius())

				# suspension setup
				wheel.setFrontWheel(p.isAxleSteerable(axIndex))
				wheel.setMaxSuspensionTravelCm(p.getAxleSuspMaxTravel(axIndex))
				wheel.setMaxSuspensionForce(p.getAxleSuspMaxForce(axIndex))
				wheel.setSuspensionStiffness(p.getAxleSuspStiffness(axIndex))
				wheel.setWheelsDampingRelaxation(p.getAxleSuspDampingRelax(axIndex))
				wheel.setWheelsDampingCompression(p.getAxleSuspDampingComp(axIndex))
				wheel.setFrictionSlip(p.getAxleSuspFrictionSlip(axIndex))
				wheel.setRollInfluence(p.getAxleSuspRollInfluence(axIndex))

				self.wheels.append(VComponent([meshNp], wheelNp))

	def getChassis(self):
		return self.components[0]
	def getSpeed(self):
		return self.vehicle.getCurrentSpeedKmHour()
	def getTrailerHitchPoint(self):
		return self.parser.getTrailerHitchPoint()
	def getType(self):
		return self.parser.getType()
