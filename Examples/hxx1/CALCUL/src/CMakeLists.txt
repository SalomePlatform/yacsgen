CMAKE_MINIMUM_REQUIRED(VERSION 2.8.8 FATAL_ERROR)
PROJECT(CALCUL C CXX)


SET(BUILD_SHARED_LIBS TRUE)

SET(_lib_HEADERS
  CALCUL.hxx
)

SET(_lib_SOURCES
  CALCUL.cxx
)

ADD_LIBRARY(CALCULCXX ${_lib_SOURCES})
TARGET_LINK_LIBRARIES(CALCULCXX )

INSTALL(TARGETS CALCULCXX DESTINATION lib)
INSTALL(FILES ${_lib_HEADERS} DESTINATION include)

