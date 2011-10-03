'''
Created on 06.08.2011

@author: marcel
'''

class VComponent:
    '''
    classdocs
    '''
    def __init__(self, npMesh, npBody):
        '''
        Constructor
        '''
        self.npTruckMdl = npMesh
        self.body = npBody

    def update(self):
        print "shouldn't call update anymore"
        pass

    def addForce(self, x, y, z):
        print "addForce: NYI"

    def getBody(self):
        return self.body
    def getNp(self):
        return self.npTruckMdl
    def getPos(self):
        return self.body.getPos()
    def setPos(self, pos):
        self.body.setPos(pos)
    def setR(self, rot):
        self.body.setR(rot)

#==============================================================
class VChassis(VComponent):
    def update(self):
        VComponent.update(self)
        #self.npTruckMdl.setZ(self.npTruckMdl.getZ()+0.1) # fix the geom/model offset temporarily

#==============================================================
class VWheel(VComponent):
    '''
    classdocs
    '''

    def __init__(self, npMesh, npBody, wheel, isPowered):
        '''
        Constructor
        '''
        VComponent.__init__(self, npMesh, npBody)
        self._wheel = wheel
        self._isPowered = isPowered

    def steer(self, direction, torque):
        print "steer: NYI"

    def center(self):
        angle = 0.0
        print "center: NYI"

        if angle < 0.01 and angle > -0.01:
            self.steer(1, 0.0)
        if angle > 0.01:
            self.steer(-1, 10.0)
        if angle < -0.01:
            self.steer(1, 10.0)

    def getWheel(self):
        return self._wheel

    def isPowered(self):
        return self._isPowered
    def isSteerable(self):
        return self.wheel.getFrontWheel()
