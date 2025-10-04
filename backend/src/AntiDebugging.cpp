#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"

using namespace llvm;

namespace {

struct AntiDebugging : public PassInfoMixin<AntiDebugging> {
  PreservedAnalyses run(Module &M, ModuleAnalysisManager &AM) {
    // ONLY add to non-main functions
    bool changed = false;
    
    for (Function &F : M) {
      if (F.isDeclaration() || F.getName() == "main") continue;
      
      // Add simple bogus instruction that does nothing
      addBogusDebugCheck(&F);
      changed = true;
    }

    if (changed) {
      errs() << "🕵️‍♂️ AntiDebugging: Added to non-main functions\n";
      return PreservedAnalyses::none();
    }
    return PreservedAnalyses::all();
  }

private:
  void addBogusDebugCheck(Function *F) {
    // Just add a harmless arithmetic operation that gets optimized away
    BasicBlock &entry = F->getEntryBlock();
    IRBuilder<> builder(&entry.front());
    
    Value *dummy1 = builder.getInt32(42);
    Value *dummy2 = builder.getInt32(123);
    builder.CreateAdd(dummy1, dummy2, "bogus_debug_check"); // This does nothing
  }
};

} // anonymous namespace

void registerAntiDebuggingPass(PassBuilder &PB) {
  PB.registerPipelineParsingCallback(
    [](StringRef Name, ModulePassManager &MPM,
       ArrayRef<PassBuilder::PipelineElement>) {
      if (Name == "anti-debug") {
        MPM.addPass(AntiDebugging());
        return true;
      }
      return false;
    });
}