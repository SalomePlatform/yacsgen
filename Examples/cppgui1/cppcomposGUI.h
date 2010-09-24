#ifndef _cppcomposGUI_H_
#define _cppcomposGUI_H_

#include <SalomeApp_Module.h>
#include "ui_demo.h"

class cppcomposGUI: public SalomeApp_Module
{
  Q_OBJECT

public:
  cppcomposGUI();
  void    initialize( CAM_Application* );
  QString engineIOR() const;

public slots:
  bool    deactivateModule( SUIT_Study* );
  bool    activateModule( SUIT_Study* );

protected slots:
  void            OnGetBanner();
  void            OnDesigner();

};

class MyDemo: public QDialog
{
  Q_OBJECT

public:
  MyDemo(QWidget *parent = 0);

private:
  Ui::DemoDialog ui;

};

#endif
