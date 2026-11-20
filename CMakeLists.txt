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
# Character assets are generated on the user's Mac and never committed.
# Keep the baseline build reproducible without any third-party character data.
set(XTREME_SONIC_DIR "${CMAKE_CURRENT_SOURCE_DIR}/assets/private/sonic-r/saturn"
    CACHE PATH "Private generated Sonic R skeletal C/H directory")
if(EXISTS "${XTREME_SONIC_DIR}/sonic.c" AND EXISTS "${XTREME_SONIC_DIR}/sonic.h")
    message(STATUS "Private Sonic R actor: enabled (local-only)")
    target_sources(xtreme PRIVATE src/sonic_actor.c "${XTREME_SONIC_DIR}/sonic.c")
    target_include_directories(xtreme PRIVATE "${XTREME_SONIC_DIR}")
    target_compile_definitions(xtreme PRIVATE XTREME_HAS_SONIC=1)
else()
    message(STATUS "Private Sonic R actor: not installed; using original blue proxy")
endif()
target_include_directories(xtreme PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/generated")
target_compile_features(xtreme PRIVATE c_std_11)
target_link_libraries(xtreme PRIVATE LibSaturn::Saturn)
libsaturn_configure_executable(xtreme)
libsaturn_add_binary(xtreme)
libsaturn_add_disc(xtreme)
