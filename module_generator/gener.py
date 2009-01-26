import os, shutil, glob, socket

try:
  from string import Template
except:
  from compat import Template, set

class Invalid(Exception):
  pass

from mod_tmpl import resMakefile, makecommon, configure
from mod_tmpl import mainMakefile, autogen, application
from cata_tmpl import catalog, interface, idl, idlMakefile
from cata_tmpl import cataOutStream, cataInStream, cataOutparam, cataInparam
from cata_tmpl import cataService, cataCompo
from aster_tmpl import check_aster

corbaTypes = {"double":"CORBA::Double", "long":"CORBA::Long",
              "string":"const char*", "dblevec":"const %s::dblevec&",
              "stringvec":"const %s::stringvec&", "intvec":"const %s::intvec&"}
corbaOutTypes = {"double":"CORBA::Double&", "long":"CORBA::Long&",
                "string":"CORBA::String_out", "dblevec":"%s::dblevec_out",
                "stringvec":"%s::stringvec_out", "intvec":"%s::intvec_out"}

def corba_in_type(typ, module):
  if typ in ("dblevec", "intvec", "stringvec"):
    return corbaTypes[typ] % module
  else:
    return corbaTypes[typ]

def corba_out_type(typ, module):
  if typ in ("dblevec", "intvec", "stringvec"):
    return corbaOutTypes[typ] % module
  else:
    return corbaOutTypes[typ]

calciumTypes = {"CALCIUM_double":"CALCIUM_double", 
                "CALCIUM_integer":"CALCIUM_integer", 
                "CALCIUM_real":"CALCIUM_real",
                "CALCIUM_string":"CALCIUM_string", 
                "CALCIUM_complex":"CALCIUM_complex", 
                "CALCIUM_logical":"CALCIUM_logical",
               } 

ValidImpl = ("CPP", "PY", "F77", "ASTER")
ValidTypes = corbaTypes.keys()
ValidStreamTypes = calciumTypes.keys()
ValidDependencies = ("I", "T")
PyValidTypes = ValidTypes+["pyobj"]

def makedirs(namedir):
  if os.path.exists(namedir):
    dirbak = namedir+".bak"
    if os.path.exists(dirbak):
      shutil.rmtree(dirbak)
    os.rename(namedir, dirbak)
    os.listdir(dirbak) #sert seulement a mettre a jour le systeme de fichier sur certaines machines
  os.makedirs(namedir)

class Module(object):
  def __init__(self, name, components=None, prefix=""):
    self.name = name
    self.components = components or []
    self.prefix = prefix or "%s_INSTALL" % name
    self.validate()

  def validate(self):
    lcompo = set()
    for compo in self.components:
      if compo.name in lcompo:
        raise Invalid("%s is already defined as a component of the module" % compo.name)
      lcompo.add(compo.name)
      compo.validate()

class Component(object):
  def __init__(self, name, services=None, impl="PY", libs="", rlibs="", 
                     includes="", kind="lib", sources=None):
    self.name = name
    self.impl = impl
    self.kind = kind
    self.services = services or []
    self.libs = libs
    self.rlibs = rlibs
    self.includes = includes
    self.sources = sources or []

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

class Service(object):
  def __init__(self, name, inport=None, outport=None, instream=None, 
                     outstream=None, body="", defs=""):
    self.name = name
    self.inport = inport or []
    self.outport = outport or []
    self.instream = instream or []
    self.outstream = outstream or []
    self.defs = defs
    self.body = body
    self.impl = ""

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

class Generator(object):
  def __init__(self, module, context=None):
    self.module = module
    self.context = context or {}
    self.kernel = self.context["kernel"]
    self.aster = ""

  def generate(self):
    module = self.module
    namedir = module.name+"_SRC"
    force = self.context.get("force")
    update = self.context.get("update")
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
    makefiles = []
    for compo in module.components:
      makefile = makefile+" "+compo.name
      srcs[compo.name] = compo.makeCompo(self)
      makefiles.append("     src/"+compo.name+"/Makefile")

    srcs["Makefile.am"] = makefile+'\n'
    idlfile = "%s.idl" % module.name
    catalogfile = "%sCatalog.xml" % module.name

    self.makeFiles({"autogen.sh":autogen,
                    "Makefile.am":mainMakefile,
                    "README":"", "NEWS":"", "AUTHORS":"", "ChangeLog":"",
                    "configure.ac":configure.substitute(module=module.name.lower(), makefiles='\n'.join(makefiles)),
                    "idl":{"Makefile.am":idlMakefile.substitute(module=module.name), idlfile:self.makeidl()},
                    "src":srcs,
                    "resources":{"Makefile.am":resMakefile.substitute(module=module.name), catalogfile:self.makeCatalog()},
                    "adm_local":{"make_common_starter.am":makecommon, "check_aster.m4":check_aster},
                    }, namedir)
    os.chmod(os.path.join(namedir, "autogen.sh"), 0777)
    #copy source files if any in creates tree
    for compo in module.components:
      for src in compo.sources:
        shutil.copyfile(src, os.path.join(namedir, "src", compo.name, src))

    for m4file in ("check_Kernel.m4", "check_omniorb.m4", 
                   "ac_linker_options.m4", "ac_cxx_option.m4",
                   "python.m4", "enable_pthreads.m4", "check_f77.m4", 
                   "acx_pthread.m4", "check_boost.m4"):
      shutil.copyfile(os.path.join(self.kernel, "salome_adm", "unix", "config_files", m4file), 
                      os.path.join(namedir, "adm_local", m4file))

    return

  def makeArgs(self, service):
    params = []
    for name, typ in service.inport:
      params.append("%s %s" % (corba_in_type(typ, self.module.name), name))
    for name, typ in service.outport:
      params.append("%s %s" % (corba_out_type(typ, self.module.name), name))
    return ",".join(params)

  def makeCatalog(self):
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
        outparams = "\n".join(params)
        streams = []
        for name, typ, dep in serv.instream:
          streams.append(cataInStream.substitute(name=name, type=calciumTypes[typ], dep=dep))
        for name, typ, dep in serv.outstream:
          streams.append(cataOutStream.substitute(name=name, type=calciumTypes[typ], dep=dep))
        datastreams = "\n".join(streams)
        services.append(cataService.substitute(service=serv.name, author="EDF-RD",
                                               inparams=inparams, outparams=outparams, datastreams=datastreams))
      impltype, implname = compo.getImpl()
      components.append(cataCompo.substitute(component=compo.name, author="EDF-RD", impltype=impltype, implname=implname,
                                             services='\n'.join(services)))
    return catalog.substitute(components='\n'.join(components))

  def makeidl(self):
    interfaces = []
    for compo in self.module.components:
      services = []
      for serv in compo.services:
        params = []
        for name, typ in serv.inport:
          if compo.impl in ("PY", "ASTER") and typ == "pyobj":
            typ = "Engines::fileBlock"
          params.append("in %s %s" % (typ, name))
        for name, typ in serv.outport:
          if compo.impl in ("PY", "ASTER") and typ == "pyobj":
            typ = "Engines::fileBlock"
          params.append("out %s %s" % (typ, name))
        service = "    void %s(" % serv.name
        service = service+",".join(params)+") raises (SALOME::SALOME_Exception);"
        services.append(service)
      interfaces.append(interface.substitute(component=compo.name, services="\n".join(services)))
    return idl.substitute(module=self.module.name, interfaces='\n'.join(interfaces))

  def makeFiles(self, dic, basedir):
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
    ier = os.system("cd %s_SRC;sh autogen.sh" % self.module.name)
    if ier != 0:
      raise Invalid("bootstrap has ended in error")

  def configure(self):
    prefix = self.module.prefix
    if prefix:
      prefix = os.path.abspath(prefix)
      cmd = "cd %s_SRC;./configure --with-kernel=%s --with-aster=%s --prefix=%s"
      ier = os.system(cmd % (self.module.name, self.kernel, self.aster, prefix))
    else:
      cmd = "cd %s_SRC;./configure --with-kernel=%s --with-aster=%s"
      ier = os.system(cmd % (self.module.name, self.kernel, self.aster))
    if ier != 0:
      raise Invalid("configure has ended in error")

  def make(self):
    ier = os.system("cd %s_SRC;make" % self.module.name)
    if ier != 0:
      raise Invalid("make has ended in error")

  def install(self):
    ier = os.system("cd %s_SRC;make install" % self.module.name)
    if ier != 0:
      raise Invalid("install has ended in error")

  def make_appli(self, appliname, restrict=None, altmodules=None):
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

    #create config_appli.xml file
    appli = application.substitute(prerequisites=prerequisites, modules="\n".join(modules))
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

