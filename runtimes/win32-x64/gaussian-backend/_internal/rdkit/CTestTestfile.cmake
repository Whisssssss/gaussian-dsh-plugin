# CMake generated Testfile for 
# Source directory: D:/bld/rdkit-meta_1756565448258/work/rdkit
# Build directory: D:/bld/rdkit-meta_1756565448258/work/rdkit
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
add_test(pythonSourceTests "D:/YDW/Trae_Gromacs/miniconda3/python.exe" "-m" "pytest")
set_tests_properties(pythonSourceTests PROPERTIES  WORKING_DIRECTORY "D:/bld/rdkit-meta_1756565448258/work/rdkit" _BACKTRACE_TRIPLES "D:/bld/rdkit-meta_1756565448258/work/Code/cmake/Modules/RDKitUtils.cmake;242;add_test;D:/bld/rdkit-meta_1756565448258/work/rdkit/CMakeLists.txt;22;add_pythonpytest;D:/bld/rdkit-meta_1756565448258/work/rdkit/CMakeLists.txt;0;")
subdirs("Chem")
