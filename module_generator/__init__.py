import os,shutil,string,glob,socket
import re
import platform
try:
  from string import Template
except:
  from compat import Template,set

class Invalid(Exception):pass

archi=platform.architecture()[0]


corbaTypes={"double":"CORBA::Double","long":"CORBA::Long","string":"const char*",
    "dblevec":"const %s::dblevec&","stringvec":"const %s::stringvec&","intvec":"const %s::intvec&"}
corbaOutTypes={"double":"CORBA::Double&","long":"CORBA::Long&","string":"CORBA::String_out",
    "dblevec":"%s::dblevec_out","stringvec":"%s::stringvec_out","intvec":"%s::intvec_out"}

def corba_in_type(typ,module):
  if typ in ("dblevec","intvec","stringvec"):
    return corbaTypes[typ] % module
  else:
    return corbaTypes[typ]

def corba_out_type(typ,module):
  if typ in ("dblevec","intvec","stringvec"):
    return corbaOutTypes[typ] % module
  else:
    return corbaOutTypes[typ]

if archi == "64bit":
  f77Types={"double":"double *","long":"int *","string":"const char *"}
else:
  f77Types={"double":"double *","long":"long *","string":"const char *"}

calciumTypes={"CALCIUM_double":"CALCIUM_double","CALCIUM_integer":"CALCIUM_integer","CALCIUM_real":"CALCIUM_real",
                "CALCIUM_string":"CALCIUM_string","CALCIUM_complex":"CALCIUM_complex","CALCIUM_logical":"CALCIUM_logical",
               } 

ValidImpl=("CPP","PY","F77","ASTER")
ValidTypes=corbaTypes.keys()
ValidStreamTypes=calciumTypes.keys()
ValidDependencies=("I","T")
PyValidTypes=ValidTypes+["pyobj"]

def makedirs(namedir):
  if os.path.exists(namedir):
    dirbak=namedir+".bak"
    if os.path.exists(dirbak):
      shutil.rmtree(dirbak)
    os.rename(namedir,dirbak)
    os.listdir(dirbak) #sert seulement a mettre a jour le systeme de fichier sur certaines machines
  os.makedirs(namedir)

class Module(object):
  def __init__(self,name,components=None,prefix=""):
    self.name=name
    self.components=components or []
    self.prefix=prefix or "%s_INSTALL" % name
    self.validate()

  def validate(self):
    l=set()
    for c in self.components:
      if c.name in l:
        raise Invalid("%s is already defined as a component of the module" % c.name)
      l.add(c.name)

class Component(object):
  def __init__(self,name,services=None,impl="PY",libs="",rlibs="",includes="",kind="lib"):
    self.name=name
    self.impl=impl
    self.kind=kind
    self.services=services or []
    self.libs=libs
    self.rlibs=rlibs
    self.includes=includes
    self.validate()

  def validate(self):
    if self.impl not in ValidImpl:
      raise Invalid("%s is not a valid implementation. It should be one of %s" % (self.impl,ValidImpl))

    l=set()
    for s in self.services:
      s.impl=self.impl
      if s.name in l:
        raise Invalid("%s is already defined as a component of the module" % s.name)
      l.add(s.name)
      s.validate()

  def getImpl(self):
    return "SO",""

exeCPP="""#!/bin/sh

export SALOME_CONTAINER=$$1
export SALOME_CONTAINERNAME=$$2
export SALOME_INSTANCE=$$3

${compoexe}
"""
exeCPP=Template(exeCPP)

class CPPComponent(Component):
  def __init__(self,name,services=None,libs="",rlibs="",includes="",kind="lib",exe_path=None):
    self.exe_path=exe_path
    Component.__init__(self,name,services,impl="CPP",libs=libs,rlibs=rlibs,includes=includes,kind=kind)

  def validate(self):
    Component.validate(self)
    kinds=("lib","exe")
    if self.kind not in kinds:
        raise Invalid("kind must be one of %s" % kinds)

    if self.kind == "exe" :
        if not self.exe_path:
          raise Invalid("exe_path must be defined for component %s" % self.name)

  def makeCompo(self,gen):
    cxxFile="%s.cxx" % self.name
    hxxFile="%s.hxx" % self.name
    if self.kind=="lib":
      return {"Makefile.am":compoMakefile.substitute(module=gen.module.name,component=self.name,
                                                   libs=self.libs,rlibs=self.rlibs,
                                                   includes=self.includes),
              cxxFile:gen.makeCXX(self),hxxFile:gen.makeHXX(self)}
    if self.kind=="exe":
      return {"Makefile.am":compoEXEMakefile.substitute(module=gen.module.name,component=self.name,
                                                   libs=self.libs,rlibs=self.rlibs,
                                                   includes=self.includes),
              self.name+".exe":exeCPP.substitute(compoexe=self.exe_path),
              cxxFile:gen.makeCXX(self,1),hxxFile:gen.makeHXX(self)}

class PYComponent(Component):
  def __init__(self,name,services=None,python_path=None,kind="lib"):
    self.python_path=python_path or []
    Component.__init__(self,name,services,impl="PY",kind=kind)

  def validate(self):
    Component.validate(self)
    kinds=("lib","exe")
    if self.kind not in kinds:
        raise Invalid("kind must be one of %s" % kinds)

  def makeCompo(self,gen):
    pyFile="%s.py" % self.name
    if self.kind=="lib":
      return {"Makefile.am":pycompoMakefile.substitute(module=gen.module.name,component=self.name),
              pyFile:gen.makePY(self)}
    if self.kind=="exe":
      return {"Makefile.am":pycompoEXEMakefile.substitute(module=gen.module.name,component=self.name),
              self.name+".exe":self.makePYEXE(gen),
              }

  def makePYEXE(self,gen):
    services=[]
    inits=[]
    defs=[]
    for s in self.services:
      defs.append(s.defs)
      params=[]
      pyparams=[]
      for name,typ in s.inport:
        params.append(name)
        if typ=="pyobj":
          pyparams.append("      %s=cPickle.loads(%s)" %(name,name))
      inparams=",".join(params)
      convertinparams='\n'.join(pyparams)

      params=[]
      pyparams=[]
      for name,typ in s.outport:
        params.append(name)
        if typ=="pyobj":
          pyparams.append("      %s=cPickle.dumps(%s,-1)" %(name,name))
      outparams=",".join(params)
      convertoutparams='\n'.join(pyparams)
      service=pyService.substitute(component=self.name,service=s.name,inparams=inparams,
                                    outparams=outparams,body=s.body,convertinparams=convertinparams,
                                    convertoutparams=convertoutparams,
                                    )
      streams=[]
      for name,typ,dep in s.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name,typ,dep))
      instream="\n".join(streams)
      streams=[]
      for name,typ,dep in s.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name,typ,dep))
      outstream="\n".join(streams)

      init=pyinitService.substitute(component=self.name,service=s.name,
                                    instream=instream,outstream=outstream)
      services.append(service)
      inits.append(init)

    python_path=",".join([repr(p) for p in self.python_path])
    return pyCompoEXE.substitute(component=self.name,module=gen.module.name,
                              servicesdef="\n".join(defs),servicesimpl="\n".join(services),initservice='\n'.join(inits),
                              python_path=python_path)


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



class ASTERComponent(Component):
  def __init__(self,name,services=None,libs="",rlibs="",aster_dir="",python_path=None,argv=None,kind="lib",
                   exe_path=None,asrun=None):
    self.aster_dir=aster_dir
    self.python_path=python_path or []
    self.argv=argv or []
    self.exe_path=exe_path
    self.asrun=asrun
    Component.__init__(self,name,services,impl="ASTER",libs=libs,rlibs=rlibs,kind=kind)

  def validate(self):
    Component.validate(self)
    if not self.aster_dir:
        raise Invalid("aster_dir must be defined for component %s" % self.name)

    kinds=("lib","cexe","exe")
    if self.kind not in kinds:
        raise Invalid("kind must be one of %s" % kinds)
    if self.kind == "lib" and not self.python_path:
        raise Invalid("python_path must be defined for component %s" % self.name)
    if self.kind == "cexe" :
        if not self.exe_path:
          raise Invalid("exe_path must be defined for component %s" % self.name)
        if not self.asrun:
          raise Invalid("asrun must be defined for component %s" % self.name)
        if not os.path.exists(self.asrun):
          raise Invalid("asrun does not exist for component %s" % self.name)
    if self.kind == "exe" :
        if not self.exe_path:
          raise Invalid("exe_path must be defined for component %s" % self.name)
        if not self.asrun:
          raise Invalid("asrun must be defined for component %s" % self.name)
        if not os.path.exists(self.asrun):
          raise Invalid("asrun does not exist for component %s" % self.name)

    for s in self.services:
      #on ajoute un inport string de nom jdc en premier dans la liste des ports de chaque service
      s.inport.insert(0,("jdc","string"))

  def makeCompo(self,gen):
    File="%s.py" % self.name
    #on suppose que les composants ASTER sont homogenes (utilisent meme install)
    gen.aster=self.aster_dir
    if self.kind=="lib":
      return {"Makefile.am":astercompoMakefile.substitute(module=gen.module.name,component=self.name),
             File:gen.makeASTER(self)}
    elif self.kind == "cexe":
      #creation de l'installation aster dans exe_path
      self.makeCEXEPATH(gen)
      return {"Makefile.am":astercexeMakefile.substitute(module=gen.module.name,component=self.name),
             File:self.makeCEXEASTER(gen)}
    elif self.kind == "exe":
      #creation de l'installation aster dans exe_path
      self.makeEXEPATH(gen)
      return {"Makefile.am":asterexeMakefile.substitute(module=gen.module.name,component=self.name),
               self.name+".exe":exeaster.substitute(export=os.path.join(self.exe_path,"make_etude.export"),asrun=self.asrun),
               self.name+"_module.py":self.makeEXEASTER(gen)}

  def makeEXEPATH(self,gen):
    makedirs(self.exe_path)
    #patch to E_SUPERV.py
    f=open(os.path.join(self.aster_dir,"bibpyt","Execution","E_SUPERV.py"))
    esuperv=f.read()
    esuperv=re.sub("j=self.JdC","self.jdc=j=self.JdC",esuperv)
    f.close()
    #utilisation d'un programme principal python different
    f=open(os.path.join(self.aster_dir,"config.txt"))
    config=f.read()
    config=re.sub("Execution\/E_SUPERV.py",os.path.join(self.exe_path,"aster_component.py"),config)
    f.close()

    gen.makeFiles({
                   "aster_component.py":component.substitute(component=self.name),
                   "make_etude.export":make_etude.substitute(config=os.path.join(self.exe_path,"config.txt"),
                                                             comm=os.path.join(self.exe_path,self.name+".comm")),
                   self.name+".comm":comm,
                   "config.txt":config,
                   "profile.sh":os.path.join(self.aster_dir,"profile.sh"),
                   "E_SUPERV.py":esuperv,
                  }, self.exe_path)

  def makeCEXEPATH(self,gen):
    makedirs(self.exe_path)
    #patch to E_SUPERV.py
    f=open(os.path.join(self.aster_dir,"bibpyt","Execution","E_SUPERV.py"))
    esuperv=f.read()
    esuperv=re.sub("j=self.JdC","self.jdc=j=self.JdC",esuperv)
    f.close()
    #utilisation d'un programme principal python different
    f=open(os.path.join(self.aster_dir,"config.txt"))
    config=f.read()
    config=re.sub("Execution\/E_SUPERV.py",os.path.join(self.exe_path,"aster_container.py"),config)
    f.close()
    gen.makeFiles({self.name+".exe":cexe.substitute(export=os.path.join(self.exe_path,"make_etude.export"),
                                                    asrun=self.asrun),
                   "aster_container.py":container,
                   "make_etude.export":make_etude.substitute(config=os.path.join(self.exe_path,"config.txt"),
                                                             comm=os.path.join(self.exe_path,self.name+".comm")),
                   self.name+".comm":comm,
                   "config.txt":config,
                   "profile.sh":os.path.join(self.aster_dir,"profile.sh"),
                   "E_SUPERV.py":esuperv,
                  }, self.exe_path)
    #make exe executable
    os.chmod(os.path.join(self.exe_path,self.name+".exe"),0777)

  def makeEXEASTER(self,gen):
    services=[]
    inits=[]
    defs=[]
    for s in self.services:
      defs.append(s.defs)
      params=[]
      datas=[]
      for name,typ in s.inport:
        params.append(name)
        if typ == "pyobj":
          datas.append('"%s":cPickle.loads(%s)' % (name,name))
        else:
          datas.append('"%s":%s' % (name,name))
      #ajout de l'adresse du composant
      datas.append('"component":self.proxy.ptr()')
      dvars="{"+','.join(datas)+"}"
      inparams=",".join(params)

      params=[]
      datas=[]
      for name,typ in s.outport:
        params.append(name)
        if typ == "pyobj":
          datas.append('cPickle.dumps(j.g_context["%s"],-1)'%name)
        else:
          datas.append('j.g_context["%s"]'%name)
      outparams=",".join(params)
      rvars=",".join(datas)

      service=asterEXEService.substitute(component=self.name,service=s.name,inparams=inparams,
                                    outparams=outparams,body=s.body,dvars=dvars,rvars=rvars)
      streams=[]
      for name,typ,dep in s.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name,typ,dep))
      instream="\n".join(streams)
      streams=[]
      for name,typ,dep in s.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name,typ,dep))
      outstream="\n".join(streams)

      init=pyinitEXEService.substitute(component=self.name,service=s.name,
                                    instream=instream,outstream=outstream)
      services.append(service)
      inits.append(init)
    return asterEXECompo.substitute(component=self.name,module=gen.module.name,
                              servicesdef="\n".join(defs),servicesimpl="\n".join(services),initservice='\n'.join(inits),
                              aster_dir=self.aster_dir)

  def makeCEXEASTER(self,gen):
    services=[]
    inits=[]
    defs=[]
    for s in self.services:
      defs.append(s.defs)
      params=[]
      datas=[]
      for name,typ in s.inport:
        params.append(name)
        if typ == "pyobj":
          datas.append('"%s":cPickle.loads(%s)' % (name,name))
        else:
          datas.append('"%s":%s' % (name,name))
      #ajout de l'adresse du composant
      datas.append('"component":self.proxy.ptr()')
      dvars="{"+','.join(datas)+"}"
      inparams=",".join(params)

      params=[]
      datas=[]
      for name,typ in s.outport:
        params.append(name)
        if typ == "pyobj":
          datas.append('cPickle.dumps(j.g_context["%s"],-1)'%name)
        else:
          datas.append('j.g_context["%s"]'%name)
      outparams=",".join(params)
      rvars=",".join(datas)

      service=asterCEXEService.substitute(component=self.name,service=s.name,inparams=inparams,
                                    outparams=outparams,body=s.body,dvars=dvars,rvars=rvars)
      streams=[]
      for name,typ,dep in s.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name,typ,dep))
      instream="\n".join(streams)
      streams=[]
      for name,typ,dep in s.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name,typ,dep))
      outstream="\n".join(streams)

      init=pyinitCEXEService.substitute(component=self.name,service=s.name,
                                    instream=instream,outstream=outstream)
      services.append(service)
      inits.append(init)
    return asterCEXECompo.substitute(component=self.name,module=gen.module.name,
                              servicesdef="\n".join(defs),servicesimpl="\n".join(services),initservice='\n'.join(inits),
                              aster_dir=self.aster_dir)
  def getImpl(self):
    if self.kind=="cexe":
      return "CEXE",os.path.join(self.exe_path,self.name+".exe")
    else:
      return "SO",""

class F77Component(Component):
  def __init__(self,name,services=None,libs="",rlibs="",kind="lib",exe_path=None):
    self.exe_path=exe_path
    Component.__init__(self,name,services,impl="F77",libs=libs,rlibs=rlibs,kind=kind)

  def validate(self):
    Component.validate(self)
    kinds=("lib","exe")
    if self.kind not in kinds:
        raise Invalid("kind must be one of %s" % kinds)

    if self.kind == "exe" :
        if not self.exe_path:
          raise Invalid("exe_path must be defined for component %s" % self.name)

    for s in self.services:
      #defs generation
      params=["void *compo"]
      strparams=[]
      for name,typ in s.inport:
        if typ == "string":
          params.append("const STR_PSTR(%s)"%name)
          strparams.append("STR_PLEN(%s)"%name)
        else:
          params.append("%s %s" % (f77Types[typ],name))
      for name,typ in s.outport:
        if typ == "string":
          params.append("const STR_PSTR(%s)"%name)
          strparams.append("STR_PLEN(%s)"%name)
        else:
          params.append("%s %s" % (f77Types[typ],name))
      args=','.join(params)+" " + " ".join(strparams)
      s.defs=s.defs+'\nextern "C" void F_FUNC(%s,%s)(%s);' % (s.name.lower(),s.name.upper(),args)

      #body generation
      params=["&component"]
      strparams=[]
      strallocs=[]
      #length allocated for out string
      lstr=20
      for name,typ in s.inport:
        if typ == "string":
          params.append("STR_CPTR(%s)" % name)
          strparams.append("STR_CLEN(%s)"%name)
        else:
          params.append("&%s" % name)
      for name,typ in s.outport:
        if typ == "string":
          params.append("STR_CPTR(%s.ptr())" % name)
          strparams.append("STR_CLEN(%s.ptr())"%name)
          strallocs.append('%s=CORBA::string_dup("%s");' %(name," "*lstr))
        else:
          params.append("&%s" % name)
      s.body='\n'.join(strallocs)+'\n'+s.body
      args=','.join(params)+" " + " ".join(strparams)
      s.body=s.body+"\n   F_CALL(%s,%s)(%s);" % (s.name.lower(),s.name.upper(),args)

  def makeCompo(self,gen):
    cxxFile="%s.cxx" % self.name
    hxxFile="%s.hxx" % self.name
    if self.kind=="lib":
      return {"Makefile.am":compoMakefile.substitute(module=gen.module.name,component=self.name,
                                                   libs=self.libs,rlibs=self.rlibs,
                                                   includes=self.includes),
              cxxFile:gen.makeCXX(self),hxxFile:gen.makeHXX(self)}
    if self.kind=="exe":
      return {"Makefile.am":compoEXEMakefile.substitute(module=gen.module.name,component=self.name,
                                                   libs=self.libs,rlibs=self.rlibs,
                                                   includes=self.includes),
              self.name+".exe":exeCPP.substitute(compoexe=self.exe_path),
              cxxFile:gen.makeCXX(self,1),hxxFile:gen.makeHXX(self)}

class Service(object):
  def __init__(self,name,inport=None,outport=None,instream=None,outstream=None,body="",defs=""):
    self.name=name
    self.inport=inport or []
    self.outport=outport or []
    self.instream=instream or []
    self.outstream=outstream or []
    self.defs=defs
    self.body=body

  def validate(self):
    l=set()
    for p in self.inport:
      name,typ=self.validatePort(p)
      if name in l:
        raise Invalid("%s is already defined as a service parameter" % name)
      l.add(name)

    for p in self.outport:
      name,typ=self.validatePort(p)
      if name in l:
        raise Invalid("%s is already defined as a service parameter" % name)
      l.add(name)

    l=set()
    for p in self.instream:
      name,typ,dep=self.validateStream(p)
      if name in l:
        raise Invalid("%s is already defined as a stream port" % name)
      l.add(name)

    for p in self.outstream:
      name,typ,dep=self.validateStream(p)
      if name in l:
        raise Invalid("%s is already defined as a stream port" % name)
      l.add(name)

  def validatePort(self,p):
    try:
      name,typ=p
    except:
      raise Invalid("%s is not a valid definition of an data port (name,type)" % (p,))

    if self.impl in ("PY","ASTER"):
      validtypes=PyValidTypes
    else:
      validtypes=ValidTypes

    if typ not in validtypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ,validtypes))
    return name,typ

  def validateStream(self,p):
    try:
      name,typ,dep=p
    except:
      raise Invalid("%s is not a valid definition of a stream port (name,type,dependency)" % (p,))
    if typ not in ValidStreamTypes:
      raise Invalid("%s is not a valid type. It should be one of %s" % (typ,ValidStreamTypes))
    if dep not in ValidDependencies:
      raise Invalid("%s is not a valid dependency. It should be one of %s" % (dep,ValidDependencies))
    return name,typ,dep

class Generator(object):
  def __init__(self,module,context=None):
    self.module=module
    self.context=context or {}
    self.kernel=self.context["kernel"]
    self.aster=""

  def generate(self):
    module=self.module
    namedir=module.name+"_SRC"
    force=self.context.get("force")
    update=self.context.get("update")
    if os.path.exists(namedir):
      if force:
        shutil.rmtree(namedir)
      elif not update:
        raise Invalid("The directory %s already exists" % namedir)
    if update:
      makedirs(namedir)
    else:
      os.makedirs(namedir)

    srcs={}
    makefile="SUBDIRS="
    makefiles=[]
    for c in module.components:
      makefile=makefile+" "+c.name
      srcs[c.name]=c.makeCompo(self)
      makefiles.append("     src/"+c.name+"/Makefile")

    srcs["Makefile.am"]=makefile+'\n'
    idlFile="%s.idl" % module.name
    catalogFile="%sCatalog.xml" % module.name

    self.makeFiles({"autogen.sh":autogen,
                    "Makefile.am":mainMakefile,
                    "README":"","NEWS":"","AUTHORS":"","ChangeLog":"",
                    "configure.ac":configure.substitute(module=module.name.lower(),makefiles='\n'.join(makefiles)),
                    "idl":{"Makefile.am":idlMakefile.substitute(module=module.name),idlFile:self.makeIdl()},
                    "src":srcs,
                    "resources":{"Makefile.am":resMakefile.substitute(module=module.name),catalogFile:self.makeCatalog()},
                    "adm_local":{"make_common_starter.am":makecommon,"check_aster.m4":check_aster},
                    }, namedir)
    os.chmod(os.path.join(namedir,"autogen.sh"),0777)

    for m4file in ("check_Kernel.m4","check_omniorb.m4","ac_linker_options.m4","ac_cxx_option.m4",
                   "python.m4","enable_pthreads.m4","check_f77.m4","acx_pthread.m4","check_boost.m4"):
      shutil.copyfile(os.path.join(self.kernel,"salome_adm","unix","config_files",m4file),os.path.join(namedir,"adm_local",m4file))

    return

  def makePY(self,component):
    services=[]
    inits=[]
    defs=[]
    for s in component.services:
      defs.append(s.defs)
      params=[]
      pyparams=[]
      for name,typ in s.inport:
        params.append(name)
        if typ=="pyobj":
          pyparams.append("      %s=cPickle.loads(%s)" %(name,name))
      inparams=",".join(params)
      convertinparams='\n'.join(pyparams)

      params=[]
      pyparams=[]
      for name,typ in s.outport:
        params.append(name)
        if typ=="pyobj":
          pyparams.append("      %s=cPickle.dumps(%s,-1)" %(name,name))
      outparams=",".join(params)
      convertoutparams='\n'.join(pyparams)
      service=pyService.substitute(component=component.name,service=s.name,inparams=inparams,
                                    outparams=outparams,body=s.body,convertinparams=convertinparams,
                                    convertoutparams=convertoutparams)
      streams=[]
      for name,typ,dep in s.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name,typ,dep))
      instream="\n".join(streams)
      streams=[]
      for name,typ,dep in s.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name,typ,dep))
      outstream="\n".join(streams)

      init=pyinitService.substitute(component=component.name,service=s.name,
                                    instream=instream,outstream=outstream)
      services.append(service)
      inits.append(init)

    python_path=",".join([repr(p) for p in component.python_path])
    return pyCompo.substitute(component=component.name,module=self.module.name,
                              servicesdef="\n".join(defs),servicesimpl="\n".join(services),initservice='\n'.join(inits),
                              python_path=python_path)

  def makeASTER(self,component):
    services=[]
    inits=[]
    defs=[]
    for s in component.services:
      defs.append(s.defs)
      params=[]
      datas=[]
      for name,typ in s.inport:
        params.append(name)
        if typ == "pyobj":
          datas.append('"%s":cPickle.loads(%s)' % (name,name))
        else:
          datas.append('"%s":%s' % (name,name))
      #ajout de l'adresse du composant
      datas.append('"component":self.proxy.ptr()')
      dvars="{"+','.join(datas)+"}"
      inparams=",".join(params)

      params=[]
      datas=[]
      for name,typ in s.outport:
        params.append(name)
        if typ == "pyobj":
          datas.append('cPickle.dumps(j.g_context["%s"],-1)'%name)
        else:
          datas.append('j.g_context["%s"]'%name)
      outparams=",".join(params)
      rvars=",".join(datas)

      service=asterService.substitute(component=component.name,service=s.name,inparams=inparams,
                                    outparams=outparams,body=s.body,dvars=dvars,rvars=rvars)
      streams=[]
      for name,typ,dep in s.instream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","IN","%s")'% (name,typ,dep))
      instream="\n".join(streams)
      streams=[]
      for name,typ,dep in s.outstream:
        streams.append('       calcium.create_calcium_port(self.proxy,"%s","%s","OUT","%s")'% (name,typ,dep))
      outstream="\n".join(streams)

      init=pyinitService.substitute(component=component.name,service=s.name,
                                    instream=instream,outstream=outstream)
      services.append(service)
      inits.append(init)
    python_path=",".join([repr(p) for p in component.python_path])
    argv=",".join([repr(p) for p in component.argv])
    return asterCompo.substitute(component=component.name,module=self.module.name,
                              servicesdef="\n".join(defs),servicesimpl="\n".join(services),initservice='\n'.join(inits),
                              aster_dir=component.aster_dir,python_path=python_path,argv=argv)

  def makeArgs(self,service):
    params=[]
    for name,typ in service.inport:
      params.append("%s %s" % (corba_in_type(typ,self.module.name),name))
    for name,typ in service.outport:
      params.append("%s %s" % (corba_out_type(typ,self.module.name),name))
    return ",".join(params)

  def makeHXX(self,component):
    services=[]
    for s in component.services:
      service="    void %s(" % s.name
      service=service+self.makeArgs(s)+");"
      services.append(service)
    servicesdef="\n".join(services)
    return hxxCompo.substitute(component=component.name,module=self.module.name,servicesdef=servicesdef)

  def makeCXX(self,component,exe=0):
    services=[]
    inits=[]
    defs=[]
    for s in component.services:
      defs.append(s.defs)
      service=cxxService.substitute(component=component.name,service=s.name,parameters=self.makeArgs(s),
                                    body=s.body,exe=exe)
      streams=[]
      for name,typ,dep in s.instream:
        streams.append('          create_calcium_port(this,"%s","%s","IN","%s");'% (name,typ,dep))
      instream="\n".join(streams)
      streams=[]
      for name,typ,dep in s.outstream:
        streams.append('          create_calcium_port(this,"%s","%s","OUT","%s");'% (name,typ,dep))
      outstream="\n".join(streams)

      init=initService.substitute(component=component.name,service=s.name,
                                  instream=instream,outstream=outstream)
      services.append(service)
      inits.append(init)
    return cxxCompo.substitute(component=component.name,module=self.module.name,exe=exe,exe_path=component.exe_path,
                               servicesdef="\n".join(defs),servicesimpl="\n".join(services),initservice='\n'.join(inits))

  def makeCatalog(self):
    components=[]
    for c in self.module.components:
      services=[]
      for s in c.services:
        params=[]
        for name,typ in s.inport:
          params.append(cataInparam.substitute(name=name,type=typ))
        inparams="\n".join(params)
        params=[]
        for name,typ in s.outport:
          params.append(cataOutparam.substitute(name=name,type=typ))
        outparams="\n".join(params)
        streams=[]
        for name,typ,dep in s.instream:
          streams.append(cataInStream.substitute(name=name,type=calciumTypes[typ],dep=dep))
        for name,typ,dep in s.outstream:
          streams.append(cataOutStream.substitute(name=name,type=calciumTypes[typ],dep=dep))
        datastreams="\n".join(streams)
        services.append(cataService.substitute(service=s.name,author="EDF-RD",
                                               inparams=inparams,outparams=outparams,datastreams=datastreams))
      impltype,implname=c.getImpl()
      components.append(cataCompo.substitute(component=c.name,author="EDF-RD",impltype=impltype,implname=implname,
                                             services='\n'.join(services)))
    return catalog.substitute(components='\n'.join(components))

  def makeIdl(self):
    interfaces=[]
    for c in self.module.components:
      services=[]
      for s in c.services:
        params=[]
        for name,typ in s.inport:
          if c.impl in ("PY","ASTER") and typ=="pyobj":
            typ="Engines::fileBlock"
          params.append("in %s %s" % (typ,name))
        for name,typ in s.outport:
          if c.impl in ("PY","ASTER") and typ=="pyobj":
            typ="Engines::fileBlock"
          params.append("out %s %s" % (typ,name))
        service="    void %s(" % s.name
        service=service+",".join(params)+") raises (SALOME::SALOME_Exception);"
        services.append(service)
      interfaces.append(interface.substitute(component=c.name,services="\n".join(services)))
    return idl.substitute(module=self.module.name,interfaces='\n'.join(interfaces))

  def makeFiles(self,d,basedir):
    for name,content in d.items():
      file=os.path.join(basedir,name)
      if isinstance(content,str):
        f= open(file, 'w')
        f.write(content)
        f.close()
      else:
        if not os.path.exists(file):
          os.makedirs(file)
        self.makeFiles(content,file)

  def bootstrap(self):
    ier=os.system("cd %s_SRC;sh autogen.sh" % self.module.name)
    if ier != 0:
      raise Invalid("bootstrap has ended in error")

  def configure(self):
    prefix=self.module.prefix
    if prefix:
      prefix=os.path.abspath(prefix)
      cmd="cd %s_SRC;./configure --with-kernel=%s --with-aster=%s --prefix=%s"
      ier=os.system(cmd % (self.module.name,self.kernel,self.aster,prefix))
    else:
      cmd="cd %s_SRC;./configure --with-kernel=%s --with-aster=%s"
      ier=os.system(cmd % (self.module.name,self.kernel,self.aster))
    if ier != 0:
      raise Invalid("configure has ended in error")

  def make(self):
    ier=os.system("cd %s_SRC;make" % self.module.name)
    if ier != 0:
      raise Invalid("make has ended in error")

  def install(self):
    ier=os.system("cd %s_SRC;make install" % self.module.name)
    if ier != 0:
      raise Invalid("install has ended in error")

  def make_appli(self,appliname,restrict=None,altmodules=None):
    makedirs(appliname)

    d,f=os.path.split(self.kernel)

    #collect modules besides KERNEL module with the same suffix if any
    modules_dict={}
    if f[:6] == "KERNEL":
      suffix=f[6:]
      for dd in os.listdir(d):
        if dd[-len(suffix):] == suffix:
          module=dd[:-len(suffix)]
          path=os.path.join(d,dd)
          #try to find catalog files
          l=glob.glob(os.path.join(path,"share","salome","resources","*","*Catalog.xml"))
          if not l:
            #catalogs have not been found : try the upper level
            l=glob.glob(os.path.join(path,"share","salome","resources","*Catalog.xml"))
          if l:
            #catalogs have been found : add the corresponding entries in the application
            for e in l:
              b,c=os.path.split(e)
              name=c[:-11]
              modules_dict[name]='  <module name="%s" path="%s"/>' % (name,path)
          else:
            modules_dict[module]='  <module name="%s" path="%s"/>' % (module,path)

    modules_dict["KERNEL"]='  <module name="KERNEL" path="%s"/>' % self.kernel

    #keep only the modules which names are in restrict if given
    modules=[]
    if restrict:
      for m in restrict:
        if modules_dict.has_key(m):
          modules.append(modules_dict[m])
    else:
      modules=modules_dict.values()

    #add the alternate modules if given
    if altmodules:
      for module,path in altmodules.items():
        modules.append('  <module name="%s" path="%s"/>' % (module,path))

    #add the generated module
    modules.append('  <module name="%s" path="%s"/>' % (self.module.name,os.path.abspath(self.module.prefix)))

    #try to find a prerequisites file
    prerequisites=self.context.get("prerequisites")
    if not prerequisites:
      #try to find one in d
      prerequisites=os.path.join(d,"profile%s.sh" % suffix)
    if not os.path.exists(prerequisites):
      raise Invalid("Can not create an application : prerequisites file not defined or does not exist")

    #create config_appli.xml file
    appli=application.substitute(prerequisites=prerequisites,modules="\n".join(modules))
    fil=open(os.path.join(appliname,"config_appli.xml"),'w')
    fil.write(appli)
    fil.close()

    #execute appli_gen.py script
    appligen=os.path.join(self.kernel,"bin","salome","appli_gen.py")
    ier=os.system("cd %s;%s" % (appliname,appligen))
    if ier != 0:
      raise Invalid("make_appli has ended in error")

    #add CatalogResources.xml if not created by appli_gen.py
    if not os.path.exists(os.path.join(appliname,"CatalogResources.xml")):
      #CatalogResources.xml does not exist create a minimal one
      f =open(os.path.join(appliname,'CatalogResources.xml'),'w')
      command="""<!DOCTYPE ResourcesCatalog>
<resources>
    <machine hostname="%s" protocol="ssh" mode="interactive" />
</resources>
"""
      host=socket.gethostname().split('.')[0]
      f.write(command % host)
      f.close()


application="""
<application>
<prerequisites path="${prerequisites}"/>
<modules>
${modules}
</modules>
</application>
"""
application=Template(application)

autogen="""#!/bin/sh

rm -rf autom4te.cache
rm -f aclocal.m4 adm_local/ltmain.sh

echo "Running aclocal..."    ;
aclocal --force -I adm_local || exit 1
echo "Running autoheader..." ; autoheader --force -I adm_local            || exit 1
echo "Running autoconf..."   ; autoconf --force                    || exit 1
echo "Running libtoolize..." ; libtoolize --copy --force           || exit 1
echo "Running automake..."   ; automake --add-missing --copy       || exit 1
"""
mainMakefile="""include $(top_srcdir)/adm_local/make_common_starter.am
SUBDIRS = idl resources src
ACLOCAL_AMFLAGS = -I adm_local
"""

configure="""
AC_INIT(salome,4.1)
AC_CONFIG_AUX_DIR(adm_local)
AM_INIT_AUTOMAKE
AM_CONFIG_HEADER(${module}_config.h)

dnl Check Salome Install
CHECK_KERNEL
if test "x$$Kernel_ok" = "xno"; then
  AC_MSG_ERROR([You must define a correct KERNEL_ROOT_DIR or use the --with-kernel= configure option !])
fi

AC_PROG_LIBTOOL
AC_PROG_CC
AC_PROG_CXX
CHECK_F77
CHECK_BOOST
CHECK_OMNIORB

MODULE_NAME=${module}
AC_SUBST(MODULE_NAME)

AC_CHECK_ASTER

echo
echo
echo
echo "------------------------------------------------------------------------"
echo "$$PACKAGE $$VERSION"
echo "------------------------------------------------------------------------"
echo
echo "Configuration Options Summary:"
echo
echo "Mandatory products:"
echo "  Threads ................ : $$threads_ok"
echo "  OmniOrb (CORBA) ........ : $$omniORB_ok"
echo "  OmniOrbpy (CORBA) ...... : $$omniORBpy_ok"
echo "  Python ................. : $$python_ok"
echo "  Boost  ................. : $$boost_ok"
echo "  SALOME KERNEL .......... : $$Kernel_ok"
echo "  Code Aster ............. : $$Aster_ok"
echo
echo "------------------------------------------------------------------------"
echo

if test "x$$threads_ok" = "xno"; then
  AC_MSG_ERROR([Thread is required],1)
fi
if test "x$$python_ok" = "xno"; then
  AC_MSG_ERROR([Python is required],1)
fi
if test "x$$omniORB_ok" = "xno"; then
  AC_MSG_ERROR([OmniOrb is required],1)
fi
if test "x$$omniORBpy_ok" = "xno"; then
  AC_MSG_ERROR([OmniOrbpy is required],1)
fi
if test "x$$Kernel_ok" = "xno"; then
  AC_MSG_ERROR([Expat is required],1)
fi

AC_CONFIG_FILES([
        Makefile
        idl/Makefile
        resources/Makefile
        src/Makefile
${makefiles}
        ])
AC_OUTPUT
"""
configure=Template(configure)

makecommon="""
# Standard directory for installation
salomeincludedir   = $(includedir)/salome
libdir             = $(prefix)/lib/salome
bindir             = $(prefix)/bin/salome
salomescriptdir    = $(bindir)
salomepythondir    = $(prefix)/lib/python$(PYTHON_VERSION)/site-packages/salome

# Directory for installing idl files
salomeidldir       = $(prefix)/idl/salome

# Directory for installing resource files
salomeresdir       = $(prefix)/share/salome/resources/${MODULE_NAME}

# Directories for installing admin files
admlocaldir       = $(prefix)/adm_local
admlocalunixdir     = $(admlocaldir)/unix
admlocalm4dir        = $(admlocaldir)/unix/config_files

# Shared modules installation directory
sharedpkgpythondir =$(pkgpythondir)/shared_modules

# Documentation directory
docdir             = $(datadir)/doc/salome

IDL_INCLUDES = -I$(KERNEL_ROOT_DIR)/idl/salome
KERNEL_LIBS= -L$(KERNEL_ROOT_DIR)/lib/salome -lSalomeContainer -lOpUtil -lSalomeDSCContainer -lSalomeDSCSuperv -lSalomeDatastream -lSalomeDSCSupervBasic -lCalciumC
KERNEL_INCLUDES= -I$(KERNEL_ROOT_DIR)/include/salome $(OMNIORB_INCLUDES) $(BOOST_CPPFLAGS)

"""

idlMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am

BUILT_SOURCES = ${module}SK.cc
IDL_FILES=${module}.idl

lib_LTLIBRARIES = lib${module}.la
salomeidl_DATA = $$(IDL_FILES)
salomepython_DATA = ${module}_idl.py
lib${module}_la_SOURCES      =
nodist_lib${module}_la_SOURCES = ${module}SK.cc
nodist_salomeinclude_HEADERS= ${module}.hh
lib${module}_la_CXXFLAGS     = -I.  $$(KERNEL_INCLUDES)
lib${module}_la_LIBADD     = $$(KERNEL_LIBS)
##########################################################
%SK.cc %.hh : %.idl
\t$$(OMNIORB_IDL) -bcxx $$(IDLCXXFLAGS) $$(OMNIORB_IDLCXXFLAGS) $$(IDL_INCLUDES) $$<
%_idl.py : %.idl
\t$$(OMNIORB_IDL) -bpython $$(IDL_INCLUDES) $$<

CLEANFILES = *.hh *SK.cc *.py

clean-local:
\trm -rf ${module} ${module}__POA

install-data-local:
\t$${mkinstalldirs} $$(DESTDIR)$$(salomepythondir)
\tcp -R ${module} ${module}__POA $$(DESTDIR)$$(salomepythondir)

uninstall-local:
\trm -rf $$(DESTDIR)$$(salomepythondir)/${module}
\trm -rf $$(DESTDIR)$$(salomepythondir)/${module}__POA
"""
idlMakefile=Template(idlMakefile)
resMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am
DATA_INST = ${module}Catalog.xml
salomeres_DATA = $${DATA_INST}
EXTRA_DIST = $${DATA_INST}
"""
resMakefile=Template(resMakefile)
compoMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am

AM_CFLAGS=$$(KERNEL_INCLUDES) -fexceptions

lib_LTLIBRARIES = lib${component}Engine.la
lib${component}Engine_la_SOURCES      = ${component}.cxx 
nodist_lib${component}Engine_la_SOURCES =
lib${component}Engine_la_CXXFLAGS = -I$$(top_builddir)/idl  $$(KERNEL_INCLUDES) ${includes}
lib${component}Engine_la_FFLAGS = $$(KERNEL_INCLUDES) -fexceptions ${includes}
lib${component}Engine_la_LIBADD   = -L$$(top_builddir)/idl -l${module} $$(FLIBS) ${libs}
lib${component}Engine_la_LDFLAGS = ${rlibs}
salomeinclude_HEADERS = ${component}.hxx
"""
compoMakefile=Template(compoMakefile)
compoEXEMakefile="""
include $$(top_srcdir)/adm_local/make_common_starter.am

AM_CFLAGS=$$(KERNEL_INCLUDES) -fexceptions

lib_LTLIBRARIES = lib${component}Exelib.la
lib${component}Exelib_la_SOURCES      = ${component}.cxx 
nodist_lib${component}Exelib_la_SOURCES =
lib${component}Exelib_la_CXXFLAGS = -I$$(top_builddir)/idl  $$(KERNEL_INCLUDES) ${includes}
lib${component}Exelib_la_FFLAGS = $$(KERNEL_INCLUDES) -fexceptions ${includes}
lib${component}Exelib_la_LIBADD   = -L$$(top_builddir)/idl -l${module} $$(FLIBS) ${libs}
lib${component}Exelib_la_LDFLAGS = ${rlibs}
salomeinclude_HEADERS = ${component}.hxx
# These files are executable scripts
dist_salomescript_SCRIPTS= ${component}.exe
"""
compoEXEMakefile=Template(compoEXEMakefile)

pycompoMakefile="""include $$(top_srcdir)/adm_local/make_common_starter.am
salomepython_PYTHON = ${component}.py
"""
pycompoMakefile=Template(pycompoMakefile)

pycompoEXEMakefile="""include $$(top_srcdir)/adm_local/make_common_starter.am
dist_salomescript_SCRIPTS= ${component}.exe
"""
pycompoEXEMakefile=Template(pycompoEXEMakefile)

idl="""
#ifndef _${module}_IDL_
#define _${module}_IDL_

#include "DSC_Engines.idl"
#include "SALOME_Exception.idl"

module ${module} 
{
typedef sequence<string> stringvec;
typedef sequence<double> dblevec;
typedef sequence<long> intvec;

${interfaces}
};

#endif 
"""
idl=Template(idl)
interface="""
  interface ${component}:Engines::Superv_Component
  {
${services}
  };
"""
interface=Template(interface)
catalog="""<?xml version='1.0' encoding='us-ascii' ?>

<!-- XML component catalog -->
<begin-catalog>

<!-- Path prefix information -->

<path-prefix-list>
</path-prefix-list>

<!-- Commonly used types  -->
<type-list>
  <objref name="pyobj" id="python:obj:1.0"/>
</type-list>

<!-- Component list -->
<component-list>
${components}
</component-list>
</begin-catalog>
"""
catalog=Template(catalog)

cxxCompo="""
#include "${component}.hxx"
#include <string>
#include <unistd.h>

#include <Calcium.hxx>
#include <calcium.h>
#include <signal.h>
#include <SALOME_NamingService.hxx>
#include <Utils_SALOME_Exception.hxx>

typedef void (*sighandler_t)(int);
sighandler_t setsig(int sig, sighandler_t handler)
{
  struct sigaction context, ocontext;
  context.sa_handler = handler;
  sigemptyset(&context.sa_mask);
  context.sa_flags = 0;
  if (sigaction(sig, &context, &ocontext) == -1)
    return SIG_ERR;
  return ocontext.sa_handler;
}

static void AttachDebugger()
{
  if(getenv ("DEBUGGER"))
    {
      std::stringstream exec;
#if ${exe}
      exec << "$$DEBUGGER " << "${exe_path} " << getpid() << "&";
#else
      exec << "$$DEBUGGER SALOME_Container " << getpid() << "&";
#endif
      std::cerr << exec.str() << std::endl;
      system(exec.str().c_str());
      while(1);
    }
}

static void THandler(int theSigId)
{
  std::cerr << "SIGSEGV: "  << std::endl;
  AttachDebugger();
  //to exit or not to exit
  _exit(1);
}

static void terminateHandler(void)
{
  std::cerr << "Terminate: not managed exception !"  << std::endl;
  AttachDebugger();
  throw SALOME_Exception("Terminate: not managed exception !");
}

static void unexpectedHandler(void)
{
  std::cerr << "Unexpected: unexpected exception !"  << std::endl;
  AttachDebugger();
  throw SALOME_Exception("Unexpected: unexpected exception !");
}


#define  _(A,B)   A##B
#ifdef _WIN32
#define F_FUNC(lname,uname) __stdcall uname
#define F_CALL(lname,uname) uname
#define STR_PSTR(str)       char *str, int _(Len,str)
#define STR_PLEN(str)
#define STR_PTR(str)        str
#define STR_LEN(str)        _(Len,str)
#define STR_CPTR(str)        str,strlen(str)
#define STR_CLEN(str)
#else
#define F_FUNC(lname,uname) _(lname,_)        /* Fortran function name */
#define F_CALL(lname,uname) _(lname,_)        /* Fortran function call */
#define STR_PSTR(str)       char *str         /* fortran string arg pointer */
#define STR_PLEN(str)       , int _(Len,str)  /* fortran string arg length */
#define STR_PTR(str)        str               /* fortran string pointer */
#define STR_LEN(str)        _(Len,str)        /* fortran string length */
#define STR_CPTR(str)        str              /* fortran string calling arg pointer */
#define STR_CLEN(str)       , strlen(str)     /* fortran string calling arg length */
#endif

//DEFS
${servicesdef}
//ENDDEF

extern "C" void cp_exit(int err);

extern "C" void F_FUNC(cpexit,CPEXIT)(int err)
{
  if(err==-1)
    _exit(-1);
  else
    cp_exit(err);
}

using namespace std;

//! Constructor for component "${component}" instance
/*!
 *
 */
${component}_i::${component}_i(CORBA::ORB_ptr orb,
                     PortableServer::POA_ptr poa,
                     PortableServer::ObjectId * contId,
                     const char *instanceName,
                     const char *interfaceName)
          : Superv_Component_i(orb, poa, contId, instanceName, interfaceName)
{
  std::cerr << "create component" << std::endl;
#if ${exe}
  setsig(SIGSEGV,&THandler);
  set_terminate(&terminateHandler);
  set_unexpected(&unexpectedHandler);
#endif
  _thisObj = this ;
  _id = _poa->activate_object(_thisObj);
}

${component}_i::${component}_i(CORBA::ORB_ptr orb,
                     PortableServer::POA_ptr poa,
                     Engines::Container_ptr container,
                     const char *instanceName,
                     const char *interfaceName)
          : Superv_Component_i(orb, poa, container, instanceName, interfaceName)
{
#if ${exe}
  setsig(SIGSEGV,&THandler);
  set_terminate(&terminateHandler);
  set_unexpected(&unexpectedHandler);
#endif
  _thisObj = this ;
  _id = _poa->activate_object(_thisObj);
}

//! Destructor for component "${component}" instance
${component}_i::~${component}_i()
{
}

void ${component}_i::destroy()
{
  Engines_Component_i::destroy();
#if ${exe}
  if(!CORBA::is_nil(_orb))
    _orb->shutdown(0);
#endif
}

//! Register datastream ports for a component service given its name
/*!
 *  \param service_name : service name
 *  \\return true if port registering succeeded, false if not
 */
CORBA::Boolean
${component}_i::init_service(const char * service_name) {
  CORBA::Boolean rtn = false;
  string s_name(service_name);
${initservice}
  return rtn;
}

${servicesimpl}

extern "C"
{
  PortableServer::ObjectId * ${component}Engine_factory( CORBA::ORB_ptr orb,
                                                    PortableServer::POA_ptr poa,
                                                    PortableServer::ObjectId * contId,
                                                    const char *instanceName,
                                                    const char *interfaceName)
  {
    MESSAGE("PortableServer::ObjectId * ${component}Engine_factory()");
    ${component}_i * myEngine = new ${component}_i(orb, poa, contId, instanceName, interfaceName);
    return myEngine->getId() ;
  }
  void yacsinit()
  {
    int argc=0;
    char *argv=0;
    CORBA::ORB_var orb = CORBA::ORB_init( argc , &argv ) ;
    PortableServer::POAManager_var pman;
    CORBA::Object_var obj;
    try
      {
        SALOME_NamingService * salomens = new SALOME_NamingService(orb);
        obj = orb->resolve_initial_references("RootPOA");
        PortableServer::POA_var  poa = PortableServer::POA::_narrow(obj);
        PortableServer::POAManager_var pman = poa->the_POAManager();
        std::string containerName(getenv("SALOME_CONTAINERNAME"));
        std::string instanceName(getenv("SALOME_INSTANCE"));
        obj=orb->string_to_object(getenv("SALOME_CONTAINER"));
        Engines::Container_var container = Engines::Container::_narrow(obj);
        ${component}_i * myEngine = new ${component}_i(orb, poa, container, instanceName.c_str(), "${component}");
        pman->activate();
        obj=myEngine->_this();
        Engines::Component_var component = Engines::Component::_narrow(obj);
        string component_registerName = containerName + "/" + instanceName;
        salomens->Register(component,component_registerName.c_str());
        orb->run();
        orb->destroy();
      }
    catch(CORBA::Exception&)
      {
        std::cerr << "Caught CORBA::Exception."<< std::endl;
      }
    catch(std::exception& exc)
      {
        std::cerr << "Caught std::exception - "<<exc.what() << std::endl;
      }
    catch(...)
      {
        std::cerr << "Caught unknown exception." << std::endl;
      }
  }

  void F_FUNC(yacsinit,YACSINIT)()
  {
    yacsinit();
  }
}
"""
cxxCompo=Template(cxxCompo)

hxxCompo="""
#ifndef _${component}_HXX_
#define _${component}_HXX_

#include "Superv_Component_i.hxx"
#include "${module}.hh"

class ${component}_i:
  public virtual POA_${module}::${component},
  public virtual Superv_Component_i
{
  public:
    ${component}_i(CORBA::ORB_ptr orb, PortableServer::POA_ptr poa,
              PortableServer::ObjectId * contId,
              const char *instanceName, const char *interfaceName);
    ${component}_i(CORBA::ORB_ptr orb, PortableServer::POA_ptr poa,
              Engines::Container_ptr container,
              const char *instanceName, const char *interfaceName);
    virtual ~${component}_i();
    void destroy();
    CORBA::Boolean init_service(const char * service_name);
${servicesdef}
};

extern "C"
{
    PortableServer::ObjectId * ${component}Engine_factory( CORBA::ORB_ptr orb,
                                                      PortableServer::POA_ptr poa,
                                                      PortableServer::ObjectId * contId,
                                                      const char *instanceName,
                                                      const char *interfaceName);
    void yacsinit();
}
#endif

"""
hxxCompo=Template(hxxCompo)

cxxService="""
void ${component}_i::${service}(${parameters})
{
  std::cerr << "${component}_i::${service}" << std::endl;
  beginService("${component}_i::${service}");
  Superv_Component_i * component = dynamic_cast<Superv_Component_i*>(this);
  char       nom_instance[INSTANCE_LEN];
  int info = cp_cd(component,nom_instance);
  try
    {
//BODY
${body}
//ENDBODY
      cp_fin(component,CP_ARRET);
    }
  catch ( const CalciumException & ex)
    {
      std::cerr << ex.what() << std::endl;
      cp_fin(component,CP_ARRET);
      SALOME::ExceptionStruct es;
      es.text=CORBA::string_dup(ex.what());
      es.type=SALOME::INTERNAL_ERROR;
      throw SALOME::SALOME_Exception(es);
    }
  catch ( const SALOME_Exception & ex)
    {
      cp_fin(component,CP_ARRET);
      SALOME::ExceptionStruct es;
      es.text=CORBA::string_dup(ex.what());
      es.type=SALOME::INTERNAL_ERROR;
      throw SALOME::SALOME_Exception(es);
    }
  catch ( const SALOME::SALOME_Exception & ex)
    {
      cp_fin(component,CP_ARRET);
      throw;
    }
  catch (...)
    {
      std::cerr << "unknown exception" << std::endl;
#if ${exe}
      _exit(-1);
#endif
      cp_fin(component,CP_ARRET);
      SALOME::ExceptionStruct es;
      es.text=CORBA::string_dup(" unknown exception");
      es.type=SALOME::INTERNAL_ERROR;
      throw SALOME::SALOME_Exception(es);
    }
  endService("${component}_i::${service}");
  std::cerr << "end of ${component}_i::${service}" << std::endl;
}

"""
cxxService=Template(cxxService)

initService="""
  if (s_name == "${service}")
    {
      try
        {
          //initialization CALCIUM ports IN
${instream}
          //initialization CALCIUM ports OUT
${outstream}
        }
      catch(const PortAlreadyDefined& ex)
        {
          std::cerr << "${component}: " << ex.what() << std::endl;
          //Ports already created : we use them
        }
      catch ( ... )
        {
          std::cerr << "${component}: unknown exception" << std::endl;
        }
      rtn = true;
    }
"""
initService=Template(initService)

pyCompo="""
import sys,traceback,os
sys.path=sys.path+[${python_path}]
import ${module}__POA
import calcium
import dsccalcium
import SALOME
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
    print "${component}.__init__: ", containerName, ';', instanceName,interfaceName
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
    print "${component}.${service}"
    self.beginService("${component}.${service}")
    component=self.proxy
    returns=None
    try:
${convertinparams}
#BODY
${body}
#ENDBODY
      print "End of ${component}.${service}"
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

cataCompo="""
  <component>
        <!-- Component identification -->
        <component-name>${component}</component-name>
        <component-username>${component}</component-username>
        <component-type>Data</component-type>
        <component-author>${author}</component-author>
        <component-version>1.0</component-version>
        <component-comment></component-comment>
        <component-multistudy>0</component-multistudy>
        <component-impltype>${impltype}</component-impltype>
        <component-implname>${implname}</component-implname>
        <component-interface-list>
            <component-interface-name>${component}</component-interface-name>
            <component-interface-comment></component-interface-comment>
            <component-service-list>
${services}
            </component-service-list>
        </component-interface-list>
  </component>"""
cataCompo=Template(cataCompo)
cataService="""                <component-service>
                    <!-- service-identification -->
                    <service-name>${service}</service-name>
                    <service-author>${author}</service-author>
                    <service-version>1.0</service-version>
                    <service-comment></service-comment>
                    <service-by-default>0</service-by-default>
                    <!-- service-connexion -->
                    <inParameter-list>
${inparams}
                    </inParameter-list>
                    <outParameter-list>
${outparams}
                    </outParameter-list>
                    <DataStream-list>
${datastreams}
                    </DataStream-list>
                </component-service>"""
cataService=Template(cataService)
cataInparam="""                        <inParameter>
                          <inParameter-name>${name}</inParameter-name>
                          <inParameter-type>${type}</inParameter-type>
                       </inParameter>"""
cataInparam=Template(cataInparam)
cataOutparam="""                        <outParameter>
                          <outParameter-name>${name}</outParameter-name>
                          <outParameter-type>${type}</outParameter-type>
                       </outParameter>"""
cataOutparam=Template(cataOutparam)
cataInStream="""                       <inParameter>
                          <inParameter-name>${name}</inParameter-name>
                          <inParameter-type>${type}</inParameter-type>
                          <inParameter-dependency>${dep}</inParameter-dependency>
                       </inParameter>"""
cataInStream=Template(cataInStream)
cataOutStream="""                       <outParameter>
                          <outParameter-name>${name}</outParameter-name>
                          <outParameter-type>${type}</outParameter-type>
                          <outParameter-dependency>${dep}</outParameter-dependency>
                       </outParameter>"""
cataOutStream=Template(cataOutStream)

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
