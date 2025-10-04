#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"

using namespace llvm;

namespace {
struct OpaquePredicates : public PassInfoMixin<OpaquePredicates> {
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
    if (F.isDeclaration() || F.size() < 2) 
      return PreservedAnalyses::all();
    
    bool changed = false;
    unsigned predicateCount = 0;

    for (auto &BB : F) {
      if (BB.size() > 5 && predicateCount < 2) {
        if (insertSimpleOpaquePredicate(&BB)) {
          changed = true;
          predicateCount++;
        }
      }
    }

    if (changed) {
      errs() << "🧠 OpaquePredicates: Added " << predicateCount << " predicates to " << F.getName() << "\n";
      return PreservedAnalyses::none();
    }
    return PreservedAnalyses::all();
  }

private:
  bool insertSimpleOpaquePredicate(BasicBlock *BB) {
    if (!BB->getTerminator()) return false;
    
    IRBuilder<> builder(BB->getTerminator());
    
    // Simple always-true condition
    Value *x = builder.getInt32(42);
    Value *square = builder.CreateMul(x, x, "square");
    Value *predicate = builder.CreateICmpSGE(square, builder.getInt32(0), "opaque_pred");
    
    // Split block - use simpler version
    Instruction *splitPoint = BB->getTerminator();
    BasicBlock *falseBlock = BB->splitBasicBlock(splitPoint, "bogus_path");
    BasicBlock *trueBlock = BB;
    
    // Replace terminator with conditional branch
    trueBlock->getTerminator()->eraseFromParent();
    builder.SetInsertPoint(trueBlock);
    builder.CreateCondBr(predicate, falseBlock, falseBlock); // Both go to same block
    
    return true;
  }
};
}

void registerOpaquePredicatesPass(PassBuilder &PB) {
  PB.registerPipelineParsingCallback(
    [](StringRef Name, FunctionPassManager &FPM,
       ArrayRef<PassBuilder::PipelineElement>) {
      if (Name == "opaque-preds") {
        FPM.addPass(OpaquePredicates());
        return true;
      }
      return false;
    });
}