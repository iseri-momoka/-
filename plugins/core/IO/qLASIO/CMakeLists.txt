option(PLUGIN_IO_QLAS "LAS IO plugin using laszip" OFF)

if (PLUGIN_IO_QLAS)
    project(QLAS_IO_PLUGIN)

    # Build LASzip from bundled source
    set(LASZIP_DIR "${CMAKE_SOURCE_DIR}/libs/qCC_io/extern/laszip" CACHE PATH "LASzip source directory")
    add_subdirectory("${LASZIP_DIR}" "${CMAKE_BINARY_DIR}/extern/laszip" EXCLUDE_FROM_ALL)

    AddPlugin(NAME ${PROJECT_NAME} TYPE io)

    target_compile_definitions(${PROJECT_NAME} PRIVATE -DQT_FORCE_ASSERTS)

    # Include laszip headers (for #include "laszip/laszip_api.h")
    target_include_directories(${PROJECT_NAME} PRIVATE
        "${LASZIP_DIR}/include"
        "${CMAKE_BINARY_DIR}/extern/laszip/include"
    )

    # Link laszip3 (the main library that has an import library)
    set(LASZIP_LIB_DIR "${CMAKE_BINARY_DIR}/extern/laszip/lib")
    target_link_libraries(${PROJECT_NAME}
        "${LASZIP_LIB_DIR}/laszip3.lib"
    )

    # Ensure laszip DLLs are built before the plugin (needed for post-build copy)
    add_dependencies(${PROJECT_NAME} laszip_api3 laszip3)

    # Note: laszip_api3.dll doesn't generate an import library in the laszip build system.
    # The API functions are already available through laszip3.lib, so we don't need to link laszip_api3 separately.

    # Copy laszip DLLs to the plugin output directory so ccViewer can find them
    foreach(_dll laszip_api3 laszip3)
        add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
            COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${CMAKE_BINARY_DIR}/extern/laszip/bin/${_dll}.dll"
                "$<TARGET_FILE_DIR:${PROJECT_NAME}>"
            COMMENT "Copying ${_dll}.dll to plugin directory"
        )
    endforeach()

    add_subdirectory(include)
    add_subdirectory(src)
    add_subdirectory(ui)

endif()
