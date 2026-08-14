# Rust 所有权、借用与生命周期

> 来源：https://doc.rust-lang.org/book/ch04-01-what-is-ownership.html ，https://doc.rust-lang.org/book/ch04-02-references-and-borrowing.html ，https://doc.rust-lang.org/book/ch04-03-slices.html

## ownership 是什么

Rust 不用垃圾回收，也不让你手动 free，靠的是一套编译期规则，叫 ownership（所有权）。规则就三条：

1. 每个值都有一个变量是它的 owner。
2. 同一时刻只能有一个 owner。
3. owner 离开作用域，值就被自动 drop 掉。

栈上的简单类型（`i32`、`bool`、`char` 这些实现了 `Copy` trait 的类型）赋值时是直接复制一份，两个变量都能用。但像 `String`、`Vec` 这种数据在堆上的类型，赋值时发生的是 move（转移所有权），不是复制：

```rust
let s1 = String::from("hello");
let s2 = s1;        // s1 的所有权转移给 s2
// println!("{s1}"); // 编译错误，s1 已经失效了
```

编译器直接把 `s1` 标记成无效的，不是它还留着一份指针等你去踩坑。想要两份独立的数据，就显式调用 `.clone()`，这是深拷贝，会真的复制一份堆内存，开销要心里有数。

## 借用（borrowing）和引用规则

要用一个值但不想拿走它的所有权，就用引用（`&T` 不可变引用、`&mut T` 可变引用），这叫借用。规则是：同一时刻，要么有任意多个不可变引用，要么只能有一个可变引用，二者不能同时存在。这条规则是编译期强制的，目的是在编译阶段就堵死数据竞争，不用等到运行时。

## 常见报错怎么读

**`cannot borrow as mutable`（E0596 一类）**：你拿到的是不可变引用，却想改里面的数据。比如函数参数写的是 `&String`，函数体里却调用了会修改内容的方法。修法很直接：把参数或变量声明成可变的，传 `&mut` 进去。

```rust
fn change(s: &String) { s.push_str(", world"); } // 错，s 是不可变引用
fn change(s: &mut String) { s.push_str(", world"); } // 对，改成可变引用
```

**`cannot borrow ... as mutable more than once at a time`（E0499）**：同时创建了两个可变引用指向同一个变量。修法是让第一个可变引用的作用域先结束（用花括号包一下，或者用完就不再引用它），再创建第二个。

**`cannot borrow ... as mutable because it is also borrowed as immutable`（E0502）**：手上还有不可变引用没用完，就想再拿一个可变引用。常见场景是先 `let r1 = &s;` 打印用，后面又想 `&mut s`。修法是把不可变引用的最后一次使用放到可变引用创建之前，让不可变引用的生命周期先结束。

**`value borrowed here after move`（E0382）**：值已经被 move 走了，你还在用原来的变量。典型例子是把一个 `String` 或 `Vec` 赋给新变量或者传进一个按值接收的函数后，还想用旧变量。修法要么把 move 改成借用（传 `&s` 而不是 `s`），要么在 move 之前 `.clone()` 一份。

**返回悬垂引用（E0106，"missing lifetime specifier"）**：函数里创建了一个局部值，返回它的引用。局部值在函数结束时就被 drop 了，返回的引用会指向已经释放的内存，编译器直接拒绝。修法通常是直接返回值本身（把所有权转移出去），而不是返回引用。

## 生命周期（lifetimes）

生命周期标注（比如 `'a`）不是在创造新的作用域，而是告诉编译器几个引用之间的存活时间有什么关系，让编译器能验证返回的引用不会比它指向的数据活得更久：

```rust
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() { x } else { y }
}
```

这里 `'a` 表示返回值的生命周期不会超过 `x` 和 `y` 中较短的那个，避免调用者拿到一个可能失效的引用。日常写代码时，大多数场景编译器能自动推断（elision），只有像上面这种返回值可能来自多个输入引用的情况才需要手写标注。

## String 与 &str 的关系（顺带一提）

之所以会有那么多借用相关的报错，很多时候和 `String`（拥有所有权，堆上分配）与 `&str`（借用来的字符串切片）混着用有关。函数参数尽量写成 `&str`，接受面更广，`String` 和字符串字面量都能传进去，也不会牵扯出多余的所有权问题。
