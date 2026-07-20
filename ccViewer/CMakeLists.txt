project( ccViewer VERSION 1.38.0 )

include( CMakePolicies NO_POLICY_SCOPE )

include_directories( ${CloudComparePlugins_SOURCE_DIR} )
include_directories( ${CMAKE_CURRENT_SOURCE_DIR} )
include_directories( ${CMAKE_CURRENT_BINARY_DIR} )
include_directories( ${CMAKE_CURRENT_SOURCE_DIR}/../qCC_selected/dialogs )

# ccViewer sources
file( GLOB header_list *.h )
file( GLOB source_list *.cpp )

# qCC_selected dialog sources (only the 4 clean ones)
set( QCC_SEL "${CMAKE_CURRENT_SOURCE_DIR}/../qCC_selected" )

list( APPEND source_list
	"${QCC_SEL}/dialogs/ccNormalComputationDlg.cpp"
	"${QCC_SEL}/dialogs/ccSubsamplingDlg.cpp"
	"${QCC_SEL}/dialogs/ccFilterByValueDlg.cpp"
	"${QCC_SEL}/dialogs/ccSORFilterDlg.cpp"
)
list( APPEND header_list
	"${QCC_SEL}/dialogs/ccNormalComputationDlg.h"
	"${QCC_SEL}/dialogs/ccSubsamplingDlg.h"
	"${QCC_SEL}/dialogs/ccFilterByValueDlg.h"
	"${QCC_SEL}/dialogs/ccSORFilterDlg.h"
)

# UI files for 4 dialogs
set( qcc_ui_list
	"${QCC_SEL}/ui_templates/normalComputationDlg.ui"
	"${QCC_SEL}/ui_templates/subsamplingDlg.ui"
	"${QCC_SEL}/ui_templates/filterByValueDlg.ui"
	"${QCC_SEL}/ui_templates/sorFilterDlg.ui"
)

# ccViewer own UI files
file( GLOB ccviewer_ui_list ui_templates/*.ui )

qt6_wrap_ui( generated_ui_list ${ccviewer_ui_list} ${qcc_ui_list} )

# qrc resources
file( GLOB qrc_list *.qrc )
if (qrc_list)
	qt6_add_resources( generated_qrc_list ${qrc_list} )
endif()

if( MSVC )
	set( rc_list images/icon/cc_viewer_icon.rc )
	add_executable( ${PROJECT_NAME} WIN32 ${header_list} ${source_list} ${generated_ui_list} ${generated_qrc_list} ${rc_list} )
elseif( APPLE )
	add_executable( ${PROJECT_NAME} MACOSX_BUNDLE ${header_list} ${generated_ui_list} ${source_list} ${generated_qrc_list} )
else()
	add_executable( ${PROJECT_NAME} ${header_list} ${source_list} ${generated_ui_list} ${generated_qrc_list} )
endif()

target_link_libraries( ${PROJECT_NAME}
	PUBLIC
		CCPluginStub
)

if( CCCORELIB_USE_QT_CONCURRENT )
	target_link_libraries( ${PROJECT_NAME} PRIVATE Qt6::Concurrent )
endif()

if( WIN32 )
	DeployQt( TARGET ${PROJECT_NAME} DEPLOY_PATH ${CCVIEWER_DEST_FOLDER} )
else()
	DeployQt( TARGET ${PROJECT_NAME} DEPLOY_PATH ${PROJECT_NAME} )
endif()

target_link_libraries( ${PROJECT_NAME} PRIVATE CCAppCommon )

set( CC_VIEWER_SHORT_VERSION "1.38.0" )

target_compile_definitions( ${PROJECT_NAME} PUBLIC CC_VIEWER )
target_compile_definitions( ${PROJECT_NAME} PRIVATE CC_VIEWER_SHORT_VERSION="${CC_VIEWER_SHORT_VERSION}" )

if (WIN32 AND MSVC)
	set_target_properties( ${PROJECT_NAME} PROPERTIES LINK_FLAGS " /MANIFEST:NO" )
endif()

if( WIN32 AND MINGW )
	add_custom_command( TARGET ${PROJECT_NAME} PRE_BUILD
		COMMAND ${CMAKE_RC_COMPILER} -i ${CMAKE_CURRENT_SOURCE_DIR}/images/icon/cc_viewer_icon.rc
		--input-format=rc -o ${CMAKE_CURRENT_BINARY_DIR}/ccViewer.res -O coff )
endif()

if (NOT APPLE)
	install_ext( TARGETS ccViewer ${CCVIEWER_DEST_FOLDER} "" )
endif()

set( auxFiles bin_other/license.txt )
if( WIN32 )
	list( APPEND auxFiles bin_other/start.bat )
endif()
if(APPLE OR WIN32)
	foreach( filename ${auxFiles} )
		install_ext( FILES ${filename} ${CCVIEWER_DEST_FOLDER} "" )
	endforeach()
endif()

if( APPLE )
	add_subdirectory( Mac )
endif()

if( APPLE )
	InstallPlugins( TYPES "gl;io;standard" DEST_PATH "${CCVIEWER_MAC_PLUGIN_DIR}" SHADER_DEST_PATH "${CCVIEWER_MAC_BASE_DIR}/Contents/Shaders" )
elseif( UNIX )
	InstallPlugins( TYPES "gl;io;standard" DEST_PATH "${CMAKE_INSTALL_LIBDIR}/cloudcompare/plugins" SHADER_DEST_PATH share/cloudcompare/shaders )
else()
	InstallPlugins( TYPES "gl;io;standard" DEST_PATH "${CCVIEWER_DEST_FOLDER}" DEST_FOLDER "plugins" SHADER_DEST_PATH "${CCVIEWER_DEST_FOLDER}" SHADER_DEST_FOLDER "shaders" )
endif()

add_custom_target(CC_VIEWER_UPDATE_VERSION ALL COMMAND ${CMAKE_COMMAND} -E touch_nocreate ${CMAKE_CURRENT_SOURCE_DIR}/ccViewerApplication.cpp)
