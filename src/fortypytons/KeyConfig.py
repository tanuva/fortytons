# -*- coding: utf-8 -*-

'''
Created on 7.10.2011

@author: marcel
'''

class KeyConfig:
	"""
	Loads pairs of "do_stuff key" assignments. Main then hooks our do_stuff actions that we call upon input.
	"""

	mapping = {}
	base = None

	def __init__(self, showbase):
		"""
		Initializes a new instance. Showbase is a Panda3D ShowBase instance that we need to actually read key input.
		"""
		self.showbase = showbase

	def setHook(self, action, method, params = None, paramsup = None):
		"""
		If params2 is not None, there will be two actions:
		1. mapped_key -> method(params)
		2. mapped_key-up -> method(paramsup)
		The first params tuple will be passed to method on keypress, the second one on key release.
		Use this to control an analogue axis using keys.
		To hook only the -up state of a key, set params to None
		"""

		if params == None and paramsup == None:
			self.showbase.accept(self.mapping[action], method)
			print "Hook: {0} => {1} => {2}".format(self.mapping[action], action, method)

		if not params == None:
			self.showbase.accept(self.mapping[action], method, params)
			print "Hook: {0} => {1} => {2} {3}".format(self.mapping[action], action, method, params)

		if not paramsup == None:
			self.showbase.accept("%s-up" % self.mapping[action], method, paramsup)
			print "Hook: {0} => {1} => {2} {3}".format(self.mapping[action], action, method, paramsup)

	def loadConfig(self, filename):
		f = open(filename, 'r')

		for line in f.readlines():
			# filter out comments and invalid lines
			if not line[0] == '#' \
			and len(line) > 4 \
			and len(line.split(' ')) == 2:
				line.strip(' ')
				action, key = line.split(' ')
				key = key[:-1] # strip the trailing \n from the key name

				self._addMappingPair(action, key)

		print "Loaded key mappings:"
		print self.mapping

	def _addMappingPair(self, action, key):
		if not action in self.mapping:
			self.mapping[action] = key
		else:
			print "[ERR] The action \"%s\" is already configured. Ignoring this one." % action
