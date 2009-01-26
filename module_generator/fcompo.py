
from gener import Component
from cppcompo import CPPComponent

import platform
archi = platform.architecture()[0]

if archi == "64bit":
  f77Types = {"double":"double *", "long":"int *", "string":"const char *"}
else:
  f77Types = {"double":"double *", "long":"long *", "string":"const char *"}

class F77Component(CPPComponent):
  def __init__(self, name, services=None, libs="", rlibs="", 
                     kind="lib", exe_path=None, sources=None):
    CPPComponent.__init__(self, name, services, libs=libs, rlibs=rlibs, 
                                kind=kind, exe_path=exe_path, sources=sources)
    self.impl = "F77"

  def makebody(self):
    for serv in self.services:
      #defs generation
      params = ["void *compo"]
      strparams = []
      for name, typ in serv.inport:
        if typ == "string":
          params.append("const STR_PSTR(%s)"%name)
          strparams.append("STR_PLEN(%s)"%name)
        else:
          params.append("%s %s" % (f77Types[typ], name))
      for name, typ in serv.outport:
        if typ == "string":
          params.append("const STR_PSTR(%s)"%name)
          strparams.append("STR_PLEN(%s)"%name)
        else:
          params.append("%s %s" % (f77Types[typ], name))
      args = ','.join(params)+" " + " ".join(strparams)
      serv.defs = serv.defs+'\nextern "C" void F_FUNC(%s,%s)(%s);' % (serv.name.lower(), serv.name.upper(), args)

      #body generation
      params = ["&component"]
      strparams = []
      strallocs = []
      #length allocated for out string
      lstr = 20
      for name, typ in serv.inport:
        if typ == "string":
          params.append("STR_CPTR(%s)" % name)
          strparams.append("STR_CLEN(%s)"%name)
        else:
          params.append("&%s" % name)
      for name, typ in serv.outport:
        if typ == "string":
          params.append("STR_CPTR(%s.ptr())" % name)
          strparams.append("STR_CLEN(%s.ptr())"%name)
          strallocs.append('%s=CORBA::string_dup("%s");' %(name, " "*lstr))
        else:
          params.append("&%s" % name)
      serv.body = '\n'.join(strallocs)+'\n'+serv.body
      args = ','.join(params)+" " + " ".join(strparams)
      serv.body = serv.body+"\n   F_CALL(%s,%s)(%s);" % (serv.name.lower(), serv.name.upper(), args)

  def makeCompo(self, gen):
    self.makebody()
    return CPPComponent.makeCompo(self, gen)
