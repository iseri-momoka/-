cmake_minimum_required( VERSION 3.16 )

project( CloudCompareSlim )

# Prevent in-source build
string( TOLOWER "${CMAKE_CURRENT_SOURCE_DIR}" _src )
string( TOLOWER "${CMAKE_CURRENT_BINARY_DIR}" _bin )
if ( "${_src}" STREQUAL "${_bin}" )
	message( FATAL_ERROR "Do not build directly in the source folder! Create a 'build' directory and run cmake from there." )
endif()

# Add our cmake module path
list( APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/" )

include( CMakePolicies )
include( CMakeSetCompilerOptions )
include( DeployQt )
include( CMakeInclude )
include( Install )

# CCViewer
option( OPTION_BUILD_CCVIEWER "Check to compile CCViewer project" ON )

# Testing
option( BUILD_TESTING "Build tests for CC" OFF )

# Default debug suffix for libraries
set( CMAKE_DEBUG_POSTFIX "d" )

# Destination folders
if( WIN32 OR APPLE )
	set( CLOUDCOMPARE_DEST_FOLDER CloudCompare )
	set( CCVIEWER_DEST_FOLDER ccViewer )
else()
	set( CLOUDCOMPARE_DEST_FOLDER bin )
	set( CCVIEWER_DEST_FOLDER bin )
endif()

if( WIN32 )
	set( INSTALL_DESTINATIONS ${CLOUDCOMPARE_DEST_FOLDER} )
	if( ${OPTION_BUILD_CCVIEWER} )
		list( APPEND INSTALL_DESTINATIONS ${CCVIEWER_DEST_FOLDER} )
	endif()
endif()

# Add external libraries (Qt)
include( CMakeExternalLibs )

# Internal libs
add_subdirectory( libs )

# Plugins (qCoreIO + qLASIO)
add_subdirectory( plugins )

# CCViewer (our main app)
if( OPTION_BUILD_CCVIEWER )
	add_subdirectory( ccViewer )
endif()
