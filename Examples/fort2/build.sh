../exec.sh python components.py
../exec.sh make

# test
appli/salome -t
appli/salome shell ../test_compo.py
appli/salome killall
