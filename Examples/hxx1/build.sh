
# build COMPONENTCPP lib
tar -xzvf cpp_component.tgz
mkdir COMPONENTCPP_BUILD
export HXXTESTPATH=`pwd`
cd COMPONENTCPP_SRC
../../exec.sh ./build_configure
cd ../COMPONENTCPP_BUILD
../../exec.sh ../COMPONENTCPP_SRC/configure --prefix=$HXXTESTPATH/COMPONENTCPP_INSTALL
../../exec.sh make
../../exec.sh make install
cd ..
# build & test SALOME component 
../exec.sh python component.py

appli/salome start -t
appli/salome shell python test_compohxx.py
appli/salome killall
