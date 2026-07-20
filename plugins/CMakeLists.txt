project( CloudComparePlugins )

# Add our cmake module path so we don't need relative paths for these
list( APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/" )

include( Plugins )

set( CloudCompare_SOURCE_DIR "${CMAKE_SOURCE_DIR}/qCC_selected" )
set( CloudComparePlugins_SOURCE_DIR "${CMAKE_SOURCE_DIR}/plugins" )

add_subdirectory( core )
