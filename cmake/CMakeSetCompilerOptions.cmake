# Require C++17
set( CMAKE_CXX_STANDARD 17 )
set( CMAKE_CXX_STANDARD_REQUIRED ON )
set( CMAKE_CXX_EXTENSIONS NO )

add_compile_definitions(QT_DISABLE_DEPRECATED_UP_TO=0x050F00)

# ccache
# https://crascit.com/2016/04/09/using-ccache-with-cmake/
find_program( CCACHE_PROGRAM ccache )

if ( CCACHE_PROGRAM )
    set( CMAKE_CXX_COMPILER_LAUNCHER ${CCACHE_PROGRAM} )
    set( CMAKE_C_COMPILER_LAUNCHER ${CCACHE_PROGRAM} )
endif()

# Link Time Optimization (LTO) for Release builds
# (disabled for MinGW: GCC LTO produces "multiple definition" errors on
#  dllexported virtual destructor thunks in qCC_db)
if( NOT MINGW )
    include(CheckIPOSupported)
    check_ipo_supported(RESULT ipo_supported OUTPUT ipo_output)
    if( ipo_supported )
        set( CMAKE_INTERPROCEDURAL_OPTIMIZATION TRUE )
    else()
        message( STATUS "LTO not supported: ${ipo_output}" )
    endif()
endif()

if ( UNIX )
    set( CMAKE_POSITION_INDEPENDENT_CODE ON )
	add_definitions(-Wno-deprecated-declarations)
elseif( MSVC )
    add_definitions(-DNOMINMAX -D_CRT_SECURE_NO_WARNINGS -D__STDC_LIMIT_MACROS)

    # Multithreaded compilation (default ON for faster builds)
    option( OPTION_MP_BUILD "Check to activate multithreaded compilation with MSVC" ON )
    if( ${OPTION_MP_BUILD} )
       set( CMAKE_CXX_FLAGS ${CMAKE_CXX_FLAGS}\ /MP)
    endif()

    #use VLD for mem leak checking
    option( OPTION_USE_VISUAL_LEAK_DETECTOR "Check to activate compilation (in debug) with Visual Leak Detector" OFF )
    if( ${OPTION_USE_VISUAL_LEAK_DETECTOR} )
        set( CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} /D USE_VLD" )
    endif()
endif()
