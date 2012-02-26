# -*- coding: utf-8 -*-
'''
Created on 16.10.2011

@author: marcel
'''

import xml.dom.minidom as dom
from xml.dom.minidom import Comment
from panda3d.core import Vec3

class VehicleDOMParser:
	xmlfile = None
	allowedDatatypes = ("int", "float", "vector", "bool", "str", "func")

	@staticmethod
	def createDOMParser(xmlfile):
		print "parsing", xmlfile
		tree = dom.parse(xmlfile)

		# Find a <vehicle> node in the doc root
		vehicleNode = None

		for node in tree.childNodes:
			if node.nodeName == "vehicle":
				vehicleNode = node
		if vehicleNode == None:
			print "[ERR] %s doesn't contain a <vehicle> node!" % xmlfile

		# Find the vehicle type specified in the xml file
		for node in vehicleNode.childNodes:
			if not node.nodeName == "#text" and len(node.childNodes) == 1 and node.getAttribute("type"):
				vehicleType = node.firstChild.data.strip()

				if vehicleType == "truck":
					return TruckDOMParser(xmlfile, vehicleNode)
				elif vehicleType == "trailer":
					return TrailerDOMParser(xmlfile, vehicleNode)
				else:
					return None

	def _traverseTree(self, startNode, recursing = False):
		if recursing:
			# Add our current node to the path as its the parent for everything we'll add to the data store

			if not isinstance(startNode, Comment) and not startNode.getAttribute("id") == "":
				self.path.append(startNode.getAttribute("id"))
			else:
				self.path.append(startNode.nodeName)

		for node in startNode.childNodes:
			if not node.nodeName == "#text":
				#print node.nodeName, "|\n", node.childNodes, "\n", len(node.childNodes), "\n==="

				if len(node.childNodes) == 1:
					if not self._addData(node.nodeName, node.getAttribute("type"), node.firstChild.data.strip()):
						return False
				else:
					# recurse
					self._traverseTree(node, True)

		if recursing:
			# Recursion step is done, remove this path element

			#if not self.path[-1] == startNode.nodeName:
				# We also appended an id (as in <axle id = "1">)
				#self.path.pop()

			# Pop the original <axle> node
			self.path.pop()

		return True

	def _addData(self, nodeName, datatype, data, parent = "vehicle"):
		if not datatype in self.allowedDatatypes:
			print "[ERR] \"%s\" has no valid type attribute defined!" % (nodeName)
			return False

		# Push it into self.data
		# Combines the path elements collected in self.path to access self.data the right way
		# Do a "print strPath" to see whats happening! :)
		# Ex: Recursion: <vehicle> -> <axle id = "1"> -> <suspension> -> <stiffness>
		#     Generated code: self.data[axle][1][suspension][stiffness] = newEntry
		strPath = "self.data"

		for pathNodeName in self.path:
			if not pathNodeName in eval(strPath).keys():
				eval(strPath)[pathNodeName] = {}
			strPath += "[\"%s\"]" % pathNodeName

		# Check if the current key already exists...
		if nodeName in eval(strPath).keys():
			print "[WRN] %s defines \"%s\" more than once. Using the first definition." % (self.xmlfile, nodeName)
			return True

		strPath += "[\"%s\"] = " % nodeName

		# Prepare the actual data for storage
		if datatype == "vector":
			strPath += "Vec3(%s)" % (data)
		elif datatype == "func":
			strPath += ("\"" + data + "\"")
		elif datatype == "bool":
			strPath += "bool(%s)" % (data) # we don't want quotes around the value (not: bool('False'))
		else:
			strPath += "%s('%s')" % (datatype, data)

		#print strPath # Print the path + the value we just read
		exec strPath
		return True

	def _get(self, path):
		"""
		Build the data access code (like in _addData(...))
		"""

		# Make sure we iterate over an array even if path only has one stage (and therefore is a string)
		if type(path).__name__ == "str":
			tmp = path
			path = []
			path.append(tmp)

		strPath = "self.data"

		for nodename in path:
			if not type(nodename).__name__ == "str":
				nodename = str(nodename)

			strPath += "[\"%s\"]" % nodename

		try:
			return eval(strPath)
		except KeyError:
			print "[ERR] VehicleDOMParser: Requested unexisting value:", strPath
			return None

	# Getters
	def getType(self):
		return self._get(["type"])
	
	def getManufacturer(self):
		return self._get("manufacturer")
	
	def getModel(self):
		return self._get("model")
	
	def getMesh(self):
		return self._get("mesh")
		
	def getDimensions(self):
		return Vec3(self._get("width"), self._get("height"), self._get("length"))
	
	def getWeight(self):
		return self._get("weight")
		
	def getSpawnheight(self):
		return self._get("spawnheight")
		
	def getRideheight(self):
		return self._get("rideheight")

	def getColShapes(self):
		shapes = []
		
		for shape in range(0, len(self._get(["colShapes"]).keys())):
			shapes.append(self._get(["colShapes", str(shape)]))
		
		return shapes
	
	def getWheelMesh(self):
		return self._get(["wheel", "mesh"])
	
	def getWheelWeight(self):
		return self._get(["wheel", "weight"])
	
	def getWheelRadius(self):
		return self._get(["wheel", "radius"])
	
	def getWheelWidth(self):
		return self._get(["wheel", "width"])
	
	def getAxleCount(self):
		return len(self._get("axles").keys())

	def isAxleSteerable(self, axle):
		return self._get(["axles", str(axle), "steerable"])

	def getAxleSteeringFactor(self, axle):
		return self._get(["axles", str(axle), "steeringFactor"])

	def getAxlePosition(self, axle):
		return self._get(["axles", str(axle), "position"])
	
	def getAxleWidth(self, axle):
		return self._get(["axles", str(axle), "width"])
	
	def getAxleSuspMaxTravel(self, axle):
		return self._get(["axles", str(axle), "suspension", "maxTravel"])
	
	def getAxleSuspMaxForce(self, axle):
		return self._get(["axles", str(axle), "suspension", "maxForce"])
	
	def getAxleSuspStiffness(self, axle):
		return self._get(["axles", str(axle), "suspension", "stiffness"])
	
	def getAxleSuspDampingRelax(self, axle):
		return self._get(["axles", str(axle), "suspension", "dampingRelax"])
	
	def getAxleSuspDampingComp(self, axle):
		return self._get(["axles", str(axle), "suspension", "dampingCompression"])
	
	def getAxleSuspFrictionSlip(self, axle):
		return self._get(["axles", str(axle), "suspension", "frictionSlip"])
	
	def getAxleSuspRollInfluence(self, axle):
		return self._get(["axles", str(axle), "suspension", "rollInfluence"])

	def getTrailerHitchPoint(self):
		return self._get(["trailerHitch", "position"])

class TruckDOMParser(VehicleDOMParser):
	# The actual data we've read
	data = {}
	# Acts as a stack and helps us find the right path to use for storage inside self.data
	path = []

	def __init__(self, xmlfile, vehicleNode):
		self.xmlfile = xmlfile

		# Read everything we can grab from the tree
		if not self._traverseTree(vehicleNode):
			print "doh"
			exit(1)

	# Getters
	def getBrakingForce(self):
		return self._get("brakingForce")
	
	def getParkingBrakeForce(self):
		return self._get("parkingBrakeForce")
	
	def getSteeringAngleMax(self):
		return self._get(["steering", "maxAngle"])
	
	def getSteeringRate(self):
		return self._get(["steering", "rate"])
	
	def getDrivetrainType(self):
		return self._get(["drivetrain", "type"])
	
	def getEngineRpmMax(self):
		return self._get(["drivetrain", "maxRpm"])
	
	def getEngineRpmIdle(self):
		return self._get(["drivetrain", "idleRpm"])
	
	def getPoweredAxleRatio(self):
		return self._get(["drivetrain", "powAxleRatio"])
	
	def getGearCount(self):
		return len(self._get(["drivetrain"]).keys())
	
	def getGearRatios(self):
		ratios = []

		for gear in range(0, self.getGearCount()):
			ratios.append(self._get(["drivetrain", "gears", str(gear), "ratio"]))
		
		return ratios
	
	def getTorqueFuncs(self):
		funcs = []

		for funcIndex in range(0, len(self._get(["drivetrain", "torque"]))):
			funcs.append(self._get(["drivetrain", "torque", str(funcIndex)]))
		
		return funcs
	
	def axleIsPowered(self, axle):
		return self._get(["axles", str(axle), "powered"])

class TrailerDOMParser(VehicleDOMParser):
	# The actual data we've read
	data = {}
	# Acts as a stack and helps us find the right path to use for storage inside self.data
	path = []

	def __init__(self, xmlfile, vehicleNode):
		self.xmlfile = xmlfile

		# Read everything we can grab from the tree
		if not self._traverseTree(vehicleNode):
			print "doh"
			exit(1)
