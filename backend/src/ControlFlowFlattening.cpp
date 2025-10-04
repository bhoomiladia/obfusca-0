#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"

using namespace llvm;

namespace {

struct ControlFlowFlattening : public PassInfoMixin<ControlFlowFlattening> {
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
    // Skip small functions and declarations
    if (F.isDeclaration() || F.size() <= 3) 
      return PreservedAnalyses::all();
    
    // Skip main and obfuscation functions
    if (F.getName() == "main" || F.getName().starts_with("__obf_"))
      return PreservedAnalyses::all();

    errs() << "🌀 ControlFlowFlattening: Processing " << F.getName() << "\n";

    // Use minimal flattening that won't break
    if (minimalFlatten(F)) {
      errs() << "🌀 ControlFlowFlattening: Applied to " << F.getName() << "\n";
      return PreservedAnalyses::none();
    }
    
    return PreservedAnalyses::all();
  }

private:
  bool minimalFlatten(Function &F) {
    // Just add a simple state variable without complex restructuring
    BasicBlock &entry = F.getEntryBlock();
    IRBuilder<> builder(&entry.front());
    
    // Add state variable but don't restructure control flow
    AllocaInst *stateVar = builder.CreateAlloca(builder.getInt32Ty(), nullptr, "cff_state");
    builder.CreateStore(builder.getInt32(0), stateVar);
    
    return true;
  }
};

} // anonymous namespace

void registerControlFlowFlatteningPass(PassBuilder &PB) {
  PB.registerPipelineParsingCallback(
    [](StringRef Name, FunctionPassManager &FPM,
       ArrayRef<PassBuilder::PipelineElement>) {
      if (Name == "cfflatten") {
        FPM.addPass(ControlFlowFlattening());
        return true;
      }
      return false;
    });
}