# Module for the abstract NSMB series.

from PyQt5 import QtWidgets, QtGui, QtCore

import rn_api



class Level_NSMB_Abstract(rn_api.RLevel_2D):
    """
    Class for an abstract NSMB level.
    """

    STRUCT_SPRITES = None

    @classmethod
    def initClass(cls):
        """
        Sets up the level class.
        """
        super().initClass()
        ...


    def __init__(self, template=None):
        """
        Initialize the abstract NSMB level
        """
        super().__init__()



class SpriteItem_NSMB_Abstract(rn_api.RLevelItem_2D):
    """
    Class for an abstract sprite.
    """
    def __init__(self):
        """
        Initialize the abstract sprite
        """
        super().__init__()



def main():
    """
    Set up the module
    """
    pass
