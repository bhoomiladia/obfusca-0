#include "llvm/IR/PassManager.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Passes/PassBuilder.h"
#include <random>

using namespace llvm;

namespace {

struct BogusInstructionsPass : PassInfoMixin<BogusInstructionsPass> {
  BogusInstructionsPass(unsigned seed = 0) : RNG(seed ? seed : 0xC0FFEE) {}

  PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
      unsigned bogusCount = 0;
      LLVMContext &Ctx = M.getContext();
      
      for (Function &F : M) {
          if (F.isDeclaration()) continue;
          
          for (BasicBlock &BB : F) {
              if (BB.empty()) continue;
              
              Instruction *insertPoint = nullptr;
              for (Instruction &I : BB) {
                  if (!I.isTerminator()) {
                      insertPoint = &I;
                      break;
                  }
              }
              if (!insertPoint) continue;
              
              IRBuilder<> B(insertPoint);
              
              if (insertBogusArithmetic(B, Ctx)) bogusCount++;
              if (insertBogusMemory(B, Ctx, &F)) bogusCount++;
          }
      }

      errs() << "{\"pass\": \"bogus-instructions\", \"bogus_instr_count\": " << bogusCount << "}\n";
      
      return PreservedAnalyses::all();
  }

private:
  std::mt19937 RNG;
  
  bool insertBogusArithmetic(IRBuilder<> &B, LLVMContext &Ctx) {
      try {
          Value *val1 = ConstantInt::get(Type::getInt32Ty(Ctx), RNG() % 1000 + 1);
          Value *val2 = ConstantInt::get(Type::getInt32Ty(Ctx), RNG() % 1000 + 1);
          
          Value *bogusAdd = B.CreateAdd(val1, val2, "bogus_add");
          Value *bogusMul = B.CreateMul(bogusAdd, val2, "bogus_mul");
          Value *bogusSub = B.CreateSub(bogusMul, val1, "bogus_sub");
          
          Value *xorVal = ConstantInt::get(Type::getInt32Ty(Ctx), RNG() % 1000 + 1);
          B.CreateXor(bogusSub, xorVal, "bogus_xor");
          
          return true;
      } catch (...) {
          return false;
      }
  }
  
  bool insertBogusMemory(IRBuilder<> &B, LLVMContext &Ctx, Function *F) {
      try {
          AllocaInst *bogusAlloca = B.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "bogus_alloca");
          
          Value *bogusVal = ConstantInt::get(Type::getInt32Ty(Ctx), RNG() % 1000 + 1);
          B.CreateStore(bogusVal, bogusAlloca);
          
          Value *bogusLoad = B.CreateLoad(Type::getInt32Ty(Ctx), bogusAlloca, "bogus_load");
          B.CreateAdd(bogusLoad, ConstantInt::get(Type::getInt32Ty(Ctx), 42), "bogus_calc");
          
          return true;
      } catch (...) {
          return false;
      }
  }
};

} // namespace

void registerBogusInstructionsPass(PassBuilder &PB) {
    PB.registerPipelineParsingCallback(
        [](StringRef name, ModulePassManager &MPM, ArrayRef<PassBuilder::PipelineElement>) {
            if (name == "bogus-instructions") {
                MPM.addPass(BogusInstructionsPass());
                return true;
            }
            return false;
        });
}