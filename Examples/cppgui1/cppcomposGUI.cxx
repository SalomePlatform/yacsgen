#include "cppcomposGUI.h"
#include <SUIT_MessageBox.h>
#include <SUIT_ResourceMgr.h>
#include <SUIT_Desktop.h>
#include <SalomeApp_Application.h>

// QT Includes
#include <QInputDialog>
#include <QIcon>

// Export the module
extern "C" {
  CAM_Module* createModule()
  {
    return new cppcomposGUI();
  }
}

// Constructor
cppcomposGUI::cppcomposGUI() :
  SalomeApp_Module( "cppcompos" ), // default name
  LightApp_Module( "cppcompos" )
{
}

// Module's initialization
void cppcomposGUI::initialize( CAM_Application* app )
{

  SalomeApp_Module::initialize( app );

  QWidget* aParent = application()->desktop();
  SUIT_ResourceMgr* aResourceMgr = app->resourceMgr();

  // create actions
  QPixmap aPixmap = aResourceMgr->loadPixmap( "cppcompos","exec.png" );
  createAction( 901, "Banner", QIcon( aPixmap ), "Banner", "Banner", 0, aParent, false, this, SLOT( OnGetBanner() ) );
  createAction( 902, "Designer", QIcon( aPixmap ), "Designer", "Designer", 0, aParent, false, this, SLOT( OnDesigner() ) );

  // create menus
  int aMenuId;
  aMenuId = createMenu( "cppcompos", -1, -1, 30 );
  createMenu( 901, aMenuId, 10 );

  // create toolbars
  int aToolId = createTool ( "cppcompos" );
  createTool( 901, aToolId );
  createTool( 902, aToolId );
}

// Module's engine IOR
QString cppcomposGUI::engineIOR() const
{
  return "bidon";
}

// Module's activation
bool cppcomposGUI::activateModule( SUIT_Study* theStudy )
{
  bool bOk = SalomeApp_Module::activateModule( theStudy );

  setMenuShown( true );
  setToolShown( true );

  return bOk;
}

// Module's deactivation
bool cppcomposGUI::deactivateModule( SUIT_Study* theStudy )
{
  setMenuShown( false );
  setToolShown( false );

  return SalomeApp_Module::deactivateModule( theStudy );
}

// Action slot
void cppcomposGUI::OnGetBanner()
{
  // Dialog to get the Name
  bool ok = FALSE;
  QString myName = QInputDialog::getText( getApp()->desktop(), "label", "name", QLineEdit::Normal, QString::null, &ok );

  if ( ok && !myName.isEmpty()) 
  {
    QString banner = "Hello " + myName;
    SUIT_MessageBox::information( getApp()->desktop(), "info", banner, "OK" );
  }
}

// Action slot
void cppcomposGUI::OnDesigner()
{
  QWidget* wid= new MyDemo(getApp()->desktop());
  wid->show();
}

MyDemo::MyDemo(QWidget *parent)
        :QDialog(parent)
{
  ui.setupUi(this);
}
