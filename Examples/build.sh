#/bin/bash
# build all examples

cur_dir=`pwd`

script_dir=`dirname $0`

# activate stop on error
set -e

cd $script_dir

list_dirs="calcium1 calcium2 cpp1 cpp2 cppgui1 fort1 fort2 pydoc1 pygui1 pyth1 pyth2 types1 hxx1"
for dir in $list_dirs ; do
  cd $dir
  echo Building $dir ... "(see build.log & build.err)"
  ./build.sh > build.log 2> build.err
  cd ..
done

echo Build finished!
