'''
Created on 14.08.2011

@author: marcel
'''

from direct.gui.DirectGui import DirectButton, DirectLabel
from panda3d.core import Point3

class TuningGui:
    '''
    classdocs
    '''

    guiOffset = Point3(.8, 0, .8)

    """
    wheel.setMaxSuspensionTravelCm(30.0)
    wheel.setSuspensionStiffness(60.0)
    wheel.setWheelsDampingRelaxation(2.3)
    wheel.setWheelsDampingCompression(4.4)
    wheel.setFrictionSlip(100.0)

    wheel.setRollInfluence(0.1)

     	setMaxSuspensionTravelCm (float value)
        setSuspensionStiffness (float value)
 	setSuspensionDamping (float value)
 	setSuspensionCompression (float value)
 	setFrictionSlip (float value)

 	setMaxSuspensionForce (float value)
    """

    guiElms = []

    def __init__(self, tuning):
        '''
        Constructor
        '''

        self.tuning = tuning

        self.guiElms.append(self.createSettingElement(Point3(0,0,0), "SuspStiff",
                                  self.tuning.getSuspensionStiffness,
                                  self.suspStiffP,
                                  self.suspStiffM))
        self.guiElms.append(self.createSettingElement(Point3(0,0,-.1), "MaxSuspForce",
                                  self.tuning.getMaxSuspensionForce,
                                  self.suspForceP,
                                  self.suspForceM))
        self.guiElms.append(self.createSettingElement(Point3(0,0,-.2), "MaxSuspTravel",
                                  self.tuning.getMaxSuspensionTravelCm,
                                  self.suspTravelP,
                                  self.suspTravelM))
        self.guiElms.append(self.createSettingElement(Point3(0,0,-.3), "SuspDamp",
                                  self.tuning.getSuspensionDamping,
                                  self.suspDampP,
                                  self.suspDampM))
        self.guiElms.append(self.createSettingElement(Point3(0,0,-.4), "SuspComp",
                                  self.tuning.getSuspensionCompression,
                                  self.suspCompP,
                                  self.suspCompM))
        self.guiElms.append(self.createSettingElement(Point3(0,0,-.5), "FrictionSlip",
                                  self.tuning.getFrictionSlip,
                                  self.frictionSlipP,
                                  self.frictionSlipM))
        self.updateLabels()


    def createSettingElement(self, relPos, settingName, getter, plus, minus):
        # Absolute TopLeft position of this component + Offset for the whole bunch
        absPos = relPos + Point3(-1.1, 0, .95)
        
        lblDescr = DirectLabel(text = settingName, scale = .05, pos = (absPos))
        btnPlus  = DirectButton(text = "[+]", scale = .05, pos = (absPos + Point3(.2, 0, 0)), command = plus)
        lblVal   = DirectLabel(text = "xxxx", scale = .05, pos = (absPos + Point3(.3, 0, 0)))
        btnMinus = DirectButton(text = "[-]", scale = .05, pos = (absPos + Point3(.4, 0, 0)), command = minus)
        return (lblDescr, btnPlus, lblVal, btnMinus, getter)

    def updateLabels(self):
        """
        Update the caption for every label.
        """
        for e in self.guiElms:
            lblVal, getter = e[2], e[4] # See createSettingElement return value
            lblVal["text"] = "%.1f" % getter()

    def suspTravelP(self):
        self.tuning.setMaxSuspensionTravelCm(self.tuning.getMaxSuspensionTravelCm() + 5.0)
        self.updateLabels()
    def suspTravelM(self):
        self.tuning.setMaxSuspensionTravelCm(self.tuning.getMaxSuspensionTravelCm() - 5.0)
        self.updateLabels()
    def suspForceP(self):
        self.tuning.setMaxSuspensionForce(self.tuning.getMaxSuspensionForce() + 50.0)
        self.updateLabels()
    def suspForceM(self):
        self.tuning.setMaxSuspensionForce(self.tuning.getMaxSuspensionForce() - 50.0)
        self.updateLabels()
    def suspStiffP(self):
        self.tuning.setSuspensionStiffness(self.tuning.getSuspensionStiffness() + 1.0)
        self.updateLabels()
    def suspStiffM(self):
        self.tuning.setSuspensionStiffness(self.tuning.getSuspensionStiffness() - 1.0)
        self.updateLabels()
    def suspDampP(self):
        self.tuning.setSuspensionDamping(self.tuning.getSuspensionDamping() + 0.1)
        self.updateLabels()
    def suspDampM(self):
        self.tuning.setSuspensionDamping(self.tuning.getSuspensionDamping() - 0.1)
        self.updateLabels()
    def suspCompP(self):
        self.tuning.setSuspensionCompression(self.tuning.getSuspensionCompression() + 0.1)
        self.updateLabels()
    def suspCompM(self):
        self.tuning.setSuspensionCompression(self.tuning.getSuspensionCompression() - 0.1)
        self.updateLabels()
    def frictionSlipP(self):
        self.tuning.setFrictionSlip(self.tuning.getFrictionSlip() + 0.1)
        self.updateLabels()
    def frictionSlipM(self):
        self.tuning.setFrictionSlip(self.tuning.getFrictionSlip() - 0.1)
        self.updateLabels()

