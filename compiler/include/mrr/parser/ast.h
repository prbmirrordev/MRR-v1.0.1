/*
 * MRR Compiler — Abstract Syntax Tree Definitions
 *
 * The AST represents the syntactic structure of MRR source code.
 * Nodes are organized hierarchically:
 *
 *   ASTNode (base)
 *   ├── Expression
 *   │   ├── LiteralExpr (int, float, string, bool, hex, bytes)
 *   │   ├── IdentifierExpr
 *   │   ├── BinaryExpr
 *   │   ├── UnaryExpr
 *   │   ├── CallExpr
 *   │   ├── MemberAccessExpr
 *   │   ├── IndexExpr
 *   │   ├── CastExpr
 *   │   ├── AsmExpr (inline assembly)
 *   │   ├── SyscallExpr
 *   │   ├── ShellcodeExpr
 *   │   └── PointerExpr (raw ptr operations)
 *   ├── Statement
 *   │   ├── VarDeclStmt (let / mut)
 *   │   ├── AssignStmt
 *   │   ├── ReturnStmt
 *   │   ├── IfStmt
 *   │   ├── MatchStmt
 *   │   ├── ForStmt
 *   │   ├── WhileStmt
 *   │   ├── LoopStmt
 *   │   ├── BlockStmt
 *   │   ├── ExprStmt
 *   │   ├── UnsafeStmt
 *   │   ├── DeferStmt
 *   │   └── BreakStmt / ContinueStmt
 *   └── Declaration
 *       ├── FunctionDecl
 *       ├── StructDecl
 *       ├── EnumDecl
 *       ├── TraitDecl
 *       ├── ImplDecl
 *       ├── ModuleDecl
 *       ├── UseDecl
 *       ├── DriverDecl (Ring-0 driver entry)
 *       ├── InterruptDecl
 *       ├── HookDecl
 *       └── ExploitDecl
 */

#pragma once

#include "mrr/lexer/token.h"
#include <memory>
#include <string>
#include <vector>
#include <optional>
#include <variant>

namespace mrr {
namespace ast {

// ─── Forward Declarations ───
struct Expression;
struct Statement;
struct Declaration;

using ExprPtr  = std::unique_ptr<Expression>;
using StmtPtr  = std::unique_ptr<Statement>;
using DeclPtr  = std::unique_ptr<Declaration>;

// ─── Type Representation ───
struct TypeRef {
    std::string              name;           // e.g., "i32", "ptr", "MyStruct"
    bool                     is_pointer = false;
    bool                     is_ref     = false;
    bool                     is_mut     = false;
    bool                     is_raw     = false;
    bool                     is_volatile = false;
    std::optional<uint32_t>  alignment;
    std::unique_ptr<TypeRef> inner;          // For ptr<T>, ref<T>

    SourceLocation           location;
};

// ─── AST Node Base ───
struct ASTNode {
    SourceLocation location;
    virtual ~ASTNode() = default;
};

// ═══════════════════════════════════════
// ─── EXPRESSIONS ──────────────────────
// ═══════════════════════════════════════

enum class ExprKind {
    Literal, Identifier, Binary, Unary, Call, MemberAccess,
    Index, Cast, Asm, Syscall, Shellcode, Pointer, Block,
    If, Match, Lambda, SizeOf, AlignOf, AddressOf, Deref
};

struct Expression : ASTNode {
    ExprKind expr_kind;
    explicit Expression(ExprKind k) : expr_kind(k) {}
};

// ── Literal Expression ──
enum class LiteralKind {
    Integer, UnsignedInteger, Float, String, Char,
    Bool, HexBytes, RawString, Null
};

struct LiteralExpr : Expression {
    LiteralKind literal_kind;
    std::string raw_value;

    LiteralExpr() : Expression(ExprKind::Literal) {}
};

// ── Identifier Expression ──
struct IdentifierExpr : Expression {
    std::string name;
    std::vector<std::string> path;  // For module::path::ident

    IdentifierExpr() : Expression(ExprKind::Identifier) {}
};

// ── Binary Expression ──
struct BinaryExpr : Expression {
    TokenKind op;
    ExprPtr   left;
    ExprPtr   right;

    BinaryExpr() : Expression(ExprKind::Binary) {}
};

// ── Unary Expression ──
struct UnaryExpr : Expression {
    TokenKind op;
    ExprPtr   operand;
    bool      is_prefix = true;

    UnaryExpr() : Expression(ExprKind::Unary) {}
};

// ── Call Expression ──
struct CallExpr : Expression {
    ExprPtr              callee;
    std::vector<ExprPtr> arguments;

    CallExpr() : Expression(ExprKind::Call) {}
};

// ── Member Access Expression (a.b or a->b) ──
struct MemberAccessExpr : Expression {
    ExprPtr     object;
    std::string member;
    bool        is_arrow = false;  // -> vs .

    MemberAccessExpr() : Expression(ExprKind::MemberAccess) {}
};

// ── Index Expression (a[i]) ──
struct IndexExpr : Expression {
    ExprPtr object;
    ExprPtr index;

    IndexExpr() : Expression(ExprKind::Index) {}
};

// ── Cast Expression (expr as Type) ──
struct CastExpr : Expression {
    ExprPtr  operand;
    TypeRef  target_type;

    CastExpr() : Expression(ExprKind::Cast) {}
};

// ── Inline Assembly Expression ──
struct AsmExpr : Expression {
    std::string                            assembly_code;
    std::vector<std::string>               outputs;
    std::vector<std::string>               inputs;
    std::vector<std::string>               clobbers;
    bool                                   is_volatile = true;

    AsmExpr() : Expression(ExprKind::Asm) {}
};

// ── Syscall Expression ──
struct SyscallExpr : Expression {
    ExprPtr              syscall_number;
    std::vector<ExprPtr> args;

    SyscallExpr() : Expression(ExprKind::Syscall) {}
};

// ── Shellcode Expression ──
struct ShellcodeExpr : Expression {
    std::vector<uint8_t>  bytes;
    std::string           raw_hex;
    std::string           target_arch;    // "x86_64", "arm64"

    ShellcodeExpr() : Expression(ExprKind::Shellcode) {}
};

// ═══════════════════════════════════════
// ─── STATEMENTS ───────────────────────
// ═══════════════════════════════════════

enum class StmtKind {
    VarDecl, Assign, Return, If, Match, For, While,
    Loop, Block, Expr, Unsafe, Defer, Break, Continue
};

struct Statement : ASTNode {
    StmtKind stmt_kind;
    explicit Statement(StmtKind k) : stmt_kind(k) {}
};

// ── Variable Declaration (let / mut) ──
struct VarDeclStmt : Statement {
    std::string           name;
    std::optional<TypeRef> type;          // Optional type annotation
    ExprPtr               initializer;    // Optional initializer
    bool                  is_mutable = false;
    bool                  is_static  = false;
    bool                  is_const   = false;

    VarDeclStmt() : Statement(StmtKind::VarDecl) {}
};

// ── Block Statement ──
struct BlockStmt : Statement {
    std::vector<StmtPtr> statements;
    bool                 is_unsafe = false;

    BlockStmt() : Statement(StmtKind::Block) {}
};

// ── If Statement ──
struct IfStmt : Statement {
    ExprPtr  condition;
    StmtPtr  then_branch;
    StmtPtr  else_branch;  // nullable

    IfStmt() : Statement(StmtKind::If) {}
};

// ── Return Statement ──
struct ReturnStmt : Statement {
    ExprPtr value;  // nullable

    ReturnStmt() : Statement(StmtKind::Return) {}
};

// ── Expression Statement ──
struct ExprStmt : Statement {
    ExprPtr expression;

    ExprStmt() : Statement(StmtKind::Expr) {}
};

// ── Unsafe Block Statement ──
struct UnsafeStmt : Statement {
    StmtPtr body;

    UnsafeStmt() : Statement(StmtKind::Unsafe) {}
};

// ═══════════════════════════════════════
// ─── DECLARATIONS ─────────────────────
// ═══════════════════════════════════════

enum class DeclKind {
    Function, Struct, Enum, Trait, Impl, Module,
    Use, Driver, Interrupt, Hook, Exploit
};

struct Declaration : ASTNode {
    DeclKind    decl_kind;
    bool        is_pub = false;
    std::string doc_comment;

    explicit Declaration(DeclKind k) : decl_kind(k) {}
};

// ── Function Parameter ──
struct FnParam {
    std::string name;
    TypeRef     type;
    bool        is_mut = false;
    ExprPtr     default_value;  // nullable
};

// ── Function Declaration ──
struct FunctionDecl : Declaration {
    std::string              name;
    std::vector<FnParam>     params;
    std::optional<TypeRef>   return_type;
    StmtPtr                  body;          // BlockStmt
    bool                     is_unsafe = false;
    bool                     is_kernel = false;
    bool                     is_extern = false;
    std::string              calling_conv;  // "", "cdecl", "stdcall", "fastcall"

    FunctionDecl() : Declaration(DeclKind::Function) {}
};

// ── Struct Declaration ──
struct StructField {
    std::string name;
    TypeRef     type;
    bool        is_pub = false;
};

struct StructDecl : Declaration {
    std::string              name;
    std::vector<StructField> fields;
    std::optional<uint32_t>  alignment;     // #[align(N)]
    bool                     is_packed = false;
    bool                     is_repr_c = false;

    StructDecl() : Declaration(DeclKind::Struct) {}
};

// ── Trait Declaration ──
struct TraitDecl : Declaration {
    std::string          name;
    std::vector<DeclPtr> methods;

    TraitDecl() : Declaration(DeclKind::Trait) {}
};

// ── Impl Declaration ──
struct ImplDecl : Declaration {
    std::string              type_name;
    std::optional<std::string> trait_name;
    std::vector<DeclPtr>     methods;

    ImplDecl() : Declaration(DeclKind::Impl) {}
};

// ── Driver Declaration (Ring-0) ──
struct DriverDecl : Declaration {
    std::string  name;
    StmtPtr      init_body;     // driver_entry
    StmtPtr      cleanup_body;  // driver_unload
    std::vector<DeclPtr> irp_handlers;

    DriverDecl() : Declaration(DeclKind::Driver) {}
};

// ── Exploit Module Declaration ──
struct ExploitDecl : Declaration {
    std::string              name;
    std::string              target_info;
    std::string              author;
    std::string              description;
    StmtPtr                  payload;
    StmtPtr                  check_fn;
    StmtPtr                  exploit_fn;

    ExploitDecl() : Declaration(DeclKind::Exploit) {}
};

// ── Hook Declaration ──
struct HookDecl : Declaration {
    std::string  target_function;
    std::string  hook_type;       // "inline", "iat", "eat", "ssdt"
    StmtPtr      body;

    HookDecl() : Declaration(DeclKind::Hook) {}
};

// ═══════════════════════════════════════
// ─── PROGRAM (Top-level) ─────────────
// ═══════════════════════════════════════

struct Program : ASTNode {
    std::string              module_name;
    std::vector<DeclPtr>     declarations;
    std::vector<Diagnostic>  diagnostics;
};

} // namespace ast
} // namespace mrr
