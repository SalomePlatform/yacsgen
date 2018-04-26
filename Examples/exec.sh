#/bin/bash
# execute a command within SALOME environment 

com=$*

# Modify to your SALOME installation
export SALOME_DIR=path_to_appli
export SALOME_PACKAGES=path_to_salome_prerequisites.sh

source $SALOME_PACKAGES/salome_prerequisites.sh
source $SALOME_PACKAGES/salome_modules.sh

echo execution: $com
$com

