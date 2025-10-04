#include "llvm/IR/PassManager.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Passes/PassBuilder.h"
#include <random>
#include <sstream>
#include <iomanip>
#include <map>

using namespace llvm;

namespace {

struct RenameSymbolsPass : PassInfoMixin<RenameSymbolsPass> {
    RenameSymbolsPass(unsigned seed = 0) : RNG(seed ? seed : 0xC0FFEE) {}

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
        unsigned funcCount = 0, globalCount = 0;
        StringRef preserveName = "main";
        
        std::map<std::string, std::string> renamedFunctions;
        std::map<std::string, std::string> renamedGlobals;

        for (Function &F : M) {
            if (F.isDeclaration()) continue;
            if (F.getName() == preserveName) continue;
            
            std::string oldName = F.getName().str();
            std::string newName = genName("f", ++funcCount);
            F.setName(newName);
            renamedFunctions[oldName] = newName;
        }

        for (GlobalVariable &G : M.globals()) {
            if (G.isDeclaration() || !G.hasName()) continue;
            if (G.getName().starts_with("llvm.")) continue;
            if (G.getLinkage() == GlobalValue::AppendingLinkage) continue;

            std::string oldName = G.getName().str();
            std::string newName = genName("g", ++globalCount);
            G.setName(newName);
            renamedGlobals[oldName] = newName;
        }

        // Output JSON report
        errs() << "{\"pass\": \"rename-symbols\", \"functions_renamed\": " << funcCount;
        errs() << ", \"globals_renamed\": " << globalCount;
        
        errs() << ", \"renamed_functions\": {";
        bool first = true;
        for (const auto& [oldName, newName] : renamedFunctions) {
            if (!first) errs() << ", ";
            errs() << "\"" << oldName << "\": \"" << newName << "\"";
            first = false;
        }
        errs() << "}";
        
        errs() << ", \"renamed_globals\": {";
        first = true;
        for (const auto& [oldName, newName] : renamedGlobals) {
            if (!first) errs() << ", ";
            errs() << "\"" << oldName << "\": \"" << newName << "\"";
            first = false;
        }
        errs() << "}";
        
        errs() << "}\n";

        return PreservedAnalyses::all();
    }

private:
    std::mt19937 RNG;
    std::string genName(const char *prefix, unsigned idx) {
        std::stringstream ss;
        uint32_t r = RNG();
        ss << prefix << "_" << idx << "_" << std::hex << std::setw(8) << std::setfill('0') << r;
        return ss.str();
    }
};

} // namespace

void registerRenameSymbolsPass(PassBuilder &PB) {
    PB.registerPipelineParsingCallback(
        [](StringRef name, ModulePassManager &MPM, ArrayRef<PassBuilder::PipelineElement>) {
            if (name == "rename-symbols") {
                MPM.addPass(RenameSymbolsPass());
                return true;
            }
            return false;
        });
}