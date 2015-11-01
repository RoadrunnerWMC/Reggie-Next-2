#!/usr/bin/env python3
# -*- coding: latin-1 -*-
"""
Reggie Next - Level Editor
Version 1.0.0 "Amp"
Copyright (C) 2009-2015 RoadrunnerWMC, Treeki, Tempus, angelsl,
JasonP27, Kamek64, MalStar1000

This file is part of Reggie Next.

Reggie Next is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Reggie Next is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Reggie Next.  If not, see <http://www.gnu.org/licenses/>.


reggienext.py
This is the main executable for Reggie Next.
"""


# Standard-library imports
import importlib
import importlib.machinery
import os
import sys
from xml.etree import ElementTree as etree


# Third-party imports:
# PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets, QtOpenGL
Qt = QtCore.Qt
# PyOpenGL
from OpenGL import GL, GLU



# Local imports
import rn_api


# Constants
REGGIE_ID = 'Reggie Next by Treeki, Tempus, RoadrunnerWMC'
REGGIE_VERSION = 'Version 1.0.0 "Amp"'
REGGIE_VERSION_SHORT = '1.0.0'
WEBSITE_URL = 'http://reggienext.nsmbwii.com/'
UPDATES_URL = WEBSITE_URL + 'updates.xml'
USER_AGENT = 'ReggieNext/' + REGGIE_VERSION_SHORT + ' (' + WEBSITE_URL + ')'
MEDIAWIKI_APIS = {
    'MarioWiki': 'http://www.mariowiki.com/api.php',
    }


# Globals
app = None
appPath = None
abstractGameModules = {}
gameModules = {}
iconCache = {}
gameHierarchy = []


# This enables itemChange being called on QGraphicsItem
if not hasattr(QtWidgets.QGraphicsItem, 'ItemSendsGeometryChanges'):
    QtWidgets.QGraphicsItem.ItemSendsGeometryChanges = QtWidgets.QGraphicsItem.GraphicsItemFlag(0x800)


# Translation System

def _(english, *args):
    for i in range(len(args) // 2):
        english = english.replace(str(args[2 * i]), str(args[2 * i + 1]))
    return english

def _file(name):
    return None  # GetPath(name)



def getModulePath():
    """
    Get us Reggie Next's directory, even if we are frozen using
    cx_Freeze or some other building utility
    """
    if hasattr(sys, 'frozen'):
        return os.path.dirname(sys.executable)
    if __name__ == '__main__':
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    return None



def FilesAreMissing():
    """
    Check to see if any of the required files for Reggie Next are missing
    """
    requiredFolders = ['reggiedata', 'lib']
    if not all(map(os.path.isdir, requiredFolders)):
        QtWidgets.QMessageBox.warning(
            None, _('Error'),
            _('Sorry, you seem to be missing the required data files for Reggie Next to work. Please redownload your copy of the editor.'),
            )
        return True

    required = ['icon.png', 'splash.png']
    missing = []

    for check in required:
        if not os.path.isfile('reggiedata/' + check):
            missing.append(check)

    if len(missing) > 0:
        QtWidgets.QMessageBox.warning(
            None, _('Error'),
            _(
                'Sorry, you seem to be missing some of the required data files for Reggie Next to work. Please redownload your copy of the editor. These are the files you are missing: [files]',
                '[files]', ', '.join(missing),
                ),
            )
        return True

    return False



def getIcon(name):
    """
    Return the icon named name
    """
    global iconCache

    if name in iconCache:
        return iconCache[name]

    icon = QtGui.QIcon()
    icon.addFile(os.path.join('reggiedata', 'ico', 'sm', 'icon-' + name + '.png'))
    icon.addFile(os.path.join('reggiedata', 'ico', 'lg', 'icon-' + name + '.png'))
    iconCache[name] = icon

    return icon



def loadGameModules():
    """
    Load all game modules for Reggie Next
    """
    global gameHierarchy

    class gameCategory:
        def __iter__(self):
            return self.iterator.__iter__()

    def parseCategory(cat):
        """
        Parse a category node and return a list of the contents
        """
        items = []

        # Go through all nodes in the category
        for node in cat:
            if node.tag.lower() == 'category':
                # Recursively load this category
                cat = gameCategory()
                cat.iterator = parseCategory(node)
                cat.id = node.attrib['id']
                items.append(cat)
            elif node.tag.lower() == 'game':
                # This is a concrete game
                thisID = node.attrib['id']
                parentID = node.attrib.get('parentid', False)
                items.append(thisID)

                if not parentID:
                    gameModules[thisID] = loadModule(thisID)
                elif parentID in abstractGameModules:
                    gameModules[thisID] = loadModule(thisID, abstractGameModules[parentID])
                elif parentID in gameModules:
                    gameModules[thisID] = loadModule(thisID, gameModules[parentID])
            elif node.tag.lower() == 'abstractgame':
                # This is an abstract game; load it, but
                # don't add it to the hierarchy.
                thisID = node.attrib['id']
                abstractGameModules[thisID] = loadModule(thisID)

        return tuple(items)


    root = etree.parse(os.path.join('gameinfo', 'games.xml')).getroot()
    gameHierarchy = parseCategory(root)



def loadModule(moduleID, parentObj=None):
    """
    Create and return the game obj for the module
    """
    # Create a new game obj to store info about the game
    rn_api._newGameObj(moduleID, parentObj)

    # Allow the module to "import parentModule"
    if parentObj is not None:
        sys.modules['parentModule'] = parentObj.module

    # Import the module from the gameinfo folder
    loader = importlib.machinery.SourceFileLoader(moduleID, os.path.join('gameinfo', moduleID, moduleID + '.py'))
    module = loader.load_module()
    module.main()

    # Clean up by removing "import parentModule"
    if parentObj is not None:
        del sys.modules['parentModule']

    # Get the gameObj, and add a couple of attrubites
    gameObj = rn_api._getGameObj()
    gameObj.module = module

    return gameObj



class ListWidgetItem_SortsByOther(QtWidgets.QListWidgetItem):
    """
    A ListWidgetItem that defers sorting to another object.
    """
    def __init__(self, reference, text=''):
        super().__init__(text)
        self.setData(Qt.UserRole + 10, reference)
    def __lt__(self, other):
        thisReference = self.data(Qt.UserRole + 10)
        otherReference = other.data(Qt.UserRole + 10)
        try:
            return thisReference < otherReference
        except TypeError:
            return False



class NewLevelDialog(QtWidgets.QDialog):
    """
    Dialog that lets the user choose a game and level type
    """
    def __init__(self, parent):
        """
        Initialize the dialog
        """
        super().__init__(parent)
        self.setWindowTitle(_('New Level'))
        self.setWindowIcon(getIcon('new'))
        self.setMinimumHeight(384)

        # Create the choose game section
        self.gameChooser = QtWidgets.QTreeWidget()
        self.gameChooser.setHeaderHidden(True)
        self.gameChooser.setAnimated(True)
        self.gameChooser.setIconSize(QtCore.QSize(24, 24))
        self.gameChooser.itemSelectionChanged.connect(self.handleGameChanged)

        def addViaFunction(category, addFxn):
            """
            Add items from the category via addFxn().
            """
            for iterItem in category:
                item = QtWidgets.QTreeWidgetItem()
                if isinstance(iterItem, str):
                    # Game
                    item.setText(0, gameModules[iterItem].gameName)
                    if gameModules[iterItem].gameIcon:
                        item.setIcon(0, gameModules[iterItem].gameIcon)
                    item.setData(0, Qt.UserRole, iterItem)
                else:
                    # Category
                    item.setText(0, iterItem.id)
                    item.setFlags(Qt.ItemIsEnabled)
                    addViaFunction(iterItem, item.addChild)
                addFxn(item)

        addViaFunction(gameHierarchy, self.gameChooser.addTopLevelItem)

        chooseGameLayout = QtWidgets.QVBoxLayout()
        chooseGameLayout.addWidget(self.gameChooser)
        chooseGameWidget = QtWidgets.QGroupBox('Choose a Game:')
        chooseGameWidget.setLayout(chooseGameLayout)

        # Create the level type section
        self.levelChooser = QtWidgets.QListWidget()
        self.levelChooser.itemSelectionChanged.connect(self.handleLevelChanged)

        chooseLevelLayout = QtWidgets.QVBoxLayout()
        chooseLevelLayout.addWidget(self.levelChooser)
        chooseLevelWidget = QtWidgets.QGroupBox('Choose a Level Type:')
        chooseLevelWidget.setLayout(chooseLevelLayout)

        # Create the template section
        self.templateChooser = QtWidgets.QListWidget()

        chooseTemplateLayout = QtWidgets.QVBoxLayout()
        chooseTemplateLayout.addWidget(self.templateChooser)
        chooseTemplateWidget = QtWidgets.QGroupBox('Choose a Template:')
        chooseTemplateWidget.setLayout(chooseTemplateLayout)

        # Create the button box
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        # Create the main layout
        L = QtWidgets.QGridLayout(self)
        L.addWidget(chooseGameWidget, 0, 0)
        L.addWidget(chooseLevelWidget, 0, 1)
        L.addWidget(chooseTemplateWidget, 0, 2)
        L.addWidget(self.buttonBox, 1, 0, 1, 3)


    def handleGameChanged(self):
        """
        Handle the game being changed
        """
        selectedId = self.gameChooser.currentItem().data(0, Qt.UserRole)

        self.levelChooser.clear()
        if selectedId is None: return
        levels = gameModules[selectedId].levelTypes

        for level in levels:
            item = QtWidgets.QListWidgetItem()
            item.setText(level.TYPE_NAME)
            item.setIcon(level.ICON)
            item.setData(Qt.UserRole, levels.index(level))
            self.levelChooser.addItem(item)

        # Select the first item; save the user a click :)
        self.levelChooser.setCurrentItem(self.levelChooser.item(0))


    def handleLevelChanged(self):
        """
        Handle the level being changed
        """
        selectedId = self.gameChooser.currentItem().data(0, Qt.UserRole)
        selectedIdIdx = self.levelChooser.currentItem().data(Qt.UserRole)

        self.templateChooser.clear()
        if selectedIdIdx is None: return
        level = gameModules[selectedId].levelTypes[selectedIdIdx]

        for template in level.TEMPLATES:
            item = QtWidgets.QListWidgetItem()
            item.setText(template.NAME)
            item.setData(Qt.UserRole, level.TEMPLATES.index(template))
            self.templateChooser.addItem(item)

        # Select the first item; save the user a click :)
        self.templateChooser.setCurrentItem(self.templateChooser.item(0))


    def getSelectedInfo(self):
        """
        Returns the current template info
        """
        selectedId = self.gameChooser.currentItem().data(0, Qt.UserRole)
        selectedIdIdx = self.levelChooser.currentItem().data(Qt.UserRole)
        selectedTemplateIdx = self.templateChooser.currentItem().data(Qt.UserRole)

        return (gameModules[selectedId],
            gameModules[selectedId].levelTypes[selectedIdIdx],
            gameModules[selectedId].levelTypes[selectedIdIdx].TEMPLATES[selectedTemplateIdx],
            )


class ScreenshotDialog(QtWidgets.QDialog):
    """
    Dialog for choosing screenshot settings
    """
    ...



class ZoomWidget(QtWidgets.QWidget):
    """
    Widget that allows easy zoom level control
    """
    MAX_WIDTH = 384
    MAX_HEIGHT = 20
    ZOOM_LEVELS = (
        7.5,
        10.0,
        25.0,
        40.0,
        50.0,
        60.0,
        75.0,
        85.0,
        100.0,  # Keep this in the center!
        125.0,
        150.0,
        175.0,
        200.0,
        250.0,
        300.0,
        350.0,
        400.0,
        )

    zoomChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent):
        """
        Create and initialize the widget
        """
        super().__init__(parent)
        self.mainWindow = parent  # This often gets re-parented to the statusbar
        self.subject = None

        # Make and configure the slider
        self.slider = QtWidgets.QSlider(Qt.Horizontal)

        self.slider.setMaximumHeight(self.MAX_HEIGHT)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.ZOOM_LEVELS) - 1)
        self.slider.setTickInterval(2)
        self.slider.setTickPosition(self.slider.TicksAbove)
        self.slider.setPageStep(1)
        self.slider.setTracking(True)
        self.slider.valueChanged.connect(self.handleSliderMoved)

        # Make and configure the buttons
        self.minBtn = QtWidgets.QToolButton(self)
        self.minusBtn = QtWidgets.QToolButton(self)
        self.plusBtn = QtWidgets.QToolButton(self)
        self.maxBtn = QtWidgets.QToolButton(self)

        self.minBtn.setIcon(getIcon('zoommin'))
        self.minusBtn.setIcon(getIcon('zoomout'))
        self.plusBtn.setIcon(getIcon('zoomin'))
        self.maxBtn.setIcon(getIcon('zoommax'))
        self.minBtn.setAutoRaise(True)
        self.minusBtn.setAutoRaise(True)
        self.plusBtn.setAutoRaise(True)
        self.maxBtn.setAutoRaise(True)
        self.minBtn.clicked.connect(self.handleZoomMin)
        self.minusBtn.clicked.connect(self.handleZoomOut)
        self.plusBtn.clicked.connect(self.handleZoomIn)
        self.maxBtn.clicked.connect(self.handleZoomMax)
        self.minBtn.setToolTip(_('Zoom to Minimum'))
        self.minusBtn.setToolTip(_('Zoom In'))
        self.plusBtn.setToolTip(_('Zoom Out'))
        self.maxBtn.setToolTip(_('Zoom to Maximum'))

        # Make and configure the current-zoom-level button
        self.currentBtn = QtWidgets.QToolButton(self)
        self.currentBtn.setAutoRaise(True)
        self.currentBtn.clicked.connect(self.handleZoom100)
        self.currentBtn.setToolTip(_('Zoom to 100%'))

        # Set the slider position
        self.slider.setSliderPosition(self.slider.maximum() / 2)

        # Create a layout
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addWidget(self.minBtn)
        self.layout.addWidget(self.minusBtn)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.plusBtn)
        self.layout.addWidget(self.maxBtn)
        self.layout.addWidget(self.currentBtn)
        self.layout.setContentsMargins(0, 0, 4, 0)

        # Crush this into a small space so it'll fit on the statusbar
        self.setMinimumWidth(self.MAX_WIDTH)
        self.setMaximumWidth(self.MAX_WIDTH)
        self.setMaximumHeight(self.MAX_HEIGHT)


    def handleZoomMin(self):
        """
        Handle any command to zoom to minimum
        """
        self.slider.setSliderPosition(0)


    def handleZoomIn(self):
        """
        Handle any command to zoom in
        """
        self.slider.setSliderPosition(self.slider.sliderPosition() + self.slider.singleStep())


    def handleZoom100(self):
        """
        Handle any command to zoom to 100%
        """
        self.slider.setSliderPosition(self.slider.maximum() / 2)


    def handleZoomOut(self):
        """
        Handle any command to zoom out
        """
        self.slider.setSliderPosition(self.slider.sliderPosition() - self.slider.singleStep())


    def handleZoomMax(self):
        """
        Handle any command to zoom to maximum
        """
        self.slider.setSliderPosition(self.slider.maximum())


    def handleSliderMoved(self):
        """
        Handle the slider being moved
        """
        newLevel = self.ZOOM_LEVELS[self.slider.value()]
        if self.subject is not None:
            self.subject.setZoom(newLevel / 100)
        self.updateButtons(newLevel)

        self.zoomChanged.emit(newLevel / 100)


    def updateButtons(self, newLevel):
        """
        Enable/disable the buttons on the widget, depending on
        if newLevel is a maximum zoom, a minimum zoom, or neither
        """
        isMinimum = newLevel == self.ZOOM_LEVELS[0]
        isMaximum = newLevel == self.ZOOM_LEVELS[-1]
        is100 = newLevel == self.ZOOM_LEVELS[len(self.ZOOM_LEVELS) // 2]

        self.minBtn.setEnabled(not isMinimum)
        self.minusBtn.setEnabled(not isMinimum)
        self.plusBtn.setEnabled(not isMaximum)
        self.maxBtn.setEnabled(not isMaximum)

        self.mainWindow.actions['zoommin'].setEnabled(not isMinimum)
        self.mainWindow.actions['zoomout'].setEnabled(not isMinimum)
        self.mainWindow.actions['zoom100'].setEnabled(not is100)
        self.mainWindow.actions['zoomin'].setEnabled(not isMaximum)
        self.mainWindow.actions['zoommax'].setEnabled(not isMaximum)

        # Remove trailing ".0" if possible
        if float(int(newLevel)) == float(newLevel):
            self.currentBtn.setText(_('[zoom]%', '[zoom]', str(int(newLevel))))
        else:
            self.currentBtn.setText(_('[zoom]%', '[zoom]', str(float(newLevel))))


    def forceSetZoom(self, newZoom):
        """
        Force-set the zoom level.
        """
        self.slider.setSliderPosition(self.ZOOM_LEVELS.index(newZoom * 100))



class TabStackWidget(QtWidgets.QWidget):
    """
    Widget that contains multiple widgets in a stack,
    and some tabs for accessing them
    """
    updateStatusbarText = QtCore.pyqtSignal(str, str, str)
    tabSwitched = QtCore.pyqtSignal()

    mainWindow = None
    zoomWidget = None

    def __init__(self, mainWindow):
        """
        Initialize the widget
        """
        super().__init__(mainWindow)
        self.mainWindow = mainWindow

        # Set up the stack
        self.viewStack = QtWidgets.QStackedLayout()

        # Set up the tabs
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setShape(self.tabs.TriangularNorth)
        self.tabs.setTabsClosable(True)
        self.tabs.setIconSize(QtCore.QSize(24, 24))
        self.tabs.setMovable(True)
        self.tabs.currentChanged.connect(self.handleCurrentChanged)
        self.tabs.tabCloseRequested.connect(self.handleTabClose)
        self.tabs.tabMoved.connect(self.handleTabMove)

        # Create the layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.layout.addWidget(self.tabs)
        self.layout.addLayout(self.viewStack)


    def setZoomWidget(self, zoomWidget):
        """
        Sets the zoom widget for the tab stack.
        """
        self.zoomWidget = zoomWidget
        self.zoomWidget.zoomChanged.connect(self.handleZoomChangedBySlider)


    def handleZoomChangedBySlider(self, newZoom):
        """
        Handle the user setting a new zoom level via the slider.
        """
        self.currentWidget().setZoom(newZoom)


    def handleZoomChangedByTab(self, newZoom):
        """
        Handle the current tab requesting a new zoom level.
        """
        self.zoomWidget.forceSetZoom(newZoom)


    def handleStatusbarUpdateRequest(self):
        """
        A tab requested an update to the statusbar text.
        """
        cw = self.currentWidget()
        self.updateStatusbarText.emit(cw.statusbarPosition, cw.statusbarSelection, cw.statusbarHover)


    def addTab(self, widget, switchTo=False):
        """
        Add a new level entry
        """
        currentIdx = self.tabs.currentIndex()

        self.viewStack.insertWidget(currentIdx + 1, widget)

        self.tabs.insertTab(currentIdx + 1, widget.name)
        self.tabs.setTabIcon(currentIdx + 1, widget.icon)
        self.tabs.setTabToolTip(currentIdx + 1, widget.toolTip)

        widget.updateZoom.connect(self.handleZoomChangedByTab)
        widget.updateStatusbar.connect(self.handleStatusbarUpdateRequest)

        if switchTo:
            self.tabs.setCurrentIndex(currentIdx + 1)


    def currentWidget(self):
        """
        Wrapper around self.viewStack.currentWidget
        """
        return self.viewStack.currentWidget()


    def handleCurrentChanged(self, newIdx):
        """
        Handle the user changing the current tab
        """
        self.viewStack.setCurrentIndex(newIdx)
        self.tabSwitched.emit()

        cw = self.currentWidget()
        if self.zoomWidget is not None:
            self.zoomWidget.forceSetZoom(cw.getZoom())
        self.updateStatusbarText.emit(cw.statusbarPosition, cw.statusbarSelection, cw.statusbarHover)


    def handleTabClose(self, idx):
        """
        The user wants to close tab # idx, so let's do that.
        """
        self.tabs.removeTab(idx)
        self.viewStack.takeAt(idx)


    def handleTabMove(self, fromIdx, toIdx):
        """
        The user moved a tab from fromIdx to toIdx, so we need
        to update the viewStack.
        """
        self.viewStack.insertWidget(toIdx, self.viewStack.takeAt(fromIdx).widget())


    def getCurrentView(self):
        """
        Returns the current view
        """
        return self.currentWidget().getCurrentView()


    def allViewsIter(self):
        """
        Generator that iterates over all views
        """
        for i in range(self.viewStack.count()):
            w = self.viewStack.widget(i)
            for view in w.allViewsIter():
                yield view



class TabView(QtWidgets.QWidget):
    """
    Defines an API for a tab widget
    """
    updateZoom = QtCore.pyqtSignal(float)
    updateStatusbar = QtCore.pyqtSignal()

    zoom = 1
    icon = None
    name = None
    toolTip = ''

    statusbarPosition = ''
    statusbarSelection = ''
    statusbarHover = ''


    def __init__(self, mainWindow):
        """
        Initialize the TabView
        """
        super().__init__(mainWindow)
        self.mainWindow = mainWindow


    def getZoom(self):
        """
        Get the current zoom level
        """
        return self.zoom


    def setZoom(self, zoom):
        """
        Set the current zoom level
        """
        self.zoom = zoom


    def allViewsIter(self):
        """
        Iterate over all QGraphicsViews. Override this if you have some.
        """
        return []



class LevelScene(QtWidgets.QGraphicsScene):
    """
    QGraphicsScene subclass for a level scene
    """
    def __init__(self, x, y, w, h, parent):
        super().__init__(x, y, w, h, parent)
        self.setItemIndexMethod(self.NoIndex)

        self.bgbrush = QtGui.QColor(119, 136, 153)


    def drawBackground(self, painter, rect):
        """
        Draw the background for the level scene
        """
        painter.fillRect(rect, self.bgbrush)



class LevelViewWidget(QtWidgets.QGraphicsView):
    """
    QGraphicsView subclass for a level view
    """
    relativeZoom = 1
    tileZoom = 1

    PositionHover = QtCore.pyqtSignal(int, int)
    repaint = QtCore.pyqtSignal()
    dragstamp = False

    def __init__(self, scene, parent):
        """
        Constructor
        """
        super().__init__(scene, parent)

        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setMouseTracking(True)
        self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)

        self.YScrollBar = QtWidgets.QScrollBar(Qt.Vertical, parent)
        self.XScrollBar = QtWidgets.QScrollBar(Qt.Horizontal, parent)
        self.setVerticalScrollBar(self.YScrollBar)
        self.setHorizontalScrollBar(self.XScrollBar)

        self.currentitem = None
        self.gridType = 0  # 0 = None, 1 = dotted lines, 2 = solid lines, 3 = checkerboard
        self.gridColor = QtGui.QColor(255, 255, 255, 100)
        self.gridColorLight = QtGui.QColor(255, 255, 255, 10)
        self.gridColorDark = QtGui.QColor(255, 255, 255, 20)


    def zoomTiles(self, zoomLevel):
        """
        Zooms to a new tile size. 1 tile = (zoomLevel) pixels.
        """
        self.tileZoom = zoomLevel
        self.zoomRelativeToTiles()


    def zoomRelativeToTiles(self, zoomLevel=None):
        """
        Zooms to a new zoom level relative to the current tile size. 1 = 100% zoom.
        """
        if zoomLevel is None:
            zoomLevel = self.relativeZoom
        self.relativeZoom = zoomLevel

        absoluteZoom = self.tileZoom * self.relativeZoom

        tr = QtGui.QTransform()
        tr.scale(absoluteZoom, absoluteZoom)
        self.setTransform(tr)


    def mousePressEvent(self, event):
        """
        Overrides mouse pressing events if needed
        """
        if event.button() == Qt.LeftButton:
            # Left-click
            if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
                # Left-click + Shift key = add item to selection

                pos = self.mapToScene(event.x(), event.y())
                addsel = self.scene().items(pos)
                for i in addsel:
                    if (int(i.flags()) & i.ItemIsSelectable) != 0:
                        i.setSelected(not i.isSelected())
                        break

        elif event.button() == Qt.RightButton:
            # Right-click = paint an item
            pass
            event.accept()

            super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        """
        Overrides mouse movement events if needed
        """
        pos = self.mapToScene(event.x(), event.y())
        if pos.x() < 0:
            pos.setX(0)
        if pos.y() < 0:
            pos.setY(0)
        self.PositionHover.emit(int(pos.x()), int(pos.y()))

        if event.buttons() == Qt.RightButton and self.currentitem is not None and not self.dragstamp:
            # The user is dragging an item they just created.
            pass

        elif event.buttons() == Qt.RightButton and self.currentitem is not None and self.dragstamp:
            # The user is dragging a stamp - many objects.
            pass

        else:
            super().mouseMoveEvent(event)


    def mouseReleaseEvent(self, event):
        """
        Overrides mouse release events if needed
        """
        if event.button() == Qt.RightButton:
            self.currentitem = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)


    def paintEvent(self, e):
        """
        Handles paint events and fires a signal
        """
        self.repaint.emit()
        super().paintEvent(e)


    def drawForeground(self, painter, rect):
        """
        Draws a foreground grid
        """
        if self.gridType == 0:
            return

        startx = rect.x()
        endx = int(startx + rect.width() + 1)

        starty = rect.y()
        endy = int(starty + rect.height() + 1)

        if self.gridType in (1, 2):
            if self.gridType == 1:
                # Draw a grid with dashed lines.
                thickPen = QtGui.QPen(self.gridColor, 0.08, Qt.DashLine)
                medPen = QtGui.QPen(self.gridColor, 0.04, Qt.DashLine)
                thinPen = QtGui.QPen(self.gridColor, 0.04, Qt.DotLine)
            else:
                # Draw a grid with solid lines.
                thickPen = QtGui.QPen(self.gridColor, 0.12)
                medPen = QtGui.QPen(self.gridColor, 0.06)
                thinPen = QtGui.QPen(self.gridColor, 0.03)

            # Whatever type of lines we're using, let's draw them now.
            startx = int(startx)
            starty = int(starty)

            x = startx - 1
            while x <= endx:
                x += 1
                if x % 8 == 0:
                    painter.setPen(thickPen)
                    painter.drawLine(x, starty, x, endy)
                elif x % 4 == 0 and self.relativeZoom >= 0.25:
                    painter.setPen(medPen)
                    painter.drawLine(x, starty, x, endy)
                elif self.relativeZoom >= 0.5:
                    painter.setPen(thinPen)
                    painter.drawLine(x, starty, x, endy)

            y = starty - 1
            while y <= endy:
                y += 1
                if y % 8 == 0:
                    painter.setPen(thickPen)
                    painter.drawLine(startx, y, endx, y)
                elif y % 4 == 0 and self.relativeZoom >= 0.25:
                    painter.setPen(medPen)
                    painter.drawLine(startx, y, endx, y)
                elif self.relativeZoom >= 0.5:
                    painter.setPen(thinPen)
                    painter.drawLine(startx, y, endx, y)

        elif self.gridType == 3:
            # Draw a checkerboard-style grid

            painter.setPen(Qt.NoPen)
            startx = int(startx // 8) * 8
            starty = int(starty // 8) * 8

            painter.setBrush(QtGui.QBrush(self.gridColorLight))
            for y in range(starty, endy, 2):
                for x in range(startx, endx, 2):
                    painter.drawRect(x, y, 1, 1)
                    painter.drawRect(x + 1, y + 1, 1, 1)

            painter.setBrush(QtGui.QBrush(self.gridColorDark))
            for ytile in range(starty, endy, 8):
                for xtile in range(startx, endx, 8):
                    for y in range(ytile, ytile + 4, 2):
                        for x in range(xtile, xtile + 4, 2):
                            painter.drawRect(x, y + 1, 1, 1)
                            painter.drawRect(x + 1, y, 1, 1)
                            painter.drawRect(x + 4, y + 5, 1, 1)
                            painter.drawRect(x + 5, y + 4, 1, 1)


class TabView_2DLevel(TabView):
    """
    TabView subclass for a 2D level view, complete with area tabs
    """
    scenes = []
    views = []
    gameObj = None


    def __init__(self, mainWindow, levelObj):
        """
        Initialize the 2D Level Tab View
        """
        super().__init__(mainWindow)

        self.scenes = []
        self.views = []
        self.levelObj = levelObj

        self.icon = self.levelObj.ICON
        self.name = _('Untitled*')
        self.toolTip = _('(No file path)')

        # Create new area tabs
        self.tabs = QtWidgets.QTabBar()
        self.tabs.setExpanding(False)
        self.tabs.setShape(self.tabs.TriangularNorth)
        self.tabs.currentChanged.connect(self.handleCurrentAreaChanged)

        # Create the new stack layout
        self.stackLayout = QtWidgets.QStackedLayout()

        # Create the main layout
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        self.mainLayout.addWidget(self.tabs)
        self.mainLayout.addLayout(self.stackLayout)

        self.addTab()


    def addTab(self):
        """
        Add an area tab to the level
        """

        # Create the new scene
        self.scenes.append(LevelScene(0, 0, 64, 64, self))

        # Create the new view
        self.views.append(LevelViewWidget(self.scenes[-1], self))
        self.views[-1].centerOn(0, 0)  # This scrolls to the top left
        self.views[-1].zoomTiles(24)
        self.views[-1].gridType = self.mainWindow.setting('GridType', 1)
        self.views[-1].PositionHover.connect(self.handlePositionHoverInView)

        # Add the view to the stack layout
        self.stackLayout.addWidget(self.views[-1])

        self.tabs.addTab(_('Area [num]', '[num]', len(self.views)))


    def handlePositionHoverInView(self, x, y):
        """
        Handle the user hovering over a position in the view
        """
        self.statusbarPosition = _('([posx], [posy])', '[posx]', int(x), '[posy]', int(y))
        self.updateStatusbar.emit()


    def handleCurrentAreaChanged(self):
        """
        Handle the user clicking on a different area tab
        """
        self.stackLayout.setCurrentIndex(self.tabs.currentIndex())
        self.updateZoom.emit(self.getCurrentView().relativeZoom)


    def getCurrentView(self):
        """
        Returns the current level view
        """
        return self.views[self.tabs.currentIndex()]


    def allViewsIter(self):
        """
        Iterates over all views in this tab
        """
        return self.views


    def getZoom(self):
        return self.getCurrentView().relativeZoom


    def setZoom(self, value):
        super().setZoom(value)
        self.getCurrentView().zoomRelativeToTiles(value)



class TabView_TextEditor(TabView):
    """
    Tab view subclass for a simple plaintext editor
    """
    BASE_FONT_SIZE = 14

    def __init__(self, mainWindow):
        """
        Initializes the widget
        """
        super().__init__(mainWindow)

        self.icon = getIcon('edittext')
        self.name = _('test.txt')

        self.textEdit = QtWidgets.QPlainTextEdit(self)
        self.textEdit.cursorPositionChanged.connect(self.handleCursorPositionChanged)
        self.textEdit.selectionChanged.connect(self.handleSelectionChanged)

        self.font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self.font.setPointSize(self.BASE_FONT_SIZE * self.zoom)
        self.textEdit.setFont(self.font)

        L = QtWidgets.QVBoxLayout()
        L.setContentsMargins(0, 0, 0, 0)
        L.addWidget(self.textEdit)
        self.setLayout(L)

        # Set the "Line x, column x" statusbar label
        self.handleCursorPositionChanged()


    def handleCursorPositionChanged(self):
        """
        Handle the cursor's position being changed
        """
        line = self.textEdit.textCursor().blockNumber() + 1
        col = self.textEdit.textCursor().positionInBlock() + 1
        self.statusbarPosition = _('Line [line], Column [column]', '[line]', line, '[column]', col)
        self.updateStatusbar.emit()


    def handleSelectionChanged(self):
        """
        Handle the current selection changing
        """
        selTxt = self.textEdit.textCursor().selectedText().replace('\u2029', '\n')
        selLen = len(selTxt)
        selLines = selTxt.count('\n') + 1

        if selLen == 0:
            # No selection.
            self.statusbarSelection = ''
        elif selLen == 1:
            # Only one character.
            self.statusbarSelection = _('1 character selected')
        elif selLines == 1:
            # Only on one line.
            self.statusbarSelection = _('[chars] characters selected', '[chars]', selLen)
        else:
            # On multiple lines.
            self.statusbarSelection = _('[lines] lines, [chars] characters selected', '[lines]', selLines, '[chars]', selLen)
        self.updateStatusbar.emit()


    def setZoom(self, value):
        super().setZoom(value)
        self.font.setPointSize(self.BASE_FONT_SIZE * self.zoom)
        self.textEdit.setFont(self.font)



class LevelView3D(QtOpenGL.QGLWidget):
    """
    A 3D level view
    """
    zoom = 1

    def __init__(self, mainWindow):
        """
        Initialize the level view
        """
        super().__init__(mainWindow)
        self.mainWindow = mainWindow

        self.bgcolor = QtGui.QColor(119, 136, 153)


    def paintGL(self):
        """
        Paint the scene
        """

        normals = (
          (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0),
          (0.0, -1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, -1.0),
          )
        faces = (
          (0, 1, 2, 3), (3, 2, 6, 7), (7, 6, 5, 4),
          (4, 5, 1, 0), (5, 6, 2, 1), (7, 4, 0, 3),
          )
        vertices = (
            (-1, -1, 1), (-1, -1, -1), (-1, 1, -1), (-1, 1, 1),
            (1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1),
            )

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        for i in range(6):
            GL.glBegin(GL.GL_QUADS)
            GL.glNormal3f(*normals[i])
            GL.glVertex3f(*vertices[faces[i][0]])
            GL.glVertex3f(*vertices[faces[i][1]])
            GL.glVertex3f(*vertices[faces[i][2]])
            GL.glVertex3f(*vertices[faces[i][3]])
            GL.glEnd()


    def resizeGL(self, w, h):
        """
        Handle resize events.
        """
        self.width, self.height = w, h
        self.updateCamera()


    def updateCamera(self):
        """
        Updates the camera.
        """
        w, h = self.width, self.height
        thing = min(w, h)
        orthoW = 2 * (w / thing) / self.zoom
        orthoH = 2 * (h / thing) / self.zoom
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-orthoW, orthoW, -orthoH, orthoH, -50.0, 50.0)
        GL.glViewport(0, 0, w, h)


    def initializeGL(self):
        """
        Prepare the widget.
        """
        GL.glClearColor(self.bgcolor.red() / 255, self.bgcolor.green() / 255, self.bgcolor.blue() / 255, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        # Enable a single OpenGL light.
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_DIFFUSE, (1, 1, 1, 1))
        GL.glLightfv(GL.GL_LIGHT0, GL.GL_POSITION, (1, 1, 1, 0))
        GL.glEnable(GL.GL_LIGHT0)
        GL.glEnable(GL.GL_LIGHTING)

        # Use depth buffering for hidden surface elimination.
        GL.glEnable(GL.GL_DEPTH_TEST)

        # Setup the view of the cube.
        GL.glMatrixMode(GL.GL_PROJECTION)
        GLU.gluPerspective(40, 1, 1.0, 10)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GLU.gluLookAt(0.0, 0.0, 5.0,  # eye is at (0,0,5)
            0.0, 0.0, 0.0,            # center is at (0,0,0)
            0.0, 1.0, 0.)             # up is in positive Y direction

        # Adjust cube position to be asthetic angle.
        GL.glTranslatef(0.0, 0.0, -1.0)
        GL.glRotatef(60, 1.0, 0.0, 0.0)
        GL.glRotatef(-20, 0.0, 0.0, 1.0)



class TabView_3DLevel(TabView):
    """
    Experimental tab view for editing a 3D level.
    """
    def __init__(self, mainWindow):
        """
        Initialize the tab view
        """
        super().__init__(mainWindow)

        self.icon = getIcon('edittext')
        self.name = _('3D Level View')

        self.view = LevelView3D(self)

        L = QtWidgets.QVBoxLayout()
        L.setContentsMargins(0, 0, 0, 0)
        L.addWidget(self.view)
        self.setLayout(L)


    def setZoom(self, zoom):
        """
        Set a new zoom level.
        """
        super().setZoom(zoom)
        self.view.zoom = zoom
        self.view.updateCamera()
        self.view.update()



class TabView_ReggieNextSettings(TabView):
    """
    Tab view for editing Reggie Next settings
    """
    def __init__(self, parent):
        """
        Initialize the tab
        """
        super().__init__(parent)
        self.setObjectName('SettingsTab')
        self.name = _('Preferences')
        self.icon = getIcon('settings')
        self.setAttribute(QtCore.Qt.WA_StyledBackground)

        # Create the widget for each screen
        self.screens = (
            (_('Theme'), self.ThemeTab(self)),
            (_('Toolbar'), self.ToolbarTab(self)),
            (_('View'), self.ViewTab(self)),
            )

        # Create the category selector
        self.selector = QtWidgets.QListWidget()
        self.selector.setObjectName('SettingsTab_Selector')
        self.selector.selectionChanged = self.handleScreenChange
        self.selector.setMaximumWidth(256)

        # Create the stacked layout
        self.stackedLayout = QtWidgets.QStackedLayout()

        # Iterate over the screen widgets and add them
        for name, widget in self.screens:
            self.selector.addItem(name)
            self.stackedLayout.addWidget(widget)

        self.selector.setCurrentRow(0)

        # Create the main layout
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.selector, 0, 0)
        layout.addLayout(self.stackedLayout, 0, 1)


    def handleScreenChange(self, selected, deselected):
        """
        Change to a different Preferences screen
        """
        newIdx = selected.indexes()[0].row()
        self.stackedLayout.setCurrentIndex(newIdx)


    class ThemeTab(QtWidgets.QWidget):
        """
        Tab for choosing a theme
        """
        def __init__(self, parent):
            """
            Initialize the tab
            """
            super().__init__(parent)


    class ToolbarTab(QtWidgets.QWidget):
        """
        Tab for customizing the toolbar
        """
        separatorText = _('--- Separator ---')
        def __init__(self, parent):
            """
            Initialize the tab
            """
            super().__init__(parent)

            # Make the left side
            self.availableLabel = QtWidgets.QLabel(_('Available:'))

            self.availableList = self.QListWidget_NoInternalMove(self)
            self.availableList.setSortingEnabled(True)
            self.availableList.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
            self.availableList.setDefaultDropAction(Qt.MoveAction)
            self.availableList.setDragEnabled(True)
            self.availableList.setDropIndicatorShown(True)
            self.availableList.viewport().setAcceptDrops(True)
            self.availableList.eatSeparators = True

            self.separatorList = QtWidgets.QListWidget(self)
            self.separatorList.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)
            self.separatorList.setDragEnabled(True)
            self.separatorList.setMaximumHeight(32)
            self.separatorList.addItem(self.separatorText)

            # Make the right side
            self.onToolbarLabel = QtWidgets.QLabel(_('On Toolbar:'))

            self.onToolbarList = self.QListWidget_NoInternalMove(self)
            self.onToolbarList.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
            self.onToolbarList.setDefaultDropAction(Qt.MoveAction)
            self.onToolbarList.setDragEnabled(True)
            self.onToolbarList.setDropIndicatorShown(True)
            self.onToolbarList.viewport().setAcceptDrops(True)

            # Make the layout
            self.layout = QtWidgets.QGridLayout(self)
            self.layout.addWidget(self.availableLabel, 0, 0)
            self.layout.addWidget(self.onToolbarLabel, 0, 1)
            self.layout.addWidget(self.availableList, 1, 0)
            self.layout.addWidget(self.onToolbarList, 1, 1, 2, 1)
            self.layout.addWidget(self.separatorList, 2, 0)

            self.populateLists()


        def populateLists(self):
            """
            Adds items to the lists
            """
            actions = self.parent().parent().actions
            actionListIndices = self.parent().parent().actionListIndices

            for key in actions:
                item = ListWidgetItem_SortsByOther(actionListIndices[key], actions[key].text())
                item.setIcon(actions[key].icon())
                self.availableList.addItem(item)


        class QListWidget_NoInternalMove(QtWidgets.QListWidget):
            """
            A QListWidget that does not allow you to move items internally.
            Fixes an annoying bug that happens when you allow this behavior.
            """
            eatSeparators = False  # if True, separators will always be deleted instantly


            def dragMoveEvent(self, e):
                """
                Handle events for when the user drags something over the widget
                """
                if e.source() == self:
                    e.ignore()
                else:
                    e.accept()


            def dropEvent(self, e):
                """
                Handle events for when the user drops something onto the widget
                """
                super().dropEvent(e)

                if self.eatSeparators:
                    for item in self.findItems(self.parent().separatorText, Qt.MatchFixedString):
                        self.takeItem(self.indexFromItem(item).row())



    class ViewTab(QtWidgets.QWidget):
        """
        Tab for changing view options
        """
        def __init__(self, parent):
            """
            Initialize the tab
            """
            super().__init__(parent)

            # Tile View Size
            self.tileSize_Label = QtWidgets.QLabel(_('Tile View Size'))

            self.tileSize_RadioAuto = QtWidgets.QRadioButton(_('Recommended per game'))
            self.tileSize_RadioPreset = QtWidgets.QRadioButton(_('Preset:'))
            self.tileSize_RadioCustom = QtWidgets.QRadioButton(_('Custom:'))

            self.tileSize_RadioGroup = QtWidgets.QButtonGroup()
            self.tileSize_RadioGroup.addButton(self.tileSize_RadioAuto)
            self.tileSize_RadioGroup.addButton(self.tileSize_RadioPreset)
            self.tileSize_RadioGroup.addButton(self.tileSize_RadioCustom)

            self.tileSize_Preset = QtWidgets.QComboBox()
            self.tileSize_Preset.addItems((
                _('16x16 pixels'),
                _('20x20 pixels'),
                _('24x24 pixels'),
                _('30x30 pixels'),
                _('60x60 pixels'),
                ))

            self.tileSize_CustomSpin = QtWidgets.QSpinBox()
            self.tileSize_CustomSpin.setMinimum(2)
            self.tileSize_CustomSpin.setMaximum(128)

            self.tileSize_CustomLabel = QtWidgets.QLabel()

            # Set up layouts
            tileSizeLayout_Preset = QtWidgets.QHBoxLayout()
            tileSizeLayout_Preset.addWidget(self.tileSize_RadioPreset)
            tileSizeLayout_Preset.addWidget(self.tileSize_Preset)
            tileSizeLayout_Preset.addStretch()

            tileSizeLayout_Custom = QtWidgets.QHBoxLayout()
            tileSizeLayout_Custom.addWidget(self.tileSize_RadioCustom)
            tileSizeLayout_Custom.addWidget(self.tileSize_CustomSpin)
            tileSizeLayout_Custom.addWidget(self.tileSize_CustomLabel)
            tileSizeLayout_Custom.addStretch()

            tileSizeLayout = QtWidgets.QVBoxLayout()
            tileSizeLayout.addWidget(self.tileSize_Label)
            tileSizeLayout.addWidget(self.tileSize_RadioAuto)
            tileSizeLayout.addLayout(tileSizeLayout_Preset)
            tileSizeLayout.addLayout(tileSizeLayout_Custom)

            layout = QtWidgets.QVBoxLayout(self)
            layout.addLayout(tileSizeLayout)
            layout.addStretch()



class Theme:
    """
    Contains information about a single Reggie Next theme
    """
    def __init__(self, mainWindow, name):
        """
        Initialize the theme
        """
        self.mainWindow = mainWindow
        self.name = name

        self.loadBase()

        try:
            self.load()
        except Exception as e:
            raise
            print('Theme \"' + name + '\" is malformed: ' + str(e))
            self.clear()


    def loadBase(self):
        """
        Load the base theme. The actual theme data will be put
        on top of this.
        """
        self.colors = {}
        self.qss = ''

        with open(os.path.join('themes', 'light', 'theme.xml'), 'r', encoding='utf-8') as f:
            themeXML = f.read()
        root = etree.fromstring(themeXML)

        for node in root:
            if node.tag.lower() == 'color':
                self.colors[node.attrib['name']] = node.attrib['value']


    def load(self):
        """
        Load the theme.
        If the theme is malformed, the exception will propogate.
        """
        with open(os.path.join('themes', self.name, 'theme.xml'), 'r', encoding='utf-8') as f:
            themeXML = f.read()
        root = etree.fromstring(themeXML)

        # Parse the root node
        self.displayName = root.attrib['name']
        self.creator = root.attrib['creator']
        self.description = root.attrib['description']

        # Parse everything else
        for node in root:
            if node.tag.lower() == 'qss':
                with open(os.path.join('themes', self.name, node.attrib['file']), 'r', encoding='utf-8') as f:
                    self.qss = f.read()
            elif node.tag.lower() == 'color':
                self.colors[node.attrib['name']] = node.attrib['value']


    def color(self, name):
        """
        Returns the color called name.
        """
        return self.colors.get(name, Qt.black)



class ReggieNextWindow(QtWidgets.QMainWindow):
    """
    The main window for Reggie Next
    """

    initializing = False
    actions = {}
    actionListIndices = {}

    def __init__(self):
        """
        Editor window constructor
        """

        self.initializing = True

        # Required variables
        self.UpdateFlag = False
        self.SelectionUpdateFlag = False
        self.selObj = None
        self.CurrentSelection = []

        # Set up the window
        super().__init__(None)
        self.setWindowTitle(_('Untitled'))
        self.setIconSize(QtCore.QSize(16, 16))
        self.setUnifiedTitleAndToolBarOnMac(True)

        # Load the settings
        self.loadSettings()

        # Set up the theme
        self.loadTheme()

        # Create the tab stack widget
        self.tabStack = TabStackWidget(self)
        self.setCentralWidget(self.tabStack)

        self.addInitialTabs()

        # Set up the clipboard stuff
        self.clipboard = None
        self.systemClipboard = QtWidgets.QApplication.clipboard()
        # self.systemClipboard.dataChanged.connect(self.TrackClipboardUpdates)

        # We might have something there already, activate Paste if so
        # self.TrackClipboardUpdates()

        # Set up actions, menubar, toolbar and statusbar
        self.setupActions()
        self.setupMenubar()
        self.setupToolbar()
        self.setupStatusbar()

        self.tabStack.updateStatusbarText.connect(self.handleUpdateStatusbarText)
        self.tabStack.tabSwitched.connect(self.handleTabSwitched)

        # Create the various panels
        # self.SetupDocksAndPanels()

        # Now get stuff ready

        # QtCore.QTimer.singleShot(100, self.levelOverview.update)

        # Let's restore the state and geometry.
        # Geometry: determines the main window position
        # State: determines positions of docks
        if self.settings.contains('MainWindowGeometry'):
            self.restoreGeometry(self.setting('MainWindowGeometry'))
        if self.settings.contains('MainWindowState'):
            self.restoreState(self.setting('MainWindowState'), 0)

        # Done with initialization!
        self.initializing = False


    def loadSettings(self):
        """
        Loads ReggieNext's QSettings instance
        """
        self.settings = QtCore.QSettings('Reggie Next', REGGIE_VERSION)


    def setting(self, name, default=None):
        """
        Wrapper around self.settings.value; fixes a bool-to-string bug
        """
        result = self.settings.value(name, default)
        resultMap = {'false': False, 'true': True, 'none': None}

        if result in resultMap:
            return resultMap[result]
        return result


    def setSetting(self, name, value):
        """
        Sets a new setting value
        """
        return self.settings.setValue(name, value)


    def loadTheme(self):
        """
        Loads the theme
        """
        global app

        # Load the theme
        self.setSetting('theme', 'dark')
        self.theme = Theme(self, self.setting('theme'))

        # Apply the theme
        app.setStyle('Fusion')

        with open('style.qss', 'r', encoding='utf-8') as f:
            stylesheetMain = f.read()
        stylesheetTheme = self.theme.qss

        app.setStyleSheet(stylesheetMain + stylesheetTheme)


    def addInitialTabs(self):
        """
        Adds the initial tabs to the tab stack widget
        """
        self.tabStack.addTab(TabView_2DLevel(self, gameModules['newsupermariobroswii'].levelTypes[0]))
        self.tabStack.addTab(TabView_2DLevel(self, gameModules['newsupermariobroswii'].levelTypes[0]))
        self.tabStack.addTab(TabView_TextEditor(self))
        self.tabStack.addTab(TabView_3DLevel(self))


    def createAction(self, shortname, function, icon, text, statustext, shortcut, listIndex, toggle=False):
        """
        Helper function to create an action
        """

        if icon is not None:
            act = QtWidgets.QAction(icon, text, self)
        else:
            act = QtWidgets.QAction(text, self)

        if shortcut is not None:
            act.setShortcut(shortcut)
        if statustext is not None:
            act.setStatusTip(statustext)
        if toggle:
            act.setCheckable(True)
        if function is not None:
            act.triggered.connect(function)

        self.actions[shortname] = act

        self.actionListIndices[shortname] = listIndex


    def setupActions(self):
        """
        Create all actions
        """
        # File
        self.createAction(
            'newlevel', self.handleNewLevel, getIcon('new'),
            _('New Level'),
            _('Create a new, blank level'),
            QtGui.QKeySequence.New, 0)
        self.createAction(
            'openfromlevelname', self.handleOpenByLevelName, getIcon('open'),
            _('Open Level by Name...'),
            _('Open a level based on its in-game world/number'),
            QtGui.QKeySequence.Open, 1)
        self.createAction(
            'openfromfilename', self.handleOpenByFileName, getIcon('openfromfile'),
            _('Open Level by Filename...'),
            _('Open a level based on its filename'),
            QtGui.QKeySequence('Ctrl+Shift+O'), 2)
        self.createAction(
            'save', self.handleSave, getIcon('save'),
            _('Save Level'),
            _('Save the level back to the archive file'),
            QtGui.QKeySequence.Save, 3)
        self.createAction(
            'saveas', self.handleSaveAs, getIcon('saveas'),
            _('Save Level As...'),
            _('Save a level with a new filename'),
            QtGui.QKeySequence('Ctrl+Shift+S'), 4)
        self.createAction(
            'savecopyas', self.handleSaveCopyAs, getIcon('savecopyas'),
            _('Save Copy of Level As...'),
            _('Save a copy of level with a new filename but keeps the current file open for editing'),
            QtGui.QKeySequence('Ctrl+Alt+Shift+S'), 5)
        self.createAction(
            'screenshot', self.handleScreenshot, getIcon('screenshot'),
            _('Level Screenshot...'),
            _('Take a full size screenshot of your level for you to share'),
            QtGui.QKeySequence('Ctrl+Alt+S'), 6)
        self.createAction(
            'settings', self.handleSettings, getIcon('settings'),
            _('Reggie Next Settings...'),
            _('Change important Reggie Next settings'),
            QtGui.QKeySequence('Ctrl+Alt+P'), 7)
        self.createAction(
            'exit', self.handleExit, getIcon('delete'),
            _('Exit Reggie Next'),
            _('Exit Reggie Next'),
            QtGui.QKeySequence('Ctrl+Q'), 8)

        # Edit
        self.createAction(
            'selectall', self.handleSelectAll, getIcon('selectall'),
            _('Select All'),
            _('Select all items in this area'),
            QtGui.QKeySequence.SelectAll, 9)
        self.createAction(
            'deselect', self.handleDeselect, getIcon('deselect'),
            _('Deselect'),
            _('Deselect all currently selected items'),
            QtGui.QKeySequence('Ctrl+D'), 10)
        self.createAction(
            'undo', self.handleUndo, getIcon('undo'),
            _('Undo'),
            _('Undoes the last action'),
            QtGui.QKeySequence.Undo, 11)
        self.createAction(
            'redo', self.handleRedo, getIcon('redo'),
            _('Redo'),
            _('Redoes the last action that was undone'),
            QtGui.QKeySequence.Redo, 12)
        self.createAction(
            'cut', self.handleCut, getIcon('cut'),
            _('Cut'),
            _('Cut out the current selection to the clipboard'),
            QtGui.QKeySequence.Cut, 13)
        self.createAction(
            'copy', self.handleCopy, getIcon('copy'),
            _('Copy'),
            _('Copy the current selection to the clipboard'),
            QtGui.QKeySequence.Copy, 14)
        self.createAction(
            'paste', self.handlePaste, getIcon('paste'),
            _('Paste'),
            _('Paste items from the clipboard'),
            QtGui.QKeySequence.Paste, 15)

        # View
        self.createAction(
            'animations', self.handleAnimationsToggle, getIcon('animation'),
            _('Animations'),
            _('Play animations for certain items (may cause lagging)'),
            QtGui.QKeySequence('Ctrl+7'), 16, True)
        self.createAction(
            'collisions', self.handleCollisionsToggle, getIcon('collisions'),
            _('Collisions'),
            _('View collisions for certain items'),
            QtGui.QKeySequence('Ctrl+8'), 17, True)
        self.createAction(
            '3dhighlight', self.handle3DHighlightToggle, getIcon('3dhighlight'),
            _('3D Highlighting'),
            _('Highlight 3D depth effects for certain items'),
            QtGui.QKeySequence('Ctrl+H'), 18, True)
        self.createAction(
            'realview', self.handleRealViewToggle, getIcon('realview'),
            _('Real View'),
            _('Realistically render any special effects present in the level'),
            QtGui.QKeySequence('Ctrl+9'), 19, True)
        self.createAction(
            'fullscreen', self.handleFullscreen, getIcon('fullscreen'),
            _('Show Fullscreen'),
            _('Display the main window with all available screen space'),
            QtGui.QKeySequence('Ctrl+U'), 20, True)
        self.createAction(
            'switchgrid', self.handleSwitchGrid, getIcon('grid'),
            _('Switch Grid'),
            _('Cycle through available grid styles'),
            QtGui.QKeySequence('Ctrl+G'), 21)
        self.createAction(
            'zoommax', self.handleZoomMax, getIcon('zoommax'),
            _('Zoom to Maximum'),
            _('Zoom in as far as possible'),
            QtGui.QKeySequence('Ctrl+PgDown'), 22)
        self.createAction(
            'zoomin', self.handleZoomIn, getIcon('zoomin'),
            _('Zoom In'),
            _('Zoom in a small amount'),
            QtGui.QKeySequence.ZoomIn, 23)
        self.createAction(
            'zoom100', self.handleZoom100, getIcon('zoomactual'),
            _('Zoom to 100%'),
            _('Display the level at the default zoom level'),
            QtGui.QKeySequence('Ctrl+0'), 24)
        self.createAction(
            'zoomout', self.handleZoomOut, getIcon('zoomout'),
            _('Zoom Out'),
            _('Zoom out a small amount'),
            QtGui.QKeySequence.ZoomOut, 25)
        self.createAction(
            'zoommin', self.handleZoomMin, getIcon('zoommin'),
            _('Zoom to Minimum'),
            _('Zoom out as far as possible'),
            QtGui.QKeySequence('Ctrl+PgUp'), 26)
        # Show Overview and Show Palette are added later

        # Settings
        self.createAction(
            'reloadgraphics', self.handleReloadGraphics, getIcon('reload'),
            _('Reload Graphics'),
            _('Reload level graphics, including any changes made since the level was loaded, and clear the graphics cache'),
            QtGui.QKeySequence('Ctrl+Shift+R'), 27)

        # Help
        self.createAction(
            'aboutrn', self.handleAboutReggieNext, getIcon('reggienext'),
            _('About Reggie Next...'),
            _('Information about Reggie Next and the team behind it'),
            QtGui.QKeySequence('Ctrl+Shift+I'), 28)
        self.createAction(
            'aboutpython', self.handleAboutPython, getIcon('python'),
            _('About Python...'),
            _('Information about the Python langage Reggie Next is written in'),
            QtGui.QKeySequence('Ctrl+Shift+P'), 29)
        self.createAction(
            'aboutqt', QtWidgets.qApp.aboutQt, getIcon('qt'),
            _('About Qt...'),
            _('Information about the Qt library Reggie Next uses'),
            QtGui.QKeySequence('Ctrl+Shift+Q'), 30)
        self.createAction(
            'help', self.handleHelp, getIcon('contents'),
            _('Help Contents...'),
            _('Help documentation for beginners and power users'),
            QtGui.QKeySequence('Ctrl+Shift+H'), 31)
        self.createAction(
            'update', self.handleUpdate, getIcon('download'),
            _('Check for Updates...'),
            _('Check if any updates for Reggie Next are available to download'),
            QtGui.QKeySequence('Ctrl+Shift+U'), 33)

        # Configure them
        self.actions['undo'].setEnabled(False)
        self.actions['redo'].setEnabled(False)
        self.actions['cut'].setEnabled(False)
        self.actions['copy'].setEnabled(False)
        self.actions['paste'].setEnabled(False)
        self.actions['deselect'].setEnabled(False)


    def setupMenubar(self):
        """
        Create and set up the menubar
        """
        menubar = self.menuBar()

        # File
        fmenu = menubar.addMenu(_('&File'))
        fmenu.addSection(_('Manage'))
        fmenu.addAction(self.actions['newlevel'])
        fmenu.addAction(self.actions['openfromlevelname'])
        fmenu.addAction(self.actions['openfromfilename'])
        fmenu.addAction(self.actions['save'])
        fmenu.addAction(self.actions['saveas'])
        fmenu.addAction(self.actions['savecopyas'])
        fmenu.addSection(_('Actions'))
        fmenu.addAction(self.actions['screenshot'])
        fmenu.addAction(self.actions['settings'])
        fmenu.addSection(_('Editor'))
        fmenu.addAction(self.actions['exit'])

        # Edit
        emenu = menubar.addMenu(_('&Edit'))
        emenu.addSection(_('Selection'))
        emenu.addAction(self.actions['selectall'])
        emenu.addAction(self.actions['deselect'])
        emenu.addSection(_('Undo'))
        emenu.addAction(self.actions['undo'])
        emenu.addAction(self.actions['redo'])
        emenu.addSection(_('Clipboard'))
        emenu.addAction(self.actions['cut'])
        emenu.addAction(self.actions['copy'])
        emenu.addAction(self.actions['paste'])

        # View
        vmenu = menubar.addMenu(_('&View'))
        vmenu.addSection(_('Graphics'))
        vmenu.addAction(self.actions['animations'])
        vmenu.addAction(self.actions['collisions'])
        vmenu.addAction(self.actions['3dhighlight'])
        vmenu.addAction(self.actions['realview'])
        vmenu.addSection(_('Global'))
        vmenu.addAction(self.actions['fullscreen'])
        vmenu.addAction(self.actions['switchgrid'])
        vmenu.addSection(_('Zoom'))
        vmenu.addAction(self.actions['zoommax'])
        vmenu.addAction(self.actions['zoomin'])
        vmenu.addAction(self.actions['zoom100'])
        vmenu.addAction(self.actions['zoomout'])
        vmenu.addAction(self.actions['zoommin'])
        vmenu.addSection(_('Windows'))

        # self.levelOverviewDock.toggleViewAction() is added here later,
        # so we assign it to self.vmenu
        self.vmenu = vmenu

        # Settings
        smenu = menubar.addMenu(_('&Settings'))
        smenu.addSection(_('Reload'))
        smenu.addAction(self.actions['reloadgraphics'])
        smenu.addSection(_('Options'))

        # Help
        hmenu = menubar.addMenu(_('&Help'))
        hmenu.addSection(_('About'))
        hmenu.addAction(self.actions['aboutrn'])
        hmenu.addAction(self.actions['aboutpython'])
        hmenu.addAction(self.actions['aboutqt'])
        hmenu.addSection(_('Links'))
        hmenu.addAction(self.actions['help'])
        hmenu.addSection(_('Actions'))
        hmenu.addAction(self.actions['update'])


    def setupToolbar(self):
        """
        Create and set up the toolbar
        """
        toolbar = self.addToolBar(_('Shortcut Toolbar'))
        toolbar.setObjectName('ShortcutToolbar')

        return

        # Add buttons to the toolbar
        self.addToolbarButtons()

        # Add the area combo box
        self.areaComboBox = QtWidgets.QComboBox()
        self.areaComboBox.activated.connect(self.HandleSwitchArea)
        self.toolbar.addWidget(self.areaComboBox)


    def setupStatusbar(self):
        """
        Create and set up the status bar
        """
        statusbar = self.statusBar()

        # "addWidget": add to the left edge
        self.statusLabel = QtWidgets.QLabel()
        statusbar.addWidget(self.statusLabel)

        # "addPermanentWidget": add to the right edge
        self.zoomWidget = ZoomWidget(self)
        self.tabStack.setZoomWidget(self.zoomWidget)
        statusbar.addPermanentWidget(self.zoomWidget)


    def handleNewLevel(self):
        """
        Create a new level
        """
        dlg = NewLevelDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        gameObj, levelObj, templateObj = dlg.getSelectedInfo()

        self.tabStack.addTab(TabView_2DLevel(self, levelObj(templateObj)))


    def handleOpenByLevelName(self):
        """
        Open a level using the level picker
        """
        ...


    def handleOpenByFileName(self):
        """
        Open a level from a filename
        """
        # Populate a list of file extensions
        fileExts = []
        for gameObj in gameModules.values():
            for levelObj in gameObj.levelTypes:
                fileExts.append(_('[name] (*.[ext])', '[name]', levelObj.TYPE_NAME, '[ext]', levelObj.FILE_EXTENSION))
        fileExts.append(_('All files (*)'))
        fileExts = ';;'.join(fileExts)

        fn = QtWidgets.QFileDialog.getOpenFileName(self, _('Open File'), '', fileExts)[0]
        if fn == '': return

        with open(fn, 'rb') as f:
            data = f.read()

        # Choose the correct game to open the file with by inspecting
        # the data (don't blindly rely on file extensions)
        levelClass = None
        for possibleGame in gameModules.values():
            for possibleLevelClass in possibleGame.levelTypes:
                if possibleLevelClass.validate(data):
                    levelClass = possibleLevelClass
                    break
            if levelClass is not None: break
        else:
            QtWidgets.QMessageBox.warning(self, _('Reggie Next'), _('The file could not be recognized.'))
            return

        # So now we have the correct level class that matches the data.
        # Let's parse it.
        levelObj = levelClass.loadFromBytes(data)


    def handleSave(self):
        """
        Save the current level
        """
        ...


    def handleSaveAs(self):
        """
        Save the current level to a different file
        """
        ...


    def handleSaveCopyAs(self):
        """
        Save the current level to a different file, but do not keep track of this filename
        """
        ...


    def handleScreenshot(self):
        """
        Take a screenshot of part of the level, or the whole level, and save it
        """
        dlg = ScreenshotDialog(self)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return

        fn = QtWidgets.QFileDialog.getSaveFileName(self, _('Choose a new filename'), '/untitled.png', _('Portable Network Graphics') + ' (*.png)')[0]
        if not fn:
            return

        view = self.tabStack.getCurrentView()

        if dlg.zoneCombo.currentIndex() == 0:
            screenshotImage = QtGui.QImage(view.width(), view.height(), QtGui.QImage.Format_ARGB32)
            screenshotImage.fill(Qt.transparent)

            renderPainter = QtGui.QPainter(screenshotImage)
            view.render(renderPainter, QtCore.QRectF(0, 0, view.width(), view.height()), QtCore.QRect(QtCore.QPoint(0, 0), QtCore.QSize(view.width(), view.height())))
            renderPainter.end()
        else:
            raise NotImplementedError  # todo: figure out what to do with this

        screenshotImage.save(fn, 'PNG', 50)


    def handleSettings(self):
        """
        Edit Reggie Next settings
        """
        self.tabStack.addTab(TabView_ReggieNextSettings(self), True)


    def handleExit(self):
        """
        Exit Reggie Next. Why would you want to do this, anyway?
        """
        self.close()


    def handleSelectAll(self):
        """
        Select all objects in the current area
        """
        paintRect = QtGui.QPainterPath()
        paintRect.addRect(self.scene.sceneRect())
        self.scene.setSelectionArea(paintRect)


    def handleDeselect(self):
        """
        Deselect all currently selected items
        """
        items = self.scene.selectedItems()
        for obj in items:
            obj.setSelected(False)


    def handleUndo(self):
        """
        Undo the last action
        """
        ...


    def handleRedo(self):
        """
        Redo something previously undone
        """
        ...


    def handleCut(self):
        """
        Cut the selected items
        """
        ...


    def handleCopy(self):
        """
        Copy the selected items
        """
        ...


    def handlePaste(self):
        """
        Paste items from the system clipboard
        """
        ...


    def handleAnimationsToggle(self, checked):
        """
        Handle toggling of item animations
        """
        ...


    def handleCollisionsToggle(self, checked):
        """
        Handle toggling of item collisions
        """
        ...


    def handle3DHighlightToggle(self, checked):
        """
        Handle toggling of 3D depth highlighting
        """
        ...


    def handleRealViewToggle(self, checked):
        """
        Handle toggling of Real View
        """
        ...


    def handleFullscreen(self, checked):
        """
        Handle toggling of fullscreen mode
        """
        if checked:
            self.showFullScreen()
        else:
            self.showMaximized()


    def handleSwitchGrid(self):
        """
        Handle switching of the grid view
        """
        for view in self.tabStack.allViewsIter():
            view.gridType += 1
            if view.gridType >= 4:
                view.gridType = 0

        self.setSetting('GridType', view.gridType)
        self.tabStack.getCurrentView().scene().update()


    def handleZoomMax(self):
        """
        Handle zooming to the maximum size
        """
        self.zoomWidget.handleZoomMax()


    def handleZoomIn(self):
        """
        Handle zooming in
        """
        self.zoomWidget.handleZoomIn()


    def handleZoom100(self):
        """
        Handle zooming to the actual size
        """
        self.zoomWidget.handleZoom100()


    def handleZoomOut(self):
        """
        Handle zooming out
        """
        self.zoomWidget.handleZoomOut()


    def handleZoomMin(self):
        """
        Handle zooming to the minimum size
        """
        self.zoomWidget.handleZoomMin()


    def handleReloadGraphics(self):
        """
        Handle reloading graphics
        """
        ...
        # Requested by Grop: reload spritedata before reload tileset data


    def handleAboutReggieNext(self):
        """
        Display information about Reggie Next
        """
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle(_('About Reggie Next'))
        dialog.setMinimumWidth(512)

        with open('readme.md', 'r', encoding='utf-8') as inf:
            aboutText = inf.read()

        textView = QtWidgets.QPlainTextEdit()
        textView.setReadOnly(True)
        textView.setPlainText(aboutText)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(dialog.accept)

        L = QtWidgets.QVBoxLayout(dialog)
        L.addWidget(textView)
        L.addWidget(buttonBox)

        dialog.exec_()


    def handleAboutPython(self):
        """
        Display information about Python
        """
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle(_('About Python'))
        dialog.setMinimumWidth(512)

        aboutText = 'Python ' + sys.version + '\n\n' + sys.copyright

        textView = QtWidgets.QPlainTextEdit()
        textView.setReadOnly(True)
        textView.setPlainText(aboutText)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        buttonBox.accepted.connect(dialog.accept)

        L = QtWidgets.QVBoxLayout(dialog)
        L.addWidget(textView)
        L.addWidget(buttonBox)

        dialog.exec_()


    # About Qt is handled by a built-in PyQt function.


    def handleHelp(self):
        """
        View the included help documentation
        """
        global appPath
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(os.path.join(appPath, 'help', 'index.html')))


    def handleUpdate(self):
        """
        Check for updates, and allow the user to download any
        """
        ...


    def handleUpdateStatusbarText(self, positionText, selectionText, hoverText):
        """
        self.tabStack requested an update to the statusbar text.
        """
        labels = (positionText, selectionText, hoverText)

        # Remove empty labels
        labels = [label for label in labels if label]

        self.statusLabel.setText(_('; ').join(labels))



    def handleTabSwitched(self):
        """
        Called whenever the user switches level tabs
        """
        ...


    def closeEvent(self, event):
        """
        Handler for the main window close event
        """
        # State: determines positions of docks
        # Geometry: determines the main window position
        self.setSetting('MainWindowState', self.saveState(0))
        self.setSetting('MainWindowGeometry', self.saveGeometry())

        super().closeEvent(event)



def main():
    """
    Main startup function for Reggie Next
    """
    global app, mainWindow, appPath

    # Create an application
    app = QtWidgets.QApplication(sys.argv)

    # Go to the script path
    appPath = getModulePath()
    if appPath is not None:
        os.chdir(appPath)

    # Check if required files are missing
    if FilesAreMissing():
        sys.exit(1)

    # Set the application display name and window icon
    app.setApplicationDisplayName('Reggie Next')
    app.setWindowIcon(getIcon('reggienext'))

    # Load all game modules
    loadGameModules()

    # Create and show the main window
    mainWindow = ReggieNextWindow()
    mainWindow.show()

    # Run Reggie Next!
    exitcodesys = app.exec_()
    app.deleteLater()
    sys.exit(exitcodesys)


if __name__ == '__main__':
    main()
