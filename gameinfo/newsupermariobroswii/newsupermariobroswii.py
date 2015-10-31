# Module for NSMBW.

import struct

from PyQt5 import QtWidgets, QtGui, QtCore

import rn_api
import parentModule



class LevelTemplate_NSMBW_Blank(rn_api.RLevelTemplate):
    NAME = rn_api._('Blank level')



class Level_NSMBW(parentModule.Level_NSMB_Abstract):
    """
    Class for a NSMBW level.
    """
    ICON = rn_api.rIcon('nsmbw')
    TYPE_NAME = rn_api._('New Super Mario Bros. Wii Level')
    TEMPLATES = (
        LevelTemplate_NSMBW_Blank(),
        )
    FILE_EXTENSION = 'arc'

    BLOCK_SPRITES = 7


    @classmethod
    def initClass(cls):
        """
        Sets up the level class.
        """
        super().initClass()
        cls.addItemType(SpriteItem_NSMBW)


    def __init__(self, template=None):
        """
        Initialize the NSMBW Level
        """
        super().__init__()


    @staticmethod
    def validate(data):
        """
        Return True if the data appears to encode a NSMBW level; False otherwise
        """
        return data.startswith(b'U\xAA8-') # not robust at all, but works for now


    @classmethod
    def loadFromBytes(cls, data):
        """
        Return a new Level_NSMBW representing the archive data
        """
        level = cls()

        return level



class SpriteItem_NSMBW(parentModule.SpriteItem_NSMB_Abstract):
    """
    Class for a sprite from NSMBW.
    """
    def __init__(self):
        """
        Initialize the sprite
        """
        super().__init__()



def main():
    """
    Set up the module
    """
    rn_api.rSetGameName(rn_api._('New Super Mario Bros. Wii'))
    rn_api.rSetGameIcon(rn_api.rIcon('nsmbw'))

    rn_api.rAddLevelType(Level_NSMBW)
