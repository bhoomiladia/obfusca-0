#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/Instructions.h"
#include "llvm/IR/PassManager.h"
#include "llvm/Passes/PassBuilder.h"
#include "llvm/Support/raw_ostream.h"
#include <random>

using namespace llvm;

namespace {

struct DynamicXORPass : public PassInfoMixin<DynamicXORPass> {
  PreservedAnalyses run(Function &F, FunctionAnalysisManager &AM) {
    if (F.getName().starts_with("__obf_")) 
      return PreservedAnalyses::all();

    bool changed = false;
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(1, 255);

    for (auto &BB : F) {
      for (auto &I : BB) {
        if (auto *store = dyn_cast<StoreInst>(&I)) {
          if (shouldObfuscateStore(store)) {
            changed |= obfuscateStore(store, dis(gen));
          }
        } else if (auto *load = dyn_cast<LoadInst>(&I)) {
          if (shouldObfuscateLoad(load)) {
            changed |= obfuscateLoad(load, dis(gen));
          }
        }
      }
    }

    if (changed) {
      errs() << "🔀 DynamicXOR: Obfuscated " << F.getName() << "\n";
      return PreservedAnalyses::none();
    }
    return PreservedAnalyses::all();
  }

private:
  bool shouldObfuscateStore(StoreInst *store) {
    return isa<GlobalVariable>(store->getPointerOperand()) ||
           store->getValueOperand()->getType()->isArrayTy();
  }

  bool shouldObfuscateLoad(LoadInst *load) {
    return isa<GlobalVariable>(load->getPointerOperand()) ||
           load->getType()->isArrayTy();
  }

  bool obfuscateStore(StoreInst *store, int key) {
    IRBuilder<> builder(store);
    Value *originalValue = store->getValueOperand();
    
    Value *dynamicKey = builder.getInt32(key);
    Value *addrHash = builder.getInt32((intptr_t)store & 0xFFFF);
    Value *finalKey = builder.CreateXor(dynamicKey, addrHash);
    
    Value *encrypted = builder.CreateXor(originalValue, finalKey);
    builder.CreateStore(encrypted, store->getPointerOperand());
    
    store->eraseFromParent();
    return true;
  }

  bool obfuscateLoad(LoadInst *load, int key) {
    IRBuilder<> builder(load);
    
    Value *dynamicKey = builder.getInt32(key);
    Value *addrHash = builder.getInt32((intptr_t)load & 0xFFFF);
    Value *finalKey = builder.CreateXor(dynamicKey, addrHash);
    
    Value *encrypted = builder.CreateLoad(load->getType(), load->getPointerOperand());
    Value *decrypted = builder.CreateXor(encrypted, finalKey);
    
    load->replaceAllUsesWith(decrypted);
    load->eraseFromParent();
    return true;
  }
};

} // anonymous namespace

// Registration function instead of llvmGetPassPluginInfo
void registerDynamicXORPass(PassBuilder &PB) {
  PB.registerPipelineParsingCallback(
    [](StringRef Name, FunctionPassManager &FPM,
       ArrayRef<PassBuilder::PipelineElement>) {
      if (Name == "dynamic-xor") {
        FPM.addPass(DynamicXORPass());
        return true;
      }
      return false;
    });
}