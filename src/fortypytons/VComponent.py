'''
Created on 06.08.2011

@author: marcel
'''

class VComponent:
    def __init__(self, meshNp, bodyNp):
        self.meshNp = meshNp
        self.bodyNp = bodyNp

    def getBodyNp(self):
        return self.bodyNp
    def getMeshNp(self):
        return self.meshNp
    def getPos(self):
        return self.bodyNp.getPos()
    def setPos(self, pos):
        self.bodyNp.setPos(pos)
    def setR(self, rot):
        self.bodyNp.setR(rot)

class VConstraint:
    def __init__(self, constraint, controllable):
        self.constraint = constraint
        self.controllable = bool(controllable)

    def isControllable(self):
        return self.controllable

    def getConstraint(self):
        return self.constraint
