#!/usr/bin/python
# -*- coding: latin-1 -*-

# Reggie Next - Level Editor
# Version 1.0.0 "Amp"
# Copyright (C) 2009-2015 Treeki, Tempus, angelsl, JasonP27, Kamek64,
# MalStar1000, RoadrunnerWMC

# This file is part of Reggie Next.

# Reggie Next is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Reggie Next is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Reggie Next.  If not, see <http://www.gnu.org/licenses/>.


# api.py
# The accessible API for Reggie Next


################################################################
################################################################

import os

from PyQt5 import QtWidgets, QtGui, QtCore

import reggienext


# Enums
DIMENSIONS_2D = 1
DIMENSIONS_3D = 2



class RLevel:
    """
    Class that defines an abstract level - 2D or 3D.
    """
    # Static properties
    DIMENSIONS = None
    ICON = None
    TYPE_NAME = ''
    TEMPLATES = ()
    FILE_EXTENSION = 'bin'

    itemTypes = ()


    @classmethod
    def initClass(cls):
        """
        Initialize the level class.
        """
        cls.itemTypes = []


    def __init__(self, template=None):
        """
        Initialize the level instance.
        """
        ...


    @staticmethod
    def validate(data):
        """
        Return True if the data appears to encode a level of this type; False otherwise.
        Should be very fast in execution, yet robust enough to distinguish correctly most
        of the time.
        """
        return False


    @classmethod
    def loadFromBytes(cls, data):
        """
        Load the level from binary data
        """
        pass


    def save(self):
        """
        Save the level to binary data
        """
        return b''


    @classmethod
    def addItemType(cls, t):
        """
        Class method. Add a type of item to the class.
        """
        cls.itemTypes.append(t)



class RLevel_2D(RLevel):
    """
    Class that defines an abstract 2D level.
    """
    # Static properties
    DIMENSIONS = DIMENSIONS_2D



class RLevelItem_2D(QtWidgets.QGraphicsItem):
    """
    Class that defines an abstract 2D level item.
    """
    SORT = 0

    def __init__(self):
        """
        Initialize the item
        """
        ...



class RLevelTemplate:
    """
    Class that defines a template for a new level.
    """
    NAME = ''



################################################################
############ Publicly Accessible Top-Level Functions ###########
################################################################



def rAddLevelType(levelType):
    return currentGameObj.addLevelType(levelType)



def rSetGameIcon(ico):
    currentGameObj.gameIcon = ico


def rSetGameName(n):
    currentGameObj.gameName = n


def rIcon(name):
    return currentGameObj.getIcon(name)



def _(*args):
    return reggienext._(*args)



################################################################
################################################################
############ FOR INTERNAL USE BY REGGIENEXT.PY ONLY! ###########
################################################################
################################################################



currentGameObj = None



class _GameObj:
    """
    Stores values set by a game module via the RN API
    """
    def __init__(self, moduleID, clone=None):
        """
        Initialize the _GameObj
        """
        self.moduleID = moduleID
        if clone:
            self.cloneFrom(clone)
        else:
            self.new()


    def cloneFrom(self, other):
        """
        Clone this game obj from other
        """
        self.parentObj = other

        self.gameIcon = other.gameIcon
        self.gameName = other.gameName
        self.levelTypes = list(other.levelTypes)


    def new(self):
        """
        Set up a new game obj
        """
        self.parentObj = None

        self.gameIcon = None
        self.gameName = ''
        self.levelTypes = []


    def getFile(self, name):
        """
        Return the path to the most specific copy of the file given by file
        """
        # Inefficient, but works...
        return self.getFiles(name)[-1]


    def getFiles(self, name):
        """
        Return a list containing paths to copies of the file, least-to-most specific
        """
        if self.parentObj is not None:
            initialList = self.parentObj.getFiles(name)
        else:
            initialList = []

        possibleFP = os.path.join('gameinfo', self.moduleID, name)
        if os.path.isfile(possibleFP):
            initialList.append(possibleFP)

        return initialList


    def getIcon(self, name):
        """
        Get the icon called name
        """
        smallFP = os.path.join('ico', 'sm', 'icon-' + name + '.png')
        largeFP = os.path.join('ico', 'lg', 'icon-' + name + '.png')
        icon = QtGui.QIcon()
        icon.addFile(self.getFile(smallFP))
        icon.addFile(self.getFile(largeFP))
        return icon


    def addLevelType(self, t):
        """
        Add a level type to the game
        """
        self.levelTypes.append(t)
        t.initClass()



def _getGameObj():
    """
    Return the current _GameObj
    """
    return currentGameObj




def _newGameObj(moduleID, clone=None):
    """
    Create a new _GameObj by cloning "clone"
    """
    global currentGameObj
    currentGameObj = _GameObj(moduleID, clone)
