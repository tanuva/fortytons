# -*- coding: utf-8 -*-
'''
Created on 16.10.2011

@author: marcel
'''

import math
import xml.dom.minidom as dom

from Drivetrain import AutomaticDt
from VComponent import *
from panda3d.core import *
from panda3d.bullet import *

class VehicleDOMParser:
	xmlfile = None
	allowedDatatypes = ("int", "float", "vector", "bool", "str", "func")

	# The actual data we've read
	data = {}
	# Acts as a stack and helps us find the right path to use for storage inside self.data
	path = []

	def __init__(self, xmlfile):
		self.xmlfile = xmlfile
		tree = dom.parse(self.xmlfile)

		# Find a <vehicle> node in the doc root
		vehicleNode = None

		for node in tree.childNodes:
			if node.nodeName == "vehicle":
				vehicleNode = node
		if vehicleNode == None:
			print "[ERR] %s doesn't contain a <vehicle> node!" % xmlfile

		# Read everything we can grab from the tree
		if not self._traverseTree(vehicleNode):
			exit(1)

		#print self.data

	def _traverseTree(self, startNode, recursing = False):
		if recursing:
			# Add our current node to the path as its the parent for everything we'll add to the data store
			self.path.append(startNode.nodeName)
			if not startNode.getAttribute("id") == "":
				self.path.append(startNode.getAttribute("id"))

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

			if not self.path[-1] == startNode.nodeName:
				# We also appended an id (as in <axle id = "1">)
				self.path.pop()

			# Pop the original <axle> node
			self.path.pop()

		return True

	def _addData(self, nodeName, datatype, data, parent = "vehicle"):
		if not datatype in self.allowedDatatypes:
			print "[ERR] \"%s\" has no valid type attribute defined!" % (nodeName)
			return False

		# Push it into self.data
		# Combines the path elements collected in self.path to access self.data the right way
		# Do a "print strPath" to see what's happening! :)
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
		else:
			strPath += "%s('%s')" % (datatype, data)

		print strPath
		exec strPath
		return True

	def get(self, path):
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

class XMLTruck:
	def __init__(self, xmlfile):
		parser = VehicleDOMParser(xmlfile)

		if parser.get("type") == "truck":
			print "We are a truck!"
