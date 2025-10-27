cmake_minimum_required( VERSION 3.17 )

# Ensure using clang
set(CMAKE_C_COMPILER "$ENV{CONDA_PREFIX}/bin/clang" CACHE STRING "C compiler" FORCE)
set(CMAKE_CXX_COMPILER "$ENV{CONDA_PREFIX}/bin/clang++" CACHE STRING "C++ compiler" FORCE)

# Ensure CMake doesn't use system paths
set(CMAKE_FIND_ROOT_PATH "$ENV{CONDA_PREFIX}")
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

# Use libc++ instead of libstdc++
# set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -stdlib=libc++")

project( OCP )

include(ProcessorCount)

ProcessorCount(N_PROC)
if(NOT N_PROC OR N_PROC EQUAL 0)
    set(N_PROC 1)
endif()

message(STATUS "Found and use ${N_PROC} CPUs")

find_package( LLVM REQUIRED )
find_package( VTK REQUIRED
  COMPONENTS
    CommonCore
    WrappingPythonCore
    RenderingCore
    RenderingOpenGL2
    CommonDataModel
    CommonExecutionModel
    freetype
)

message(STATUS "VTK ${VTK_VERSION} found")

find_package( RapidJSON REQUIRED )
find_package( Clang REQUIRED )

set( Python_FIND_VIRTUALENV FIRST )
find_package( Python 3.9 COMPONENTS Interpreter Development REQUIRED )

# find OCCT and dump symbols
if(OCCT_LIB_DIR)
    file(GLOB occt_libs LIST_DIRECTORIES false ${OCCT_LIB_DIR} )
else()
    find_package( OpenCASCADE REQUIRED )

    foreach(target ${OpenCASCADE_LIBRARIES} )
        get_target_property(loc ${target} IMPORTED_LOCATION_RELEASE)
        list( APPEND occt_libs ${loc} )
    endforeach()
endif()

execute_process(
    COMMAND
    ${Python_EXECUTABLE}
    ${CMAKE_SOURCE_DIR}/dump_symbols.py
    "${occt_libs}"
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)

get_target_property( LIBCLANG_PATH libclang IMPORTED_LOCATION_RELEASE )
get_target_property( VTK_INCLUDE_DIR VTK::CommonCore INTERFACE_INCLUDE_DIRECTORIES )

# for some reason I get multiple generator expressions
string(REPLACE ">" ">;" VTK_INCLUDE_DIR ${VTK_INCLUDE_DIR})
list(GET VTK_INCLUDE_DIR 0 VTK_INCLUDE_DIR)

message( STATUS "Include dirs: ${VTK_INCLUDE_DIR}")
message( STATUS "Include dirs: ${CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES}")

if(NOT ${CMAKE_SYSTEM_NAME} STREQUAL "Darwin")
    foreach( inc IN LISTS CMAKE_CXX_IMPLICIT_INCLUDE_DIRECTORIES)
        list( APPEND CXX_INCLUDES -i ${inc}/ )
    endforeach()
else()
    list( APPEND CXX_INCLUDES -i /opt/usr/local/include/c++/v1/ -i /opt/usr/local/include/ )
endif()

if(PLATFORM)
    message( STATUS "Requested platform: ${PLATFORM}")
else()
    message( STATUS "Platform not specified.")

    if(${CMAKE_SYSTEM_NAME} STREQUAL "Windows")
        set(PLATFORM Windows)
    elseif(${CMAKE_SYSTEM_NAME} STREQUAL "Darwin")
        set(PLATFORM OSX)
    else()
        set(PLATFORM Linux)
    endif()
    message( STATUS "Set platform: ${PLATFORM}")
endif()

if(${PLATFORM} STREQUAL "OSX")
    list( APPEND CXX_INCLUDES 
        -i /opt/usr/local/include/c++/v1/ 
        -i /opt/usr/local/include/ 
    )
elseif(${PLATFORM} STREQUAL "Windows")
    list(APPEND CXX_INCLUDES
        -i /usr/x86_64-w64-mingw32/include
    )
else()
     list(APPEND CXX_INCLUDES
        -i $ENV{CONDA_PREFIX}/include/c++
    )   
endif()

message( STATUS "CXX_INCLUDES: ${CXX_INCLUDES}")

set(ENV{PYTHONPATH} ${CMAKE_SOURCE_DIR}/pywrap )

add_custom_command(
    OUTPUT ${CMAKE_SOURCE_DIR}/OCP/CMakeLists.txt
    COMMAND
        ${CMAKE_COMMAND} -E env "PYTHONPATH=${CMAKE_SOURCE_DIR}/pywrap"
        ${Python_EXECUTABLE}
        -m bindgen
        -n ${N_PROC}
        -i ${CLANG_INCLUDE_DIRS}/
        -i ${VTK_INCLUDE_DIR}/
        -i ${CLANG_INSTALL_PREFIX}/lib/clang/${LLVM_VERSION_MAJOR}/include/
        -p ${CMAKE_SOURCE_DIR}
        ${CXX_INCLUDES}
        all ${CMAKE_SOURCE_DIR}/ocp.toml ${PLATFORM}
        WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    DEPENDS ${CMAKE_SOURCE_DIR}/ocp.toml
    USES_TERMINAL
    COMMENT "Running pywrap"
)

add_custom_target(pywrap ALL DEPENDS ${CMAKE_SOURCE_DIR}/OCP/CMakeLists.txt)
