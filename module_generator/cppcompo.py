#  Copyright (C) 2009-2010  EDF R&D
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 2.1 of the License.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#  See http://www.salome-platform.org/ or email : webmaster.salome@opencascade.com
#

"""
  Module that defines CPPComponent for SALOME components implemented in C++
"""

import os
from gener import Component, Invalid
from cpp_tmpl import initService, cxxService, hxxCompo, cxxCompo
from cpp_tmpl import exeCPP, compoEXEMakefile, compoMakefile

class CPPComponent(Component):
  def __init__(self, name, services=None, libs="", rlibs="", includes="",
                     kind="lib", exe_path=None, sources=None, inheritedclass="",
                     compodefs=""):
    self.exe_path = exe_path
    Component.__init__(self, name, services, impl="CPP", libs=libs,
                             rlibs=rlibs, includes=includes, kind=kind,
                             sources=sources,inheritedclass=inheritedclass,
                             compodefs=compodefs)

  def validate(self):
    """ validate component definition parameters"""
    Component.validate(self)
    kinds = ("lib", "exe")
    if self.kind not in kinds:
      raise Invalid("kind must be one of %s for component %s" % (kinds,self.name))

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
      return {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
              cxxfile:self.makecxx(gen),
              hxxfile:self.makehxx(gen)
             }
    if self.kind == "exe":
      return {"Makefile.am":gen.makeMakefile(self.getMakefileItems(gen)),
              self.name+".exe":exeCPP.substitute(compoexe=self.exe_path),
              cxxfile:self.makecxx(gen, 1),
              hxxfile:self.makehxx(gen)
             }

  def getMakefileItems(self,gen):
    makefileItems={"header":"""
include $(top_srcdir)/adm_local/make_common_starter.am

AM_CFLAGS=$(SALOME_INCLUDES) -fexceptions
"""}
    if self.kind == "lib":
      makefileItems["lib_LTLIBRARIES"]=["lib"+self.name+"Engine.la"]
      makefileItems["salomeinclude_HEADERS"]=[self.name+".hxx"]
      makefileItems["body"]=compoMakefile.substitute(module=gen.module.name,
                                                     component=self.name,
                                                     libs=self.libs,
                                                     rlibs=self.rlibs,
                                                     sources= " ".join(map(os.path.basename,self.sources)),
                                                     includes=self.includes)
    elif self.kind == "exe":
      makefileItems["lib_LTLIBRARIES"]=["lib"+self.name+"Exelib.la"]
      makefileItems["salomeinclude_HEADERS"]=[self.name+".hxx"]
      makefileItems["dist_salomescript_SCRIPTS"]=[self.name+".exe"]
      makefileItems["body"]=compoEXEMakefile.substitute(module=gen.module.name,
                                                        component=self.name,
                                                        libs=self.libs,
                                                        rlibs=self.rlibs,
                                                        includes=self.includes)
    return makefileItems

  def makehxx(self, gen):
    """return a string that is the content of .hxx file
    """
    services = []
    for serv in self.services:
      service = "    void %s(" % serv.name
      service = service+gen.makeArgs(serv)+");"
      services.append(service)
    servicesdef = "\n".join(services)

    inheritedclass=self.inheritedclass
    if self.inheritedclass:
      inheritedclass= " public virtual " + self.inheritedclass + ","

    return hxxCompo.substitute(component=self.name, module=gen.module.name,
                               servicesdef=servicesdef, inheritedclass=inheritedclass,
                               compodefs=self.compodefs)

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
        streams.append('          create_calcium_port(this,(char *)"%s",(char *)"%s",(char *)"IN",(char *)"%s");'% (name, typ, dep))
      instream = "\n".join(streams)
      streams = []
      for name, typ, dep in serv.outstream:
        streams.append('          create_calcium_port(this,(char *)"%s",(char *)"%s",(char *)"OUT",(char *)"%s");'% (name, typ, dep))
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

