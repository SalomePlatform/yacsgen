
try:
 from string import Template
except:
 from compat import Template,set

astercompoMakefile="""include $$(top_srcdir)/adm_local/make_common_starter.am
salomepython_PYTHON = ${component}.py

"""
astercompoMakefile=Template(astercompoMakefile)
astercexeMakefile=astercompoMakefile

asterexeMakefile="""include $$(top_srcdir)/adm_local/make_common_starter.am
salomepython_PYTHON = ${component}_module.py
# These files are executable scripts
dist_salomescript_SCRIPTS= ${component}.exe
"""
asterexeMakefile=Template(asterexeMakefile)

asterCompo="""
import sys,traceback,os
import ${module}__POA
import calcium
import dsccalcium
import SALOME
import linecache
import shutil

sys.path=sys.path+[${python_path}]
import aster
import Accas
import Cata.cata
from Execution.E_SUPERV import SUPERV

aster_dir="${aster_dir}"

try:
  import numpy
except:
  numpy=None

#DEFS
${servicesdef}
#ENDDEF

class ${component}(${module}__POA.${component},dsccalcium.PyDSCComponent,SUPERV):
  '''
     To be identified as a SALOME component this Python class
     must have the same name as the component, inherit omniorb
     class ${module}__POA.${component} and DSC class dsccalcium.PyDSCComponent
     that implements DSC API.
  '''
  def __init__ ( self, orb, poa, contID, containerName, instanceName, interfaceName ):
    print "${component}.__init__: ", containerName, ';', instanceName,interfaceName
    dsccalcium.PyDSCComponent.__init__(self, orb, poa,contID,containerName,instanceName,interfaceName)
    self.argv=[${argv}]
    #modif pour aster 9.0
    if hasattr(self,"init_timer"):
      self.init_timer()
    #fin modif pour aster 9.0
    if os.path.exists(os.path.join(aster_dir,"elements")):
      shutil.copyfile(os.path.join(aster_dir,"elements"),"elem.1")
    else:
      shutil.copyfile(os.path.join(aster_dir,"catobj","elements"),"elem.1")

  def init_service(self,service):
${initservice}
    return False

${servicesimpl}
"""
asterCompo=Template(asterCompo)

asterCEXECompo="""
import sys,traceback,os
import string
import ${module}__POA
import calcium
import dsccalcium
import SALOME
import linecache
from E_SUPERV import SUPERV

try:
  import numpy
except:
  numpy=None

#DEFS
${servicesdef}
#ENDDEF

class ${component}(${module}__POA.${component},dsccalcium.PyDSCComponent,SUPERV):
  '''
     To be identified as a SALOME component this Python class
     must have the same name as the component, inherit omniorb
     class ${module}__POA.${component} and DSC class dsccalcium.PyDSCComponent
     that implements DSC API.
  '''
  def __init__ ( self, orb, poa, contID, containerName, instanceName, interfaceName ):
    print "${component}.__init__: ", containerName, ';', instanceName,interfaceName
    self.init=0
    dsccalcium.PyDSCComponent.__init__(self, orb, poa,contID,containerName,instanceName,interfaceName)

  def init_service(self,service):
${initservice}
    return False

${servicesimpl}
"""

asterEXECompo=asterCEXECompo+"""
  def destroy(self):
     dsccalcium.PyDSCComponent.destroy(self)
     self._orb.shutdown(0)
"""

asterCEXECompo=Template(asterCEXECompo)
asterEXECompo=Template(asterEXECompo)

asterService="""
  def ${service}(self,${inparams}):
    print "${component}.${service}"
    self.beginService("${component}.${service}")
    self.jdc=Cata.cata.JdC(procedure=jdc,cata=Cata.cata,nom="Salome",context_ini=${dvars})
    j=self.jdc
    #modif pour aster 9.0
    if hasattr(self,"init_timer"):
      j.timer = self.timer
    #fin modif pour aster 9.0

    # On compile le texte Python
    j.compile()

    #modif pour aster 9.0
    # On initialise les tops de mesure globale de temps d'execution du jdc
    if hasattr(self,"init_timer"):
       j.cpu_user=os.times()[0]
       j.cpu_syst=os.times()[1]
    #fin modif pour aster 9.0

    if not j.cr.estvide():
       msg="ERREUR DE COMPILATION DANS ACCAS - INTERRUPTION"
       self.MESSAGE(msg)
       print ">> JDC.py : DEBUT RAPPORT"
       print j.cr
       print ">> JDC.py : FIN RAPPORT"
       j.supprime()
       sys.stdout.flush()
       raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,msg+'\\n'+str(j.cr),"${component}.py",0))

    #surcharge des arguments de la ligne de commande (defaut stocke dans le composant) par un eventuel port de nom argv
    try:
      self.argv=self.argv+argv.split()
    except:
      pass

    #initialisation des arguments de la ligne de commande (remplace la methode initexec de B_JDC.py)
    aster.argv(self.argv)
    aster.init(CONTEXT.debug)
    j.setmode(1)
    j.ini=1

    try:
      j.exec_compile()
    except:
      sys.stdout.flush()
      exc_typ,exc_val,exc_fr=sys.exc_info()
      l=traceback.format_exception(exc_typ,exc_val,exc_fr)
      raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,"".join(l),"${component}.py",0))

    ier=0
    if not j.cr.estvide():
       msg="ERREUR A L'INTERPRETATION DANS ACCAS - INTERRUPTION"
       self.MESSAGE(msg)
       ier=1
       print ">> JDC.py : DEBUT RAPPORT"
       print j.cr
       print ">> JDC.py : FIN RAPPORT"
       sys.stdout.flush()
       raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,msg+'\\n'+str(j.cr), "${component}.py",0))
       
    if j.par_lot == 'NON':
       print "FIN EXECUTION"
       err=calcium.cp_fin(self.proxy,calcium.CP_ARRET)
       #retour sans erreur (il faut pousser les variables de sortie)
       print "End of ${component}.${service}"
       sys.stdout.flush()
       self.endService("${component}.${service}")
       return ${rvars}

    # Verification de la validite du jeu de commande
    cr=j.report()
    if not cr.estvide():
       msg="ERREUR A LA VERIFICATION SYNTAXIQUE - INTERRUPTION"
       self.MESSAGE(msg)
       print ">> JDC.py : DEBUT RAPPORT"
       print cr
       print ">> JDC.py : FIN RAPPORT"
       sys.stdout.flush()
       raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,msg+'\\n'+str(cr),"${component}.py",0))

    j.set_par_lot("NON")
    try:
       j.BuildExec()
       ier=0
       if not j.cr.estvide():
          msg="ERREUR A L'EXECUTION - INTERRUPTION"
          self.MESSAGE(msg)
          ier=1
          print ">> JDC.py : DEBUT RAPPORT"
          print j.cr
          print ">> JDC.py : FIN RAPPORT"
          sys.stdout.flush()
          raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,msg+'\\n'+str(j.cr),"${component}.py",0))
       else:
         #retour sans erreur (il faut pousser les variables de sortie)
         err=calcium.cp_fin(self.proxy,calcium.CP_ARRET)
         print "End of ${component}.${service}"
         sys.stdout.flush()
         self.endService("${component}.${service}")
         return ${rvars}
    except :
      self.MESSAGE("ERREUR INOPINEE - INTERRUPTION")
      sys.stdout.flush()
      exc_typ,exc_val,exc_fr=sys.exc_info()
      l=traceback.format_exception(exc_typ,exc_val,exc_fr)
      raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,"".join(l),"${component}.py",0))
"""
asterService=Template(asterService)

asterCEXEService="""
  def ${service}(self,${inparams}):
    print "${component}.${service}"
    self.beginService("${component}.${service}")
    if not self.init:
      self.init=1
      ier=self.main()
    j=self.jdc
    self.jdc.g_context.update(${dvars})
    try:
      CONTEXT.set_current_step(self.jdc)
      linecache.cache['<string>']=0,0,string.split(jdc,'\\n'),'<string>'
      exec jdc in self.jdc.g_context
      CONTEXT.unset_current_step()
      self.endService("${component}.${service}")
    except EOFError:
      self.endService("${component}.${service}")
    except:
      sys.stdout.flush()
      exc_typ,exc_val,exc_fr=sys.exc_info()
      l=traceback.format_exception(exc_typ,exc_val,exc_fr)
      self.endService("${component}.${service}")
      CONTEXT.unset_current_step()
      raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(SALOME.BAD_PARAM,"".join(l),"${component}.py",0))
    return ${rvars}
"""
asterCEXEService=Template(asterCEXEService)
asterEXEService=asterCEXEService


check_aster="""
#
# Check availability of Aster binary distribution
#

AC_DEFUN([AC_CHECK_ASTER],[

AC_CHECKING(for Aster)

Aster_ok=no

AC_ARG_WITH(aster,
      [AC_HELP_STRING([--with-aster=DIR],[root directory path of Aster installation])],
      [ASTER_DIR="$withval"],[ASTER_DIR=""])

if test -f ${ASTER_DIR}/asteru ; then
   Aster_ok=yes
   AC_MSG_RESULT(Using Aster distribution in ${ASTER_DIR})

   ASTER_INCLUDES=-I$ASTER_DIR/bibc/include

   AC_SUBST(ASTER_DIR)
   AC_SUBST(ASTER_INCLUDES)

else
   AC_MSG_WARN("Cannot find Aster distribution")
fi

AC_MSG_RESULT(for Aster: $Aster_ok)

])dnl
"""

comm="""
DEBUT(PAR_LOT='NON')
"""

make_etude="""P actions make_etude
P version NEW9
P nomjob salome
P ncpus 1
A memjeveux 4.000000
P mem_aster 100
A tpmax 60
P memjob 32768
P mpi_nbcpu 1
P mpi_nbnoeud 1
P tpsjob 1
P mode batch
P soumbtc oui
P consbtc oui
F conf ${config} D 0
F comm ${comm} D 1
${extras}
"""
make_etude=Template(make_etude)

make_etude_exe="""P actions make_etude
P version NEW9
P nomjob salome
P ncpus 1
A memjeveux 4.000000
P mem_aster 100
A tpmax 60
P memjob 32768
P mpi_nbcpu 1
P mpi_nbnoeud 1
P tpsjob 1
P mode batch
P soumbtc oui
P consbtc oui
F comm ${comm} D 1
"""
make_etude_exe=Template(make_etude_exe)

cexe="""#!/bin/sh

export SALOME_CONTAINERNAME=$$1

cp ${export} temp.export
cat >> temp.export << END
F mess $$PWD/messages R 6
F resu $$PWD/resu R 8
F erre $$PWD/erre R 9
END

${asrun} temp.export
"""
cexe=Template(cexe)

exeaster="""#!/bin/sh

export SALOME_CONTAINER=$$1
export SALOME_CONTAINERNAME=$$2
export SALOME_INSTANCE=$$3

cp ${export} temp.export
cat >> temp.export << END
F mess $$PWD/messages R 6
F resu $$PWD/resu R 8
F erre $$PWD/erre R 9
END

${asrun} temp.export
"""
exeaster=Template(exeaster)

container="""import sys,os
from omniORB import CORBA
from SALOME_ContainerPy import SALOME_ContainerPy_i

if __name__ == '__main__':

  print sys.argv
  orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
  poa = orb.resolve_initial_references("RootPOA")
  print "ORB and POA initialized"
  containerName=os.getenv("SALOME_CONTAINERNAME")
  cpy_i = SALOME_ContainerPy_i(orb, poa, containerName)
  print "SALOME_ContainerPy_i instance created ",cpy_i
  cpy_o = cpy_i._this()
  print "SALOME_ContainerPy_i instance activated ",cpy_o
  sys.stdout.flush()
  sys.stderr.flush()

  #activate the POA
  poaManager = poa._get_the_POAManager()
  poaManager.activate()

  #Block for ever
  orb.run()
  print "fin container aster"
  sys.stdout.flush()
  sys.stderr.flush()
"""

component="""import sys,os
from omniORB import CORBA
from ${component}_module import ${component}

if __name__ == '__main__':

  print sys.argv
  orb = CORBA.ORB_init(sys.argv, CORBA.ORB_ID)
  poa = orb.resolve_initial_references("RootPOA")
  print "ORB and POA initialized",orb,poa
  sys.stdout.flush()
  sys.stderr.flush()

  container=orb.string_to_object(os.getenv("SALOME_CONTAINER"))
  containerName=os.getenv("SALOME_CONTAINERNAME")
  instanceName=os.getenv("SALOME_INSTANCE")

  compo=${component}(orb,poa,container,containerName, instanceName, "${component}")
  comp_o = compo._this()
  comp_iors = orb.object_to_string(comp_o)
  print "ior aster",comp_iors

  sys.stdout.flush()
  sys.stderr.flush()

  #activate the POA
  poaManager = poa._get_the_POAManager()
  poaManager.activate()

  orb.run()
  print "fin du composant aster standalone"

"""
component=Template(component)
