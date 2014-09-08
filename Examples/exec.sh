#/bin/bash
# execute a command within SALOME environment 

com=$*

# Modify to your SALOME installation
export SALOME_DIR=/local00/home/I35256/salome/install/V7_main_git

source $SALOME_DIR/salome_prerequisites.sh
source $SALOME_DIR/salome_modules.sh

echo execution: $com
$com

