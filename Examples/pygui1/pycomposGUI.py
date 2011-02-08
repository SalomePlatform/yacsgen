import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4 import QtCore, QtGui, uic

import salome
import pycompos_ORB

# Get SALOME PyQt interface
import SalomePyQt
sgPyQt = SalomePyQt.SalomePyQt()

# Get SALOME Swig interface
import libSALOME_Swig
sg = libSALOME_Swig.SALOMEGUI_Swig()

# object counter
__objectid__ = 0

###
# get active study ID
###
def _getStudyId():
    return sgPyQt.getStudyId()

###
# get active study
###
def _getStudy():
    studyId = _getStudyId()
    study = salome.myStudyManager.GetStudyByID( studyId )
    return study

# called when module is initialized
# return map of popup windows to be used by the module
def windows():
  wm = {}
  wm[SalomePyQt.WT_ObjectBrowser] = Qt.LeftDockWidgetArea
  wm[SalomePyQt.WT_PyConsole]     = Qt.BottomDockWidgetArea
  return wm

# called when module is initialized
# return list of 2d/3d views to be used ny the module
def views():
  return []

# called when module is activated
# returns True if activating is successfull and False otherwise
def activate():
  # create top-level menu
  mid = sgPyQt.createMenu( "pycompos", -1, 90, sgPyQt.defaultMenuGroup() )
  # create toolbar
  tid = sgPyQt.createTool( "pycompos" )
  # create actions and fill menu and toolbar with actions
  a = sgPyQt.createAction( 941, "Hello", "Hello", "Show hello dialog box" ,"exec.png")
  sgPyQt.createMenu( a, mid )
  sgPyQt.createTool( a, tid )
  a = sgPyQt.createAction( 942, "Hello2", "Hello2", "Show hello2 dialog box" ,"exec.png")
  sgPyQt.createMenu( a, mid )
  sgPyQt.createTool( a, tid )
  a = sgPyQt.createAction( 943, "Create object", "Create object", "Create object","exec.png" )
  sgPyQt.createMenu( a, mid )
  sgPyQt.createTool( a, tid )

  return True

# called when module is deactivated
def deactivate():
  pass

_engine=None
def getEngine():
  global _engine
  if not _engine:
    _engine= salome.lcc.FindOrLoadComponent( "FactoryServerPy", "pycompos" )
  return _engine

###
# Create new object
###
def CreateObject():
    global __objectid__
    default_name = str( sgPyQt.stringSetting( "pycompos", "def_obj_name", "Object" ).trimmed() )
    # generate object name
    __objectid__  = __objectid__ + 1
    name = "%s_%d" % ( default_name, __objectid__ )
    if not name: return
    getEngine().createObject( _getStudy(), name )
    print getEngine().s1(4,5)
    print getEngine().ComponentDataType()
    sg.updateObjBrowser( True )

class DemoImpl(QtGui.QDialog):
    def __init__(self, *args):
        super(DemoImpl, self).__init__(*args)

        uic.loadUi(os.path.join(os.environ["pycompos_ROOT_DIR"],"share","salome","resources","pycompos","demo.ui"), self)

    @QtCore.pyqtSlot()
    def on_button1_clicked(self):
        for s in "This is a demo".split(" "):
            self.list.addItem(s)

# called when GUI action is activated
# action ID is passed as parameter
def OnGUIEvent( commandID ):
  print "pycompos.OnGUIEvent(): command = %d" % commandID
  if commandID==941:
    widget=QMainWindow(sgPyQt.getDesktop())
    web = QWebView(widget)
    page=os.path.join(os.environ["pycompos_ROOT_DIR"],"share","doc","salome","gui","pycompos","index.html")
    web.load(QUrl(page))
    widget.setCentralWidget(web)
    widget.show()

  elif commandID==942:
    widget = DemoImpl(sgPyQt.getDesktop())
    widget.show()

  elif commandID==943:
    CreateObject()

