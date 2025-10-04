#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"

using namespace llvm;

// Forward declarations from PrintFuncsPass
// extern void registerPrintFunctionsPass(PassBuilder &PB);
extern void registerRenameSymbolsPass(PassBuilder &PB);
extern void registerStringEncryptPass(PassBuilder &PB);
extern void registerBogusInstructionsPass(PassBuilder &PB);

// Forward declarations from other pass files
extern void registerDynamicXORPass(PassBuilder &PB);
extern void registerControlFlowFlatteningPass(PassBuilder &PB);
extern void registerOpaquePredicatesPass(PassBuilder &PB);
extern void registerBasicBlockSplitPass(PassBuilder &PB);
extern void registerAntiDebuggingPass(PassBuilder &PB);

// ONLY ONE llvmGetPassPluginInfo in the entire project
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo
llvmGetPassPluginInfo() {
    return {
        LLVM_PLUGIN_API_VERSION, "AdvancedObfuscationPasses", "v1.0",
        [](PassBuilder &PB) {
            // Register all passes from PrintFuncsPass
            // registerPrintFunctionsPass(PB);
            registerRenameSymbolsPass(PB);
            registerStringEncryptPass(PB);
            registerBogusInstructionsPass(PB);
            
            // Register advanced passes
            registerDynamicXORPass(PB);
            registerControlFlowFlatteningPass(PB);
            registerOpaquePredicatesPass(PB);
            registerBasicBlockSplitPass(PB);
            registerAntiDebuggingPass(PB);
            
            errs() << "🔧 AdvancedObfuscationPasses plugin loaded successfully!\n";
            errs() << "   Available passes: print-funcs, rename-symbols, stringenc, bogus-instructions\n";
            errs() << "   Advanced passes: dynamic-xor, cfflatten, opaque-preds, bbsplit, anti-debug\n";
        }
    };
}