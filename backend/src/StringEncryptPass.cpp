#include "llvm/IR/PassManager.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Passes/PassBuilder.h"
#include <random>
#include <vector>

using namespace llvm;

namespace {

struct StringEncryptPass : PassInfoMixin<StringEncryptPass> {
    StringEncryptPass(unsigned seed = 0) : RNG(seed ? seed : 0xC0FFEE) {}

    PreservedAnalyses run(Module &M, ModuleAnalysisManager &) {
        LLVMContext &Ctx = M.getContext();
        std::vector<GlobalVariable*> targets;
        std::vector<uint8_t> keys;
        std::vector<std::string> encryptedStrings;

        for (GlobalVariable &G : M.globals()) {
            if (!G.hasInitializer()) continue;
            if (ConstantDataArray *cda = dyn_cast<ConstantDataArray>(G.getInitializer())) {
                if (cda->isString()) {
                    targets.push_back(&G);
                    StringRef str = cda->getAsString();
                    encryptedStrings.push_back(str.str());
                }
            }
        }

        if (targets.empty()) {
            errs() << "{\"pass\": \"stringenc\", \"strings_encrypted\": 0, \"encrypted_strings\": []}\n";
            return PreservedAnalyses::all();
        }

        for (GlobalVariable *G : targets) {
            ConstantDataArray *cda = cast<ConstantDataArray>(G->getInitializer());
            unsigned origLen = cda->getNumElements();
            std::vector<Constant*> elems;

            uint8_t key = (uint8_t)(RNG() & 0xFF);
            keys.push_back(key);

            for (unsigned i = 0; i < origLen; ++i) {
                uint8_t b = (uint8_t)cda->getElementAsInteger(i);
                elems.push_back(ConstantInt::get(Type::getInt8Ty(Ctx), b ^ key));
            }

            ArrayType *arrTy = ArrayType::get(Type::getInt8Ty(Ctx), elems.size());
            G->setInitializer(ConstantArray::get(arrTy, elems));
            G->setConstant(false);
        }

        if (!targets.empty()) {
            Function *ctor = createDecryptCtor(M, targets, keys);
            appendToGlobalCtors(M, ctor, 65535);
        }

        errs() << "{\"pass\": \"stringenc\", \"strings_encrypted\": " << targets.size();
        errs() << ", \"encrypted_strings\": [";
        for (size_t i = 0; i < encryptedStrings.size(); ++i) {
            if (i > 0) errs() << ", ";
            std::string escaped;
            for (char c : encryptedStrings[i]) {
                if (c == '"') escaped += "\\\"";
                else if (c == '\\') escaped += "\\\\";
                else if (c == '\n') escaped += "\\n";
                else if (c == '\t') escaped += "\\t";
                else if (c >= 32 && c <= 126) escaped += c;
                else {
                    char buf[5];
                    snprintf(buf, sizeof(buf), "\\u%04x", (unsigned char)c);
                    escaped += buf;
                }
            }
            errs() << "\"" << escaped << "\"";
        }
        errs() << "]";
        errs() << ", \"keys\": [";
        for (size_t i = 0; i < keys.size(); ++i) {
            if (i > 0) errs() << ", ";
            errs() << (unsigned)keys[i];
        }
        errs() << "]";
        errs() << "}\n";

        return PreservedAnalyses::all();
    }

private:
    std::mt19937 RNG;

    Function* createDecryptCtor(Module &M, const std::vector<GlobalVariable*>& globals, const std::vector<uint8_t>& keys) {
        LLVMContext &Ctx = M.getContext();
        FunctionType *fnTy = FunctionType::get(Type::getVoidTy(Ctx), false);
        Function *F = Function::Create(fnTy, Function::InternalLinkage, "__obf_decrypt_init", &M);
        
        BasicBlock *entry = BasicBlock::Create(Ctx, "entry", F);
        IRBuilder<> B(entry);

        for (size_t gi = 0; gi < globals.size(); ++gi) {
            GlobalVariable *G = globals[gi];
            uint8_t key = keys[gi];
            
            ArrayType *at = cast<ArrayType>(G->getValueType());
            uint64_t len = at->getNumElements();

            BasicBlock *loopHeader = BasicBlock::Create(Ctx, "loop.header", F);
            BasicBlock *loopBody = BasicBlock::Create(Ctx, "loop.body", F);
            BasicBlock *loopEnd = BasicBlock::Create(Ctx, "loop.end", F);

            AllocaInst *counter = B.CreateAlloca(Type::getInt32Ty(Ctx), nullptr, "counter");
            B.CreateStore(ConstantInt::get(Type::getInt32Ty(Ctx), 0), counter);
            B.CreateBr(loopHeader);

            B.SetInsertPoint(loopHeader);
            Value *currentIdx = B.CreateLoad(Type::getInt32Ty(Ctx), counter, "idx");
            Value *cond = B.CreateICmpULT(currentIdx, 
                                        ConstantInt::get(Type::getInt32Ty(Ctx), len), 
                                        "loop.cond");
            B.CreateCondBr(cond, loopBody, loopEnd);

            B.SetInsertPoint(loopBody);
            Value *zero = ConstantInt::get(Type::getInt32Ty(Ctx), 0);
            Value *gep = B.CreateInBoundsGEP(G->getValueType(), G, {zero, currentIdx}, "elem.ptr");
            Value *encryptedByte = B.CreateLoad(Type::getInt8Ty(Ctx), gep, "encrypted");
            Value *decryptedByte = B.CreateXor(encryptedByte, 
                                            ConstantInt::get(Type::getInt8Ty(Ctx), key),
                                            "decrypted");
            B.CreateStore(decryptedByte, gep);
            
            Value *nextIdx = B.CreateAdd(currentIdx, 
                                       ConstantInt::get(Type::getInt32Ty(Ctx), 1),
                                       "next.idx");
            B.CreateStore(nextIdx, counter);
            B.CreateBr(loopHeader);

            B.SetInsertPoint(loopEnd);
        }

        B.CreateRetVoid();
        return F;
    }

    void appendToGlobalCtors(Module &M, Function *ctor, int priority) {
      LLVMContext &Ctx = M.getContext();
    
      StructType *elemTy = StructType::get(
          Type::getInt32Ty(Ctx),
          PointerType::get(Ctx, 0),
          PointerType::get(Ctx, 0)
      );
    
      Constant *entry = ConstantStruct::get(elemTy,
          ConstantInt::get(Type::getInt32Ty(Ctx), priority),
          ConstantExpr::getBitCast(ctor, PointerType::get(Ctx, 0)),
          Constant::getNullValue(PointerType::get(Ctx, 0))
      );
    
      GlobalVariable *GV = M.getNamedGlobal("llvm.global_ctors");
      if (!GV) {
          ArrayType *arrTy = ArrayType::get(elemTy, 1);
          GV = new GlobalVariable(M, arrTy, false, GlobalValue::AppendingLinkage, 
                                  ConstantArray::get(arrTy, entry), "llvm.global_ctors");
      } else {
          ConstantArray *CA = dyn_cast<ConstantArray>(GV->getInitializer());
          if (!CA) return;
          std::vector<Constant*> elems;
          for (unsigned i = 0; i < CA->getType()->getNumElements(); ++i) 
              elems.push_back(CA->getOperand(i));
          elems.push_back(entry);
          ArrayType *newArrTy = ArrayType::get(elemTy, elems.size());
          GV->setInitializer(ConstantArray::get(newArrTy, elems));
      }
  }
};

} // namespace

void registerStringEncryptPass(PassBuilder &PB) {
    PB.registerPipelineParsingCallback(
        [](StringRef name, ModulePassManager &MPM, ArrayRef<PassBuilder::PipelineElement>) {
            if (name == "stringenc") {
                MPM.addPass(StringEncryptPass());
                return true;
            }
            return false;
        });
}