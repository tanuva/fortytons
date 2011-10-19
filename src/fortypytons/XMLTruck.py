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

		print self.data

	def _traverseTree(self, startnode):
		for node in startnode.childNodes:
			if not node.nodeName == "#text":
				#print node.nodeName, "|\n", node.childNodes, "\n", len(node.childNodes), "\n==="

				if len(node.childNodes) == 1:
					if not self._addData(node.nodeName, node.getAttribute("type"), node.firstChild.data.strip()):
						return False
				else:
					# recurse
					self._traverseTree(node)

		return True

	def _addData(self, nodeName, datatype, data):
		if not datatype in self.allowedDatatypes:
			print "[ERR] \"%s\" has no type attribute defined!" % (nodeName)
			return False
		elif nodeName in self.data.keys():
			print "[WRN] %s defines \"%s\" more than once. Using the first definition." % (self.xmlfile, nodeName)
			return True

		if datatype == "vector":
			self.data[nodeName] = eval("Vec3(%s)" % (data))
		elif datatype == "func":
			self.data[nodeName] = data
		else:
			self.data[nodeName] = eval("%s('%s')" % (datatype, data))
		return True

	def get(self, attr):
		if attr in self.data.keys():
			return self.data[attr]
		else:
			return None

class XMLTruck:
	def __init__(self, xmlfile):
		parser = VehicleDOMParser(xmlfile)

		if parser.get("type") == "truck":
			print "We are a truck!"
