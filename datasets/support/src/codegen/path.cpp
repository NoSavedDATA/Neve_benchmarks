#include "../include.h"
extern "C" Value *batch_path(Parser_Struct *parser_struct, Function *TheFunction,
    std::string Callee, Data_Tree data_type, std::vector<Data_Tree> &args_type,
    Value *scope_struct, std::vector<std::unique_ptr<ExprAST>> &Args, std::vector<Value*> &ArgsV) {
    Value *ptr = callret("batch_path_C", {scope_struct});
    Value *value = UndefValue::get(struct_types["DT_str"]);
    value = Builder->CreateInsertValue(value, ptr, {0});
    Value *size = Builder->CreateIntCast(callret("strlen", {ptr}), struct_types["DT_str"]->getElementType(1), false);
    return Builder->CreateInsertValue(value, size, {1});
}
