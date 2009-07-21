# -*- coding: utf-8 *-
import os
from module_generator import Generator,Module,Service,PACOComponent

context={'update':1,
         "makeflags":"-j2",
         "prerequisites":"/home/aribes/Dev/Scripts_env/prerequis.sh",
         "kernel":"/home/aribes/Dev/Install/SALOME/KERNEL_INSTALL-RIBES",
         "paco":"/home/aribes/Dev/Install/PaCO++_install",
         "mpi":"/usr/lib/openmpi"
        }

cwd=os.getcwd()

master_body="""
  // Init data
  Ports::Param_Double_Port::seq_double data;
  data.length(10);
  for (double i=0; i< 10; i++) 
    data[i] = i; 
  _master_port_port->configure_port_method_put(10);
  _master_port_port->put(data);

  Ports::Param_Double_Port::seq_double * results;
  _master_port_port->get_results(results);
  std::cerr << "Master receive a sequence of length = " << results->length() << std::endl;
  for (int i = 0; i < results->length(); i++)
    std::cerr << "Master receive data : " << (*results)[i] << std::endl;
  delete results;
"""

worker_body="""
  // Réception des données
  Ports::Param_Double_Port::seq_double * data = _worker_port_port->get_data();
  std::cerr << "Node " << getMyRank() << " receive a sequence of length = " << data->length() << std::endl;
  for (int i = 0; i < data->length(); i++)
    std::cerr << "Node " << getMyRank() << " receive data : " << (*data)[i] << std::endl;
  delete data;

  // Envoi des données
  data = new Ports::Param_Double_Port::seq_double();
  data->length(5);
  for (double i=0; i< 5; i++) 
  {
    (*data)[i] = i + i + (getMyRank() * 20);
  }
  _worker_port_port->configure_set_data(5, 5*getTotalNode(), 5*getMyRank());
  _worker_port_port->set_data(data);
  delete data;
"""

c1=PACOComponent("MASTER",
                 "dummy",
                 services=[
                   Service("StartMaster",
                           parallel_outstream=[("master_port", "Param_Double_Port")],
                           body=master_body,
                           impl_type="parallel"
                          ),
                ],
               )

c2=PACOComponent("WORKER",
                 "mpi",
                 services=[
                   Service("StartWorker",
                           parallel_instream=[("worker_port", "Param_Double_Port")],
                           body=worker_body,
                           impl_type="parallel"
                          ),
                ],
               )


g=Generator(Module("DSC_PARALLEL_PARAM",components=[c1, c2],prefix="./install"),context)
g.generate()
g.bootstrap()
g.configure()
g.make()
g.install()
g.make_appli("appli",
             restrict=["KERNEL","GUI","YACS"],
             altmodules={"GUI":"/home/aribes/Dev/Install/SALOME/GUI_INSTALL",
                         "YACS":"/home/aribes/Dev/Install/SALOME/YACS_INSTALL"})

