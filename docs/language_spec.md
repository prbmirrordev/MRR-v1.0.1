# MRR Language Specification — Draft v0.1.0

## 1. Overview

MRR (Memory · Registers · Rings) is a systems programming language designed for
cyber-security research, exploit development, and Ring-0 kernel programming. It
combines syntax elements from C#, C++, Rust, and Ruby.

## 2. Lexical Elements

### 2.1 Comments
```mrr
// Line comment
/// Documentation comment
/* Block comment */
/** Doc block comment */
```

### 2.2 Identifiers
- Variables: `snake_case` (e.g., `my_var`, `buffer_size`)
- Types: `PascalCase` (e.g., `MyStruct`, `Config`)
- Constants: `SCREAMING_SNAKE` (e.g., `MAX_SIZE`)
- Modules: `snake_case` (e.g., `std::io`)

### 2.3 Literals
| Type | Examples |
|------|---------|
| Integer | `42`, `1_000_000` |
| Hex | `0xFF`, `0xDEADBEEF` |
| Binary | `0b1010_0110` |
| Octal | `0o777` |
| Float | `3.14`, `1.0e-5` |
| String | `"hello #{name}"` |
| Raw String | `r"no\escape"` |
| Byte String | `b"\x41\x42\x43"` |
| Char | `'A'` |
| Bool | `true`, `false` |
| Null | `null` |

### 2.4 String Interpolation
```mrr
let name = "MRR"
let msg = "Hello #{name}, you have #{count} items"
let hex = "Address: #{ptr:#018x}"  // Format specifiers
```

## 3. Type System

### 3.1 Primitive Types
| Type | Size | Description |
|------|------|-------------|
| `i8` .. `i128` | 1-16 bytes | Signed integers |
| `u8` .. `u128` | 1-16 bytes | Unsigned integers |
| `f32`, `f64` | 4, 8 bytes | IEEE 754 floats |
| `bool` | 1 byte | Boolean |
| `char` | 4 bytes | Unicode scalar |
| `byte` | 1 byte | Alias for `u8` |
| `usize`, `isize` | ptr-width | Pointer-sized integers |
| `str` | fat ptr | UTF-8 string |
| `ptr<T>` | ptr-width | Raw pointer to T |
| `void` | 0 bytes | Unit / no value |

### 3.2 Compound Types
```mrr
let arr: [i32]         = [1, 2, 3]        // Dynamic array
let fixed: [i32; 4]    = [1, 2, 3, 4]     // Fixed array
let tuple: (i32, str)  = (42, "hello")     // Tuple
let opt: Option<i32>   = Some(42)          // Optional
let res: Result<T, E>  = Ok(value)         // Result
```

## 4. Variables & Bindings

```mrr
let x = 42              // Immutable (Rust-style)
mut y = 0                // Mutable (MRR keyword)
const MAX: i32 = 1024    // Compile-time constant
static COUNT: u32 = 0    // Static storage
```

## 5. Functions

```mrr
fn add(a: i32, b: i32) -> i32 {
    a + b  // Implicit return (Ruby-style)
}

pub fn greet(name: str) {
    io::println("Hello #{name}")
}

// Unsafe function
unsafe fn deref_raw(p: ptr<i32>) -> i32 {
    p.read()
}

// Kernel function
kernel fn handle_irp(irp: ptr<void>) -> i32 { ... }
```

## 6. Control Flow

```mrr
// If / elif / else
if x > 10 {
    ...
} elif x > 5 {
    ...
} else {
    ...
}

// Match (pattern matching)
match value {
    0       => "zero",
    1..=10  => "small",
    n if n > 100 => "big: #{n}",
    _       => "other"
}

// Loops
for i in 0..10 { ... }
for item in collection { ... }
while condition { ... }
loop { ... break }
```

## 7. Structs, Traits & Impls

```mrr
#[repr(C)]
pub struct Buffer {
    pub data: ptr<byte>,
    pub size: usize,
    pub capacity: usize
}

pub trait Serializable {
    fn serialize(ref self) -> [byte]
    fn deserialize(data: [byte]) -> Self
}

impl Serializable for Buffer { ... }
impl Buffer {
    pub fn new(cap: usize) -> Buffer { ... }
}
```

## 8. Memory & Unsafe

```mrr
unsafe {
    let p: ptr<i32> = alloc(4)
    volatile p.write(42)
    let val = volatile p.read()
    drop(p)
}
```

## 9. Cyber-Security Constructs

### 9.1 Shellcode Blocks
```mrr
let sc = shellcode x86_64 { ... }
```

### 9.2 Inline Assembly
```mrr
asm { "mov rax, rbx" : "=a"(out) : "b"(in) : "rax" }
```

### 9.3 Driver Declarations
```mrr
driver MyDriver { fn driver_entry(...) -> i32 { ... } }
```

### 9.4 Exploit Modules
```mrr
exploit MyExploit { fn check() -> bool {...} fn payload() {...} }
```

### 9.5 Function Hooks
```mrr
hook NtCreateFile(type = "inline") { fn before(...) {...} }
```

### 9.6 Ring-0 Blocks
```mrr
ring0 { /* Privileged instructions */ }
```

## 10. Modules

```mrr
module my_module
use std::io
use std::mem::{alloc, free}
use crate::utils::*
```
