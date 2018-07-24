#/bin/bash
# execute a command within SALOME environment 

com=$*

# Modify to your SALOME installation
export SALOME_DIR=/home/I35256/salome/C9

source $SALOME_DIR/salome_prerequisites.sh
source $SALOME_DIR/salome_modules.sh
source $SALOME_DIR/modules/build/YACS_master/.yamm/env_build.sh

echo execution: $com
$com

