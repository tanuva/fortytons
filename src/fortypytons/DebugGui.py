from direct.gui.OnscreenText import OnscreenText

class DebugGui:
    def __init__(self):
        self.engineRpm = OnscreenText(text = 'XXXX', pos = (-0.5, 0.02), scale = 0.07, mayChange = True)
    #engineTorque = OnscreenText(text = 'XXXX', pos = (-0.5, 0.02), scale = 0.07, mayChange = True)
    
    def update(self, engineRpm):
        self.engineRpm['text'] = str(engineRpm)
