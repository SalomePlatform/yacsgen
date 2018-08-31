#/bin/bash
# execute a command within SALOME environment 

com=$*

# Modify to your SALOME installation
export SALOME_DIR=__YACSGEN_INSTALL_PATH__
export SALOME_PACKAGES=__YACSGEN_INSTALL_PATH__

source $SALOME_PACKAGES/salome_prerequisites.sh
source $SALOME_PACKAGES/salome_modules.sh

echo execution: $com
$com

