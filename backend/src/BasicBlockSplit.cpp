#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Transforms/Utils/BasicBlockUtils.h"
#include <vector>

using namespace llvm;

namespace {

struct BasicBlockSplit : public PassInfoMixin<BasicBlockSplit> {
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
    if (F.isDeclaration() || F.size() < 2) 
      return PreservedAnalyses::all();

    bool changed = false;
    std::vector<BasicBlock*> blocksToSplit;

    for (auto &BB : F) {
      if (BB.size() > 4) {
        blocksToSplit.push_back(&BB);
      }
    }

    for (auto *BB : blocksToSplit) {
      changed |= splitBasicBlock(BB);
    }

    if (changed) {
      errs() << "🧱 BasicBlockSplit: Split " << blocksToSplit.size() 
             << " blocks in " << F.getName() << "\n";
      return PreservedAnalyses::none();
    }
    return PreservedAnalyses::all();
  }

private:
  bool splitBasicBlock(BasicBlock *BB) {
    size_t splitPoint = BB->size() / 3;
    if (splitPoint < 2) return false;

    auto it = BB->begin();
    for (size_t i = 0; i < splitPoint; ++i) {
      ++it;
    }

    if (it == BB->end()) return false;

    BasicBlock *newBB = SplitBlock(BB, &*it);
    newBB->setName(BB->getName() + "_split");

    if (BB->getTerminator()) {
      addBogusPhiNodes(BB, newBB);
    }

    return true;
  }

  void addBogusPhiNodes(BasicBlock *predBB, BasicBlock *targetBB) {
    if (targetBB->empty()) return;

    IRBuilder<> builder(&*targetBB->begin());
    PHINode *bogusPhi = builder.CreatePHI(builder.getInt32Ty(), 2, "bogus_phi");
    bogusPhi->addIncoming(builder.getInt32(0), predBB);
  }
};

} // anonymous namespace

void registerBasicBlockSplitPass(PassBuilder &PB) {
  PB.registerPipelineParsingCallback(
    [](StringRef Name, FunctionPassManager &FPM,
       ArrayRef<PassBuilder::PipelineElement>) {
      if (Name == "bbsplit") {
        FPM.addPass(BasicBlockSplit());
        return true;
      }
      return false;
    });
}