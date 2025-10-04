cmake_minimum_required(VERSION 3.16)
project(llvm_obf_starter LANGUAGES CXX)

find_package(LLVM REQUIRED CONFIG)
message(STATUS "Found LLVM ${LLVM_PACKAGE_VERSION}")

add_definitions(${LLVM_DEFINITIONS})
include_directories(${LLVM_INCLUDE_DIRS})

# Get LLVM components
llvm_map_components_to_libnames(llvm_libs
  Core
  Support
  TransformUtils
  Analysis
)



# Advanced Obfuscation Passes - ALL PASSES TOGETHER
add_library(AdvancedObfuscationPasses MODULE
  src/AdvancedObfuscationPlugin.cpp
  src/RenameSymbolsPass.cpp
  src/BogusInstructionsPass.cpp
  src/StringEncryptPass.cpp
  src/DynamicXORPass.cpp
  src/ControlFlowFlattening.cpp
  src/OpaquePredicates.cpp
  src/AntiDebugging.cpp
  src/BasicBlockSplit.cpp
)
set_target_properties(AdvancedObfuscationPasses PROPERTIES PREFIX "")
target_link_libraries(AdvancedObfuscationPasses PRIVATE ${llvm_libs})

# Copy DLLs for easy access
if(WIN32)
  add_custom_command(TARGET AdvancedObfuscationPasses POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:AdvancedObfuscationPasses> ${CMAKE_BINARY_DIR}
  )
endif()