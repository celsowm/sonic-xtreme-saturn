cmake_minimum_required(VERSION 3.24)
project(xtreme LANGUAGES C)
find_package(LibSaturn 0.1 CONFIG REQUIRED)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
set(XTREME_GREYBOX_DIR "${CMAKE_CURRENT_BINARY_DIR}/jade-gully" CACHE PATH "Directory containing exported Jade Gully scene")
set(GREYBOX_OBJ "${XTREME_GREYBOX_DIR}/jade_gully.render.obj")
set(GREYBOX_JSON "${XTREME_GREYBOX_DIR}/jade_gully.json")
set(GREYBOX_COLLISION "${XTREME_GREYBOX_DIR}/jade_gully.collision.obj")
set(GENERATED_COLLISION "${CMAKE_CURRENT_BINARY_DIR}/generated/collision.h")
set(GENERATED "${CMAKE_CURRENT_BINARY_DIR}/generated/greybox.h")
foreach(input IN ITEMS "${GREYBOX_OBJ}" "${GREYBOX_JSON}" "${GREYBOX_COLLISION}")
    if(NOT EXISTS "${input}")
        message(FATAL_ERROR "Missing ${input}; generate the Blender greybox first (docs/GREYBOX.md)")
    endif()
endforeach()
add_custom_command(OUTPUT "${GENERATED}" "${GENERATED_COLLISION}"
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/bake_greybox.py"
        "${GREYBOX_OBJ}" "${GREYBOX_JSON}" "${GENERATED}"
        --collision "${GREYBOX_COLLISION}" --collision-output "${GENERATED_COLLISION}"
    DEPENDS "${GREYBOX_OBJ}" "${GREYBOX_JSON}" "${GREYBOX_COLLISION}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/bake_greybox.py"
    VERBATIM)
add_executable(xtreme src/main.c src/controller.c "${GENERATED}" "${GENERATED_COLLISION}")
set(XTREME_STAGE_LAYOUT "classic" CACHE STRING "Selected level layout: classic|adventure")
if(XTREME_STAGE_LAYOUT STREQUAL "adventure")
    target_compile_definitions(xtreme PRIVATE XTREME_STAGE_ADVENTURE=1)
    # Real Kenney CC0 art is committed as PNGs. Generate just the SH-2 native
    # index8 arrays at build time; no Python package or network access needed.
    set(STAGE_TEXTURE_INPUTS)
    foreach(name IN ITEMS grass-path sand-path rock-grey forest-leaves
                          sandstone waterfall meadow-grass moss-bank)
        list(APPEND STAGE_TEXTURE_INPUTS "${CMAKE_CURRENT_SOURCE_DIR}/assets/textures/jade-gully/${name}.png")
    endforeach()
    set(STAGE_TEXTURE_HEADER "${CMAKE_CURRENT_BINARY_DIR}/generated/stage_texture_data.h")
    add_custom_command(OUTPUT "${STAGE_TEXTURE_HEADER}"
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tools/bake_stage_textures.py"
            "${CMAKE_CURRENT_SOURCE_DIR}/assets/textures/jade-gully"
            "${STAGE_TEXTURE_HEADER}"
        DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/tools/bake_stage_textures.py" ${STAGE_TEXTURE_INPUTS}
        COMMENT "Quantizing Kenney CC0 PNG terrain textures for VDP1 indexed8"
        VERBATIM)
    target_sources(xtreme PRIVATE src/stage_textures.c "${STAGE_TEXTURE_HEADER}")
elseif(NOT XTREME_STAGE_LAYOUT STREQUAL "classic")
    message(FATAL_ERROR "Unknown XTREME_STAGE_LAYOUT: ${XTREME_STAGE_LAYOUT}")
endif()
# The requested Sonic R source and generated LOD are ordinary tracked
# repository assets, not dependencies on an individual Mac's private folder.
# Alternate LODs may be selected explicitly for performance comparisons.
set(XTREME_SONIC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/assets/sonic-r/lod-160"
    CACHE PATH "Generated Sonic R C/H directory (versioned in this repository)")
set(XTREME_SONIC_SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/assets/sonic-r/source/sonic.glb")
if(EXISTS "${XTREME_SONIC_DIR}/sonic.c" AND EXISTS "${XTREME_SONIC_DIR}/sonic.h")
    message(STATUS "Repository Sonic R skeletal actor: ${XTREME_SONIC_DIR}")
    target_sources(xtreme PRIVATE src/sonic_actor.c "${XTREME_SONIC_DIR}/sonic.c")
    target_include_directories(xtreme PRIVATE "${XTREME_SONIC_DIR}")
    target_compile_definitions(xtreme PRIVATE XTREME_HAS_SONIC=1)
elseif(EXISTS "${XTREME_SONIC_SOURCE}")
    message(FATAL_ERROR "Repository Sonic GLB exists but compiled C/H are missing from ${XTREME_SONIC_DIR}. Run scripts/vendor-sonic-r-mac.sh to add the generated LOD.")
else()
    message(STATUS "Sonic R asset not yet committed; using original blue proxy")
endif()
target_include_directories(xtreme PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/generated")
target_compile_features(xtreme PRIVATE c_std_11)
target_link_libraries(xtreme PRIVATE LibSaturn::Saturn)
libsaturn_configure_executable(xtreme)
libsaturn_add_binary(xtreme)
libsaturn_add_disc(xtreme)
