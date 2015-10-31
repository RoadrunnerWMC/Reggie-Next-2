# Module for NSMB2.

from PyQt5 import QtWidgets, QtGui, QtCore

import rn_api
import parentModule


def main():
    """
    Set up the module
    """
    rn_api.rSetGameName(rn_api._('New Super Mario Bros. 2'))
    rn_api.rSetGameIcon(rn_api.rIcon('nsmb2'))
