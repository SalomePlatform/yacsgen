try:
  from string import Template
except:
  from compat import Template,set

pyCompo="""
import sys,traceback,os
sys.path=sys.path+[${python_path}]
import ${module}__POA
import calcium
import dsccalcium
import SALOME
import Engines
import cPickle

try:
  import numpy
except:
  numpy=None

#DEFS
${servicesdef}
#ENDDEF

class ${component}(${module}__POA.${component},dsccalcium.PyDSCComponent):
  '''
     To be identified as a SALOME component this Python class
     must have the same name as the component, inherit omniorb
     class ${module}__POA.${component} and DSC class dsccalcium.PyDSCComponent
     that implements DSC API.
  '''
  def __init__ ( self, orb, poa, contID, containerName, instanceName, interfaceName ):
    dsccalcium.PyDSCComponent.__init__(self, orb, poa,contID,containerName,instanceName,interfaceName)

  def init_service(self,service):
${initservice}
    return False

${servicesimpl}
"""

pyCompoEXE="""#!/usr/bin/env python
"""+pyCompo+"""
  def destroy(self):
     dsccalcium.PyDSCComponent.destroy(self)
     self._orb.shutdown(0)

if __name__ == '__main__':
  from omniORB import CORBA
  print sys.argv
  orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
  poa = orb.resolve_initial_references("RootPOA")
  print "ORB and POA initialized",orb,poa
  sys.stdout.flush()
  sys.stderr.flush()

  container=orb.string_to_object(sys.argv[1])
  containerName=sys.argv[2]
  instanceName=sys.argv[3]

  compo=${component}(orb,poa,container,containerName, instanceName, "${component}")
  comp_o = compo._this()
  comp_iors = orb.object_to_string(comp_o)
  print "ior ${component}",comp_iors

  sys.stdout.flush()
  sys.stderr.flush()

  #activate the POA
  poaManager = poa._get_the_POAManager()
  poaManager.activate()

  orb.run()
  print "fin du composant ${component} standalone"

"""

pyCompo=Template(pyCompo)
pyCompoEXE=Template(pyCompoEXE)

pyService="""
  def ${service}(self,${inparams}):
    self.beginService("${component}.${service}")
    component=self.proxy
    returns=None
    try:
${convertinparams}
#BODY
${body}
#ENDBODY
      sys.stdout.flush()
      self.endService("${component}.${service}")
${convertoutparams}
      return ${outparams}
    except:
      sys.stdout.flush()
      exc_typ,exc_val,exc_fr=sys.exc_info()
      l=traceback.format_exception(exc_typ,exc_val,exc_fr)
      raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,"".join(l),"${component}.py",0)) """
pyService=Template(pyService)

pyinitService="""    if service == "${service}":
       #initialization CALCIUM ports IN
${instream}
       #initialization CALCIUM ports OUT
${outstream}
       return True """
pyinitService=Template(pyinitService)
pyinitCEXEService=pyinitService
pyinitEXEService=pyinitService

