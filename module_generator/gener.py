# Copyright (C) 2009-2013  EDF R&D
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
# See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

import os, shutil, glob, socket
import traceback
import warnings

try:
  from string import Template
except:
  from compat import Template, set

class Invalid(Exception):
  pass

debug=0

from mod_tmpl import resMakefile, makecommon, configure, paco_configure
from mod_tmpl import mainMakefile, autogen, application
from mod_tmpl import check_sphinx
from cata_tmpl import catalog, interface, idl, idlMakefile, parallel_interface
from cata_tmpl import xml, xml_interface, xml_service
from cata_tmpl import idlMakefilePaCO_BUILT_SOURCES, idlMakefilePaCO_nodist_salomeinclude_HEADERS
from cata_tmpl import idlMakefilePACO_salomepython_DATA, idlMakefilePACO_salomeidl_DATA
from cata_tmpl import idlMakefilePACO_INCLUDES
from cata_tmpl import cataOutStream, cataInStream, cataOutparam, cataInparam
from cata_tmpl import cataOutParallelStream, cataInParallelStream
from cata_tmpl import cataService, cataCompo
from aster_tmpl import check_aster
from salomemodules import salome_modules
from yacstypes import corbaTypes, corbaOutTypes, moduleTypes, idlTypes, corba_in_type, corba_out_type
from yacstypes import ValidTypes, PyValidTypes, calciumTypes, DatastreamParallelTypes
from yacstypes import ValidImpl, ValidImplTypes, ValidStreamTypes, ValidParallelStreamTypes, ValidDependencies
from gui_tmpl import pyguimakefile, pysalomeapp, cppguimakefile, cppsalomeapp
from doc_tmpl import docmakefile, docconf, docsalomeapp

def makedirs(namedir):
  """Create a new directory named namedir. If a directory already exists copy it to namedir.bak"""
  if os.path.exists(namedir):
    dirbak = namedir+".bak"
    if os.path.exists(dirbak):
      shutil.rmtree(dirbak)
    os.rename(namedir, dirbak)
    os.listdir(dirbak) #needed to update filesystem on special machines (cluster with NFS, for example)
  os.makedirs(namedir)

class Module(object):
  """
   A :class:`Module` instance represents a SALOME module that contains components given as a list of
   component instances (:class:`CPPComponent` or :class:`PYComponent` or :class:`F77Component` or :class:`ASTERComponent`)
   with the parameter *components*.

   :param name: gives the name of the module. The SALOME source module
      will be located in the <name_SRC> directory.
   :type name: str
   :param components: gives the list of components of the module.
   :param prefix: is the path of the installation directory.
   :param layout: If given and has the value "monodir", all components
      will be generated in a single directory. The default is to generate each component in its
      own directory.
   :param doc: can be used to add an online documentation to the module. It must be a list of file names (sources, images, ...) that will be
      used to build a sphinx documentation (see http://sphinx.pocoo.org, for more information). If not given, the Makefile.am
      and the conf.py (sphinx configuration) files are generated. In this case, the file name extension of source files must be .rst.
      See small examples in Examples/pygui1 and Examples/cppgui1.
   :param gui: can be used to add a GUI to the module. It must be a list of file names (sources, images, qt designer files, ...).
      If not given, the Makefile.am and SalomeApp.xml are generated. All image files are put in the resources directory of the module.
      The GUI can be implemented in C++ (file name extension '.cxx') or in Python (file name extension '.py').
      See small examples in Examples/pygui1 and Examples/cppgui1.

   For example, the following call defines a module named "mymodule" with 2 components c1 and c2  (they must have been
   defined before) that will be installed in the "install" directory::

      >>> m = module_generator.Module('mymodule', components=[c1,c2],
                                                  prefix="./install")

  """
  def __init__(self, name, components=None, prefix="",layout="multidir", doc=None, gui=None):
    self.name = name
    self.components = components or []
    self.prefix = prefix or "%s_INSTALL" % name
    self.layout=layout
    self.doc = doc
    self.gui = gui
    try:
      self.validate()
    except Invalid,e:
      if debug:
        traceback.print_exc()
      print "Error in module %s: %s" % (name,e)
      raise SystemExit

  def validate(self):
    # Test Module name, canot have a "-" in the name
    if self.name.find("-") != -1:
      raise Invalid("Module name %s is not valid, remove character - in the module name" % self.name)
    lcompo = set()
    for compo in self.components:
      if compo.name in lcompo:
        raise Invalid("%s is already defined as a component of the module" % compo.name)
      lcompo.add(compo.name)
      compo.validate()
    if self.gui and self.layout != "multidir":
      raise Invalid("A module with GUI can not be generated if layout is not multidir")

class Component(object):
  def __init__(self, name, services=None, impl="PY", libs="", rlibs="",
                     includes="", kind="lib", sources=None,
                     inheritedclass="",compodefs="",
                     idls=None,interfacedefs="",inheritedinterface="",addedmethods=""):
    self.name = name
    self.impl = impl
    self.kind = kind
    self.services = services or []
    self.libs = libs
    self.rlibs = rlibs
    self.includes = includes
    self.sources = sources or []
    self.inheritedclass=inheritedclass
    self.compodefs=compodefs
    self.idls=idls
    self.interfacedefs=interfacedefs
    self.inheritedinterface=inheritedinterface
    self.addedmethods=addedmethods

  def validate(self):
    if self.impl not in ValidImpl:
      raise Invalid("%s is not a valid implementation. It should be one of %s" % (self.impl, ValidImpl))

    lnames = set()
    for serv in self.services:
      serv.impl = self.impl
      if serv.name in lnames:
        raise Invalid("%s is already defined as a service of the module" % serv.name)
      lnames.add(serv.name)
      serv.validate()

    for src in self.sources:
      if not os.path.exists(src):
        raise Invalid("Source file %s does not exist" % src)

  def getImpl(self):
    return "SO", ""

  def getMakefileItems(self,gen):
    return {}

  def setPrerequisites(self, prerequisites_file):
    self.prerequisites = prerequisites_file

class Service(object):
  """
   A :class:`Service` instance represents a component service with dataflow and datastream ports.

   :param name: gives the name of the service.
   :type name: str
   :param inport: gives the list of input dataflow ports.
   :param outport: gives the list of output dataflow ports. An input or output dataflow port is defined
      by a 2-tuple (port name, data type name). The list of supported basic data types is: "double", "long", "string",
      "dblevec", "stringvec", "intvec", "file" and "pyobj" only for Python services. Depending on the implementation
      language, it is also possible to use some types from SALOME modules (see :ref:`yacstypes`).
   :param ret: gives the type of the return parameter
   :param instream: gives the list of input datastream ports.
   :param outstream: gives the list of output datastream ports. An input or output datastream port is defined
      by a 3-tuple (port name, data type name, mode name). The list of possible data types is: "CALCIUM_double", "CALCIUM_integer",
      "CALCIUM_real", "CALCIUM_string", "CALCIUM_complex", "CALCIUM_logical", "CALCIUM_long". The mode can be "I" (iterative mode)
      or "T" (temporal mode).
   :param defs: gives the source code to insert in the definition section of the component. It can be C++ includes
      or Python imports
   :type defs: str
   :param body: gives the source code to insert in the service call. It can be any C++
      or Python code that fits well in the body of the service method.
   :type body: str

   For example, the following call defines a minimal Python service with one input dataflow port (name "a", type double)
   and one input datastream port::

      >>> s1 = module_generator.Service('myservice', inport=[("a","double"),],
                                        instream=[("aa","CALCIUM_double","I")],
                                        body="print a")


  """
  def __init__(self, name, inport=None, outport=None, ret="void", instream=None, outstream=None,
                     parallel_instream=None, parallel_outstream=None, defs="", body="", impl_type="sequential"):
    self.name = name
    self.inport = inport or []
    self.outport = outport or []
    self.ret = ret
    self.instream = instream or []
    self.outstream = outstream or []
    self.parallel_instream = parallel_instream or []
    self.parallel_outstream = parallel_outstream or []
    self.defs = defs
    self.body = body
    self.impl = ""
    self.impl_type = impl_type

  def validate(self):
    lports = set()
    for port in self.inport:
      name, typ = self.validatePort(port)
      if name in lports:
        raise Invalid("%s is already defined as a service parameter" % name)
      lports.add(name)

    for port in self.outport:
      name, typ = self.validatePort(port)
      if name in lports:
        raise Invalid("%s is already defined as a service parameter" % name)
      lports.add(name)

    lports = set()
    for port in self.instream:
      name, typ, dep = self.validateStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    for port in self.outstream:
      name, typ, dep = self.validateStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    for port in self.parallel_instream:
      name, typ = self.validateParallelStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    for port in self.parallel_outstream:
      name, typ = self.validateParallelStream(port)
      if name in lports:
        raise Invalid("%s is already defined as a stream port" % name)
      lports.add(name)

    self.validateImplType()

  def validatePort(self, port):
    try:
      name, typ = port
    except:
      raise Invalid("%s is not a valid definition of an data port (name,type)" % (port,))

    if self.impl in ("PY", "ASTER"):
      validtypes = PyValidTypes
    else:
      validtypes = ValidTypes

    if typ not in validtypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ, validtypes))
    return name, typ

  def validateImplType(self):
    if self.impl_type not in ValidImplTypes:
      raise Invalid("%s is not a valid impl type. It should be one of %s" % (self.impl_type, ValidImplTypes))

  def validateStream(self, port):
    try:
      name, typ, dep = port
    except:
      raise Invalid("%s is not a valid definition of a stream port (name,type,dependency)" % (port,))
    if typ not in ValidStreamTypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ, ValidStreamTypes))
    if dep not in ValidDependencies:
      raise Invalid("%s is not a valid dependency. It should be one of %s" % (dep, ValidDependencies))
    return name, typ, dep

  def validateParallelStream(self, port):
    try:
      name, typ = port
    except:
      raise Invalid("%s is not a valid definition of a parallel stream port (name,type)" % (port,))
    if typ not in ValidParallelStreamTypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ, ValidParallelStreamTypes))
    return name, typ

class Generator(object):
  """
   A :class:`Generator` instance take a :class:`Module` instance as its first parameter and can be used to generate the
   SALOME source module, builds it, installs it and includes it in a SALOME application.

   :param module: gives the :class:`Module` instance that will be used for the generation.
   :param context: If given , its content is used to specify the prerequisites
      environment file (key *"prerequisites"*) and the SALOME KERNEL installation directory (key *"kernel"*).
   :type context: dict

   For example, the following call creates a generator for the module m::

      >>> g = module_generator.Generator(m,context)
  """
  def __init__(self, module, context=None):
    self.module = module
    self.context = context or {}
    self.kernel = self.context["kernel"]
    self.gui = self.context.get("gui")
    self.makeflags = self.context.get("makeflags")
    self.aster = ""
    if self.module.gui and not self.gui:
      raise Invalid("To generate a module with GUI, you need to set the 'gui' parameter in the context dictionnary")
    for component in self.module.components:
      component.setPrerequisites(self.context.get("prerequisites"))

  def generate(self):
    """Generate a SALOME source module"""
    module = self.module
    namedir = module.name+"_SRC"
    force = self.context.get("force")
    update = self.context.get("update")
    paco = self.context.get("paco")
    if os.path.exists(namedir):
      if force:
        shutil.rmtree(namedir)
      elif not update:
        raise Invalid("The directory %s already exists" % namedir)
    if update:
      makedirs(namedir)
    else:
      os.makedirs(namedir)

    srcs = {}
    makefile = "SUBDIRS="
    makefileItems={"header":"""
include $(top_srcdir)/adm_local/make_common_starter.am
AM_CFLAGS=$(SALOME_INCLUDES) -fexceptions
""",
                   "salomepython_PYTHON":[],
                   "dist_salomescript_SCRIPTS":[],
                   "salomeres_DATA":[],
                   "lib_LTLIBRARIES":[],
                   "salomeinclude_HEADERS":[],
                   "body":"",
                  }

    #get the list of SALOME modules used and put it in used_modules attribute
    def get_dependent_modules(mod,modules):
      modules[mod]=1
      if not salome_modules[mod].has_key("depends"):return
      for m in salome_modules[mod]["depends"]:
        if modules.has_key(m):continue
        get_dependent_modules(m,modules)

    modules = {}
    for compo in module.components:
      for serv in compo.services:
        for name, typ in serv.inport + serv.outport + [ ("return",serv.ret) ] :
          mod = moduleTypes[typ]
          if mod:
            get_dependent_modules(mod,modules)

    self.used_modules = modules.keys()

    for compo in module.components:
      #for components files
      fdict=compo.makeCompo(self)
      if self.module.layout=="multidir":
        srcs[compo.name] = fdict
        #for src/Makefile.am
        makefile = makefile + " " + compo.name
      else:
        srcs.update(fdict)
        #for src/Makefile.am
        mdict=compo.getMakefileItems(self)
        makefileItems["salomepython_PYTHON"]=makefileItems["salomepython_PYTHON"]+mdict.get("salomepython_PYTHON",[])
        makefileItems["dist_salomescript_SCRIPTS"]=makefileItems["dist_salomescript_SCRIPTS"]+mdict.get("dist_salomescript_SCRIPTS",[])
        makefileItems["salomeres_DATA"]=makefileItems["salomeres_DATA"]+mdict.get("salomeres_DATA",[])
        makefileItems["lib_LTLIBRARIES"]=makefileItems["lib_LTLIBRARIES"]+mdict.get("lib_LTLIBRARIES",[])
        makefileItems["salomeinclude_HEADERS"]=makefileItems["salomeinclude_HEADERS"]+mdict.get("salomeinclude_HEADERS",[])
        makefileItems["body"]=makefileItems["body"]+mdict.get("body","")+'\n'

    if module.gui:
      GUIname=module.name+"GUI"
      fdict=self.makeGui(namedir)
      srcs[GUIname] = fdict
      #for src/Makefile.am
      makefile = makefile + " " + GUIname

    if self.module.layout == "multidir":
      srcs["Makefile.am"] = makefile+'\n'
    else:
      srcs["Makefile.am"] = self.makeMakefile(makefileItems)

    docsubdir=""
    if module.doc:
      docsubdir="doc"

    #for catalog files
    catalogfile = "%sCatalog.xml" % module.name

    need_boost=0
    if module.gui:
        need_boost=1
    for compo in module.components:
      if hasattr(compo,"calciumextendedinterface") and compo.calciumextendedinterface:
        need_boost=1
        break

    #add makefile definitions to make_common_starter.am
    other_includes=""
    common_starter = makecommon.substitute(other_includes=other_includes)
    for mod in self.used_modules:
      common_starter = common_starter + salome_modules[mod]["makefiledefs"] + '\n'

    adm_local={"make_common_starter.am": common_starter, "check_aster.m4":check_aster}
    if module.doc:
      adm_local["check_sphinx.m4"]=check_sphinx

    self.makeFiles({"autogen.sh":autogen,
                    "Makefile.am":mainMakefile.substitute(docsubdir=docsubdir),
                    "README":"", "NEWS":"", "AUTHORS":"", "ChangeLog":"",
                    "src":srcs,
                    "resources":{"Makefile.am":resMakefile.substitute(module=module.name), catalogfile:self.makeCatalog()},
                    "adm_local":adm_local,
                    }, namedir)

    #add checks for modules in configure.ac
    configure_modules=""
    for mod in self.used_modules:
      configure_modules = configure_modules + salome_modules[mod]["configdefs"] + '\n'

    #for configure.ac
    configure_makefiles = []
    if self.module.layout=="multidir":
      for compo in module.components:
        configure_makefiles.append("     src/"+compo.name+"/Makefile")

    if module.gui:
      configure_makefiles.append("     src/%sGUI/Makefile" % module.name)
    if module.doc:
      configure_makefiles.append("     doc/Makefile")

    other_check=""
    other_summary=""
    other_require=""

    if need_boost:
      other_check=other_check+"""CHECK_BOOST
"""
      other_summary=other_summary+"""echo "  Boost  ................. : $boost_ok"
"""

    if module.gui:
      other_check=other_check + """CHECK_SALOME_GUI
CHECK_QT
"""
      other_summary=other_summary+'''echo "  SALOME GUI ............. : $SalomeGUI_ok"
echo "  Qt ..................... : $qt_ok"
'''
      other_require=other_require + """
      if test "x$SalomeGUI_ok" = "xno"; then
        AC_MSG_ERROR([SALOME GUI is required],1)
      fi
      if test "x$qt_ok" = "xno"; then
        AC_MSG_ERROR([Qt library is required],1)
      fi
"""
    if module.doc:
      other_check=other_check+"CHECK_SPHINX\n"
      other_summary=other_summary+'''echo "  Sphinx ................. : $sphinx_ok"\n'''
      other_require=other_require + """
      if test "x$sphinx_ok" = "xno"; then
        AC_MSG_ERROR([Sphinx documentation generator is required],1)
      fi
"""

    files={}
    #for idl files
    idlfile = "%s.idl" % module.name
    paco_config=""
    PACO_BUILT_SOURCES=""
    PACO_SALOMEINCLUDE_HEADERS=""
    PACO_INCLUDES=""
    PACO_salomepython_DATA=""
    PACO_salomeidl_DATA=""

    if paco:
      PACO_BUILT_SOURCES = idlMakefilePaCO_BUILT_SOURCES.substitute(module=module.name)
      PACO_SALOMEINCLUDE_HEADERS = idlMakefilePaCO_nodist_salomeinclude_HEADERS.substitute(module=module.name)
      PACO_salomepython_DATA = idlMakefilePACO_salomepython_DATA.substitute(module=module.name)
      PACO_salomeidl_DATA = idlMakefilePACO_salomeidl_DATA.substitute(module=module.name)
      PACO_INCLUDES = idlMakefilePACO_INCLUDES
      paco_config=paco_configure

    files["configure.ac"]=configure.substitute(module=module.name.lower(),
                                               makefiles='\n'.join(configure_makefiles),
                                               paco_configure=paco_config,
                                               modules=configure_modules,
                                               other_check=other_check,
                                               other_summary=other_summary,
                                               other_require=other_require,
                                              )

    #if components have other idls
    other_idls=""
    other_sks=""
    for compo in module.components:
      if compo.idls:
        for idl in compo.idls:
          for fidl in glob.glob(idl):
            other_idls=other_idls+os.path.basename(fidl) +" "
            other_sks=other_sks+os.path.splitext(os.path.basename(fidl))[0]+"SK.cc "

    idlfiles={"Makefile.am":    idlMakefile.substitute(module=module.name,
                                                       PACO_BUILT_SOURCES=PACO_BUILT_SOURCES,
                                                       PACO_SALOMEINCLUDE_HEADERS=PACO_SALOMEINCLUDE_HEADERS,
                                                       PACO_INCLUDES=PACO_INCLUDES,
                                                       PACO_salomepython_DATA=PACO_salomepython_DATA,
                                                       PACO_salomeidl_DATA=PACO_salomeidl_DATA,
                                                       other_idls=other_idls,other_sks=other_sks,
                                                       ),
              idlfile : self.makeidl(),
             }
    if paco:
      idlfiles["%s.xml" % module.name]=self.makexml()

    files["idl"]=idlfiles

    self.makeFiles(files,namedir)

    os.chmod(os.path.join(namedir, "autogen.sh"), 0777)
    #copy source files if any in created tree
    for compo in module.components:
      for src in compo.sources:
        if self.module.layout=="multidir":
          shutil.copyfile(src, os.path.join(namedir, "src", compo.name, os.path.basename(src)))
        else:
          shutil.copyfile(src, os.path.join(namedir, "src", os.path.basename(src)))

      if compo.idls:
        #copy provided idl files in idl directory
        for idl in compo.idls:
          for fidl in glob.glob(idl):
            shutil.copyfile(fidl, os.path.join(namedir, "idl", os.path.basename(fidl)))

    checks= ("check_Kernel.m4", "check_omniorb.m4", "ac_linker_options.m4", "ac_cxx_option.m4",
             "python.m4", "enable_pthreads.m4", "check_f77.m4", "acx_pthread.m4", "check_paco++.m4",
             "check_mpi.m4", "check_lam.m4", "check_openmpi.m4", "check_mpich.m4")
    if need_boost:
      checks=checks+("check_boost.m4",)
    for m4file in checks:
      shutil.copyfile(os.path.join(self.kernel, "salome_adm", "unix", "config_files", m4file),
                      os.path.join(namedir, "adm_local", m4file))

    if self.module.gui:
      for m4file in ("check_GUI.m4", "check_qt.m4", "check_opengl.m4"):
        shutil.copyfile(os.path.join(self.gui, "adm_local", "unix", "config_files", m4file),
                        os.path.join(namedir, "adm_local", m4file))

    self.makeDoc(namedir)
    return

  def makeDoc(self,namedir):
    if not self.module.doc:
      return
    rep=os.path.join(namedir,"doc")
    os.makedirs(rep)
    for docs in self.module.doc:
      for doc in glob.glob(docs):
        name = os.path.basename(doc)
        shutil.copyfile(doc, os.path.join(rep, name))

    d={}

    others=""
    if not self.module.gui:
       #without gui but with doc: create a small SalomeApp.xml in doc directory
       if not os.path.exists(os.path.join(namedir, "doc", "SalomeApp.xml")):
         #create a minimal SalomeApp.xml
         salomeapp=docsalomeapp.substitute(module=self.module.name,lmodule=self.module.name.lower())
         d["SalomeApp.xml"]=salomeapp
       others="SalomeApp.xml"

    if not os.path.exists(os.path.join(namedir, "doc", "Makefile.am")):
      #create a minimal makefile.am
      d["Makefile.am"]=docmakefile.substitute(others=others)

    if not os.path.exists(os.path.join(namedir, "doc", "conf.py")):
      #create a minimal conf.py
      d["conf.py"]=docconf.substitute(module=self.module.name)

    self.makeFiles(d,os.path.join(namedir,"doc"))

  def makeGui(self,namedir):
    if not self.module.gui:
      return
    ispython=False
    iscpp=False
    #Force creation of intermediate directories
    os.makedirs(os.path.join(namedir, "src", self.module.name+"GUI"))

    for srcs in self.module.gui:
      for src in glob.glob(srcs):
        shutil.copyfile(src, os.path.join(namedir, "src", self.module.name+"GUI", os.path.basename(src)))
        if src[-3:]==".py":ispython=True
        if src[-4:]==".cxx":iscpp=True
    if ispython and iscpp:
      raise Invalid("Module GUI must be pure python or pure C++ but not mixed")
    if ispython:
      return self.makePyGUI(namedir)
    if iscpp:
      return self.makeCPPGUI(namedir)
    raise Invalid("Module GUI must be in python or C++ but it is none of them")

  def makePyGUI(self,namedir):
    d={}
    if not os.path.exists(os.path.join(namedir, "src", self.module.name+"GUI", "Makefile.am")):
      #create a minimal makefile.am
      sources=[]
      other=[]
      for srcs in self.module.gui:
        for src in glob.glob(srcs):
          if src[-3:]==".py":
            sources.append(os.path.basename(src))
          else:
            other.append(os.path.basename(src))
      makefile=pyguimakefile.substitute(sources=" ".join(sources),other_sources=" ".join(other))
      d["Makefile.am"]=makefile

    if not os.path.exists(os.path.join(namedir, "src", self.module.name+"GUI", "SalomeApp.xml")):
      #create a minimal SalomeApp.xml
      salomeapp=pysalomeapp.substitute(module=self.module.name,lmodule=self.module.name.lower())
      d["SalomeApp.xml"]=salomeapp

    return d

  def makeCPPGUI(self,namedir):
    d={}
    if not os.path.exists(os.path.join(namedir, "src", self.module.name+"GUI", "Makefile.am")):
      #create a minimal makefile.am
      sources=[]
      other=[]
      ui_files=[]
      for srcs in self.module.gui:
        for src in glob.glob(srcs):
          if src[-4:]==".cxx":
            sources.append(os.path.basename(src))
          elif src[-2:]==".h":
            sources.append(os.path.basename(src)[:-2]+"_moc.cxx")
          elif src[-3:]==".ui":
            ui_files.append("ui_"+os.path.basename(src)[:-3]+".h")
          elif src[-3:]==".ts":
            other.append(os.path.basename(src)[:-3]+".qm")
          else:
            other.append(os.path.basename(src))

      makefile=cppguimakefile.substitute(sources=" ".join(sources),other_sources=" ".join(other),
                                         module=self.module.name, uisources= " ".join(ui_files))
      d["Makefile.am"]=makefile

    if not os.path.exists(os.path.join(namedir, "src", self.module.name+"GUI", "SalomeApp.xml")):
      #create a minimal SalomeApp.xml
      salomeapp=cppsalomeapp.substitute(module=self.module.name,lmodule=self.module.name.lower())
      d["SalomeApp.xml"]=salomeapp

    return d

  def makeMakefile(self,makefileItems):
    makefile=""
    if makefileItems.has_key("header"):
      makefile=makefile + makefileItems["header"]+'\n'
    if makefileItems.has_key("lib_LTLIBRARIES"):
      makefile=makefile+"lib_LTLIBRARIES= "+" ".join(makefileItems["lib_LTLIBRARIES"])+'\n'
    if makefileItems.has_key("salomepython_PYTHON"):
      makefile=makefile+"salomepython_PYTHON= "+" ".join(makefileItems["salomepython_PYTHON"])+'\n'
    if makefileItems.has_key("dist_salomescript_SCRIPTS"):
      makefile=makefile+"dist_salomescript_SCRIPTS= "+" ".join(makefileItems["dist_salomescript_SCRIPTS"])+'\n'
    if makefileItems.has_key("salomeres_DATA"):
      makefile=makefile+"salomeres_DATA= "+" ".join(makefileItems["salomeres_DATA"])+'\n'
    if makefileItems.has_key("salomeinclude_HEADERS"):
      makefile=makefile+"salomeinclude_HEADERS= "+" ".join(makefileItems["salomeinclude_HEADERS"])+'\n'
    if makefileItems.has_key("body"):
      makefile=makefile+makefileItems["body"]+'\n'
    return makefile

  def makeArgs(self, service):
    """generate source service for arguments"""
    params = []
    for name, typ in service.inport:
      if typ=="file":continue #files are not passed through service interface
      params.append("%s %s" % (corba_in_type(typ, self.module.name), name))
    for name, typ in service.outport:
      if typ=="file":continue #files are not passed through service interface
      params.append("%s %s" % (corba_out_type(typ, self.module.name), name))
    return ",".join(params)

  def makeCatalog(self):
    """generate SALOME components catalog source"""
    components = []
    for compo in self.module.components:
      services = []
      for serv in compo.services:
        params = []
        for name, typ in serv.inport:
          params.append(cataInparam.substitute(name=name, type=typ))
        inparams = "\n".join(params)
        params = []
        for name, typ in serv.outport:
          params.append(cataOutparam.substitute(name=name, type=typ))
        if serv.ret != "void" :
          params.append(cataOutparam.substitute(name="return", type=serv.ret))
        outparams = "\n".join(params)
        streams = []
        for name, typ, dep in serv.instream:
          streams.append(cataInStream.substitute(name=name, type=calciumTypes[typ], dep=dep))
        for name, typ, dep in serv.outstream:
          streams.append(cataOutStream.substitute(name=name, type=calciumTypes[typ], dep=dep))
        for name, typ in serv.parallel_instream:
          streams.append(cataInParallelStream.substitute(name=name, type=DatastreamParallelTypes[typ]))
        for name, typ in serv.parallel_outstream:
          streams.append(cataOutParallelStream.substitute(name=name, type=DatastreamParallelTypes[typ]))
        datastreams = "\n".join(streams)
        services.append(cataService.substitute(service=serv.name, author="EDF-RD",
                                               inparams=inparams, outparams=outparams, datastreams=datastreams))
      impltype, implname = compo.getImpl()
      components.append(cataCompo.substitute(component=compo.name, author="EDF-RD", impltype=impltype, implname=implname,
                                             services='\n'.join(services)))
    return catalog.substitute(components='\n'.join(components))

  def makeidl(self):
    """generate module IDL file source (CORBA interface)"""
    from pacocompo import PACOComponent
    interfaces = []
    idldefs=""
    for compo in self.module.components:
      if isinstance(compo, PACOComponent):
        services = []
        for serv in compo.services:
          params = []
          for name, typ in serv.inport:
            if typ == "file":continue #files are not passed through IDL interface
            params.append("in %s %s" % (idlTypes[typ], name))
          for name, typ in serv.outport:
            if typ == "file":continue #files are not passed through IDL interface
            params.append("out %s %s" % (idlTypes[typ], name))
          service = "    void %s(" % serv.name
          service = service+",".join(params)+");"
          services.append(service)

        interfaces.append(parallel_interface.substitute(component=compo.name, services="\n".join(services)))

      else:
        services = []
        for serv in compo.services:
          params = []
          for name, typ in serv.inport:
            if typ == "file":continue #files are not passed through IDL interface
            if compo.impl in ("PY", "ASTER") and typ == "pyobj":
              typ = "Engines::fileBlock"
            else:
              typ=idlTypes[typ]
            params.append("in %s %s" % (typ, name))
          for name, typ in serv.outport:
            if typ == "file":continue #files are not passed through IDL interface
            if compo.impl in ("PY", "ASTER") and typ == "pyobj":
              typ = "Engines::fileBlock"
            else:
              typ=idlTypes[typ]
            params.append("out %s %s" % (typ, name))
          service = "    %s %s(" % (idlTypes[serv.ret],serv.name)
          service = service+",".join(params)+") raises (SALOME::SALOME_Exception);"
          services.append(service)

        from hxxcompo import HXX2SALOMEComponent
        from hxxparacompo import HXX2SALOMEParaComponent
        if isinstance(compo,HXX2SALOMEComponent) or isinstance(compo,HXX2SALOMEParaComponent):
          from hxx_tmpl import interfaceidlhxx
          Inherited=""
          if isinstance(compo,HXX2SALOMEParaComponent):
              Inherited="SALOME_MED::ParaMEDMEMComponent"
              idldefs="""#include "ParaMEDMEMComponent.idl"\n"""
          else:
              if compo.use_medmem==True:
                  Inherited="Engines::EngineComponent,SALOME::MultiCommClass,SALOME_MED::MED_Gen_Driver"
              else:
                  Inherited="Engines::EngineComponent"
          interfaces.append(interfaceidlhxx.substitute(component=compo.name,inherited=Inherited, services="\n".join(services)))
        else:
          inheritedinterface=""
          if compo.inheritedinterface:
            inheritedinterface=compo.inheritedinterface+","
          interfaces.append(interface.substitute(component=compo.name, services="\n".join(services),inheritedinterface=inheritedinterface))

    #build idl includes for SALOME modules
    for mod in self.used_modules:
      idldefs = idldefs + salome_modules[mod]["idldefs"]

    for compo in self.module.components:
      if compo.interfacedefs:
        idldefs = idldefs + compo.interfacedefs

    return idl.substitute(module=self.module.name, interfaces='\n'.join(interfaces),idldefs=idldefs)

  # For PaCO++
  def makexml(self):
    from pacocompo import PACOComponent
    interfaces = []
    for compo in self.module.components:
      if isinstance(compo, PACOComponent):
        services = []
        for serv in compo.services:
          if serv.impl_type == "parallel":
            service = xml_service.substitute(service_name=serv.name)
            services.append(service)
        interfaces.append(xml_interface.substitute(component=compo.name, xml_services="\n".join(services)))
    return xml.substitute(module=self.module.name, interfaces='\n'.join(interfaces))

  def makeFiles(self, dic, basedir):
    """create files and directories defined in dictionary dic in basedir directory
       dic key = file name to create
       dic value = file content or dictionary defining the content of a sub directory
    """
    for name, content in dic.items():
      filename = os.path.join(basedir, name)
      if isinstance(content, str):
        fil =  open(filename, 'w')
        fil.write(content)
        fil.close()
      else:
        if not os.path.exists(filename):
          os.makedirs(filename)
        self.makeFiles(content, filename)

  def bootstrap(self):
    """Execute the first build step (bootstrap autotools with autogen.sh script) : execution of libtool, autoconf, automake"""
    ier = os.system("cd %s_SRC;sh autogen.sh" % self.module.name)
    if ier != 0:
      raise Invalid("bootstrap has ended in error")

  def configure(self):
    """Execute the second build step (configure) with installation prefix as given by the prefix attribute of module"""
    prefix = self.module.prefix
    paco = self.context.get("paco")
    mpi = self.context.get("mpi")
    args = (self.module.name, self.kernel, self.aster)
    cmd = "cd %s_SRC;./configure --with-kernel=%s --with-aster=%s" % args
    if self.gui:
      cmd = cmd + " --with-gui=%s" % self.gui
    if prefix:
      prefix = os.path.abspath(prefix)
      cmd = cmd + " --prefix=%s" % prefix
    if paco:
      cmd += " --with-paco=%s" % paco
    if mpi:
      cmd += " --with-mpi=%s" % mpi

    ier = os.system(cmd)
    if ier != 0:
      raise Invalid("configure has ended in error")

  def make(self):
    """Execute the third build step (compile and link) : make"""
    make_command = "make "
    if self.makeflags:
      make_command += self.makeflags
    ier = os.system("cd %s_SRC;%s" % (self.module.name, make_command))
    if ier != 0:
      raise Invalid("make has ended in error")

  def install(self):
    """Execute the installation step : make install """
    makedirs(self.module.prefix)
    ier = os.system("cd %s_SRC;make install" % self.module.name)
    if ier != 0:
      raise Invalid("install has ended in error")

  def make_appli(self, appliname, restrict=None, altmodules=None, resources=""):
    """
   Create a SALOME application containing the module and preexisting SALOME modules.

   :param appliname: is a string that gives the name of the application (directory path where the application
      will be installed).
   :type appliname: str
   :param restrict: If given (a list of module names), only those SALOME modules will be included in the
      application. The default is to include all modules that are located in the same directory as the KERNEL module and have
      the same suffix (for example, if KERNEL directory is KERNEL_V5 and GEOM directory is GEOM_V5, GEOM module is automatically
      included, except if restrict is used).
   :param altmodules: can be used to add SALOME modules that cannot be managed with the precedent rule. This parameter
      is a dict with a module name as the key and the installation path as the value.
   :param resources: can be used to define an alternative resources catalog (path of the file).

   For example, the following calls create a SALOME application with external modules and resources catalog in "appli" directory::

     >>> g=Generator(m,context)
     >>> g.generate()
     >>> g.bootstrap()
     >>> g.configure()
     >>> g.make()
     >>> g.install()
     >>> g.make_appli("appli", restrict=["KERNEL"], altmodules={"GUI":GUI_ROOT_DIR, "YACS":YACS_ROOT_DIR},
                      resources="myresources.xml")

    """
    makedirs(appliname)

    rootdir, kerdir = os.path.split(self.kernel)

    #collect modules besides KERNEL module with the same suffix if any
    modules_dict = {}
    if kerdir[:6] == "KERNEL":
      suffix = kerdir[6:]
      for mod in os.listdir(rootdir):
        if mod[-len(suffix):] == suffix:
          module = mod[:-len(suffix)]
          path = os.path.join(rootdir, mod)
          #try to find catalog files
          lcata = glob.glob(os.path.join(path, "share", "salome", "resources", "*", "*Catalog.xml"))
          if not lcata:
            #catalogs have not been found : try the upper level
            lcata = glob.glob(os.path.join(path, "share", "salome", "resources", "*Catalog.xml"))
          if lcata:
            #catalogs have been found : add the corresponding entries in the application
            for cata in lcata:
              catadir, catafile = os.path.split(cata)
              name = catafile[:-11]
              modules_dict[name] = '  <module name="%s" path="%s"/>' % (name, path)
          else:
            modules_dict[module] = '  <module name="%s" path="%s"/>' % (module, path)

    modules_dict["KERNEL"] = '  <module name="KERNEL" path="%s"/>' % self.kernel

    #keep only the modules which names are in restrict if given
    modules = []
    if restrict:
      for mod in restrict:
        if modules_dict.has_key(mod):
          modules.append(modules_dict[mod])
    else:
      modules = modules_dict.values()

    #add the alternate modules if given
    if altmodules:
      for module, path in altmodules.items():
        modules.append('  <module name="%s" path="%s"/>' % (module, path))

    #add the generated module
    modules.append('  <module name="%s" path="%s"/>' % (self.module.name, os.path.abspath(self.module.prefix)))


    #try to find a prerequisites file
    prerequisites = self.context.get("prerequisites")
    if not prerequisites:
      #try to find one in rootdir
      prerequisites = os.path.join(rootdir, "profile%s.sh" % suffix)
    if not os.path.exists(prerequisites):
      raise Invalid("Can not create an application : prerequisites file not defined or does not exist")

    #add resources catalog if it exists
    resources_spec=""
    if os.path.isfile(resources):
      resources_spec='<resources path="%s" />' % os.path.abspath(resources)

    #create config_appli.xml file
    appli = application.substitute(prerequisites=prerequisites,
                                   modules="\n".join(modules),
                                   resources=resources_spec)
    fil = open(os.path.join(appliname, "config_appli.xml"), 'w')
    fil.write(appli)
    fil.close()

    #execute appli_gen.py script
    appligen = os.path.join(self.kernel, "bin", "salome", "appli_gen.py")
    ier = os.system("cd %s;%s" % (appliname, appligen))
    if ier != 0:
      raise Invalid("make_appli has ended in error")

    #add CatalogResources.xml if not created by appli_gen.py
    if not os.path.exists(os.path.join(appliname, "CatalogResources.xml")):
      #CatalogResources.xml does not exist create a minimal one
      fil  = open(os.path.join(appliname, 'CatalogResources.xml'), 'w')
      command = """<!DOCTYPE ResourcesCatalog>
<resources>
    <machine hostname="%s" protocol="ssh" mode="interactive" />
</resources>
"""
      host = socket.gethostname().split('.')[0]
      fil.write(command % host)
      fil.close()

