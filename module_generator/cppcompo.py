"""
  Module that defines CPPComponent for SALOME components implemented in C++
"""

import os
from gener import Component, Invalid
from cpp_tmpl import initService, cxxService, hxxCompo, cxxCompo
from cpp_tmpl import compoEXEMakefile, compoMakefile, exeCPP

class CPPComponent(Component):
  def __init__(self, name, services=None, libs="", rlibs="", includes="", 
                     kind="lib", exe_path=None, sources=None):
    self.exe_path = exe_path
    Component.__init__(self, name, services, impl="CPP", libs=libs, 
                             rlibs=rlibs, includes=includes, kind=kind,
                             sources=sources)

  def validate(self):
    """ validate component definition parameters"""
    Component.validate(self)
    kinds = ("lib", "exe")
    if self.kind not in kinds:
      raise Invalid("kind must be one of %s" % kinds)

    if self.kind == "exe" :
      if not self.exe_path:
        raise Invalid("exe_path must be defined for component %s" % self.name)

  def makeCompo(self, gen):
    """generate files for C++ component
       
       return a dict where key is the file name and value is the content of the file
    """
    cxxfile = "%s.cxx" % self.name
    hxxfile = "%s.hxx" % self.name
    if self.kind == "lib":
      sources = " ".join(map(os.path.basename,self.sources))
      return {"Makefile.am":compoMakefile.substitute(module=gen.module.name, 
                                                     component=self.name,
                                                     libs=self.libs, 
                                                     rlibs=self.rlibs,
                                                     sources=sources,
                                                     includes=self.includes),
              cxxfile:self.makecxx(gen), hxxfile:self.makehxx(gen)}
    if self.kind == "exe":
      return {"Makefile.am":compoEXEMakefile.substitute(module=gen.module.name, 
                                                        component=self.name,
                                                        libs=self.libs, 
                                                        rlibs=self.rlibs,
                                                        includes=self.includes),
              self.name+".exe":exeCPP.substitute(compoexe=self.exe_path),
              cxxfile:self.makecxx(gen, 1), hxxfile:self.makehxx(gen)}

  def makehxx(self, gen):
    """return a string that is the content of .hxx file
    """
    services = []
    for serv in self.services:
      service = "    void %s(" % serv.name
      service = service+gen.makeArgs(serv)+");"
      services.append(service)
    servicesdef = "\n".join(services)
    return hxxCompo.substitute(component=self.name, module=gen.module.name, 
                               servicesdef=servicesdef)

  def makecxx(self, gen, exe=0):
    """return a string that is the content of .cxx file
    """
    services = []
    inits = []
    defs = []
    for serv in self.services:
      defs.append(serv.defs)
      service = cxxService.substitute(component=self.name, service=serv.name, 
                                      parameters=gen.makeArgs(serv),
                                      body=serv.body, exe=exe)
      streams = []
      for name, typ, dep in serv.instream:
        streams.append('          create_calcium_port(this,"%s","%s","IN","%s");'% (name, typ, dep))
      instream = "\n".join(streams)
      streams = []
      for name, typ, dep in serv.outstream:
        streams.append('          create_calcium_port(this,"%s","%s","OUT","%s");'% (name, typ, dep))
      outstream = "\n".join(streams)

      init = initService.substitute(component=self.name, service=serv.name,
                                    instream=instream, outstream=outstream)
      services.append(service)
      inits.append(init)
    return cxxCompo.substitute(component=self.name, module=gen.module.name, 
                               exe=exe, exe_path=self.exe_path, 
                               servicesdef="\n".join(defs), 
                               servicesimpl="\n".join(services), 
                               initservice='\n'.join(inits))

