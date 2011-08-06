'''
Created on 06.08.2011

@author: marcel
'''

from pandac.PandaModules import Quat

class VComponent:
    '''
    classdocs
    '''
    def __init__(self, npMesh, npWire, mass, body, geom):
        '''
        Constructor
        '''
        self.npTruckMdl = npMesh
        self.npWire = npWire
        self.mass = mass
        self.body = body
        self.geom = geom
        
    def update(self):
        self.npTruckMdl.setPosQuat(self.body.getPosition(), Quat(self.body.getQuaternion()))
        self.npWire.setPosQuat(self.body.getPosition(), Quat(self.body.getQuaternion()))
        
    def addForce(self, x, y, z):
        self.body.addForce(x, y, z)
    
    def getBody(self):
        return self.body
    def getNp(self):
        return self.npTruckMdl
    
#==============================================================
class VChassis(VComponent):
    def update(self):
        VComponent.update(self)
        self.npTruckMdl.setZ(self.npTruckMdl.getZ()+0.1) # fix the geom/model offset temporarily

#==============================================================
class VWheel(VComponent):
    '''
    classdocs
    '''

    def __init__(self, npMesh, npWire, mass, body, geom, susp):
        '''
        Constructor
        '''
        VComponent.__init__(self, npMesh, npWire, mass, body, geom)
        self.susp = susp
    
    def steer(self, direction, torque):
        self.susp.setParamFMax(0, torque)
        self.susp.setParamVel(0, 5 * direction)
        
    def accel(self, force):
        self.susp.setParamFMax(1, force)
        self.susp.setParamVel(1, 50)
        print "accel"
    
    def brake(self, force):
        self.susp.setParamFMax(1, force)
        self.susp.setParamVel(1, 0)
        print "brake"