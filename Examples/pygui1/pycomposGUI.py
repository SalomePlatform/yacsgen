import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4 import QtCore, QtGui, uic

# Get SALOME PyQt interface
import SalomePyQt
sgPyQt = SalomePyQt.SalomePyQt()

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
  return True

# called when module is deactivated
def deactivate():
  pass

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



