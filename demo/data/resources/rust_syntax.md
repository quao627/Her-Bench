# Rust 早期常用语法速查

> 来源：https://doc.rust-lang.org/book/ch03-01-variables-and-mutability.html ，https://doc.rust-lang.org/book/ch05-01-defining-structs.html ，https://doc.rust-lang.org/book/ch06-02-match.html ，https://doc.rust-lang.org/std/result/enum.Result.html ，https://doc.rust-lang.org/book/ch10-02-traits.html ，https://doc.rust-lang.org/book/ch04-03-slices.html

## 变量与可变性

`let` 声明的变量默认不可变，想改就得加 `mut`：

```rust
let x = 5;
// x = 6; // 编译错误
let mut y = 5;
y = 6; // 可以
```

同名变量可以用 `let` 重新声明一遍去遮蔽（shadowing）前一个，跟 `mut` 不是一回事——shadowing 甚至可以换类型，`mut` 不行。

## struct 和 enum

`struct` 把相关数据打包成一个类型：

```rust
struct User {
    name: String,
    age: u32,
}
let u = User { name: String::from("Ann"), age: 20 };
```

`enum` 定义"这个值只能是几种可能之一"，每个变体还能带数据，这点比很多语言的枚举强很多：

```rust
enum Shape {
    Circle(f64),
    Rectangle(f64, f64),
}
```

## match：穷尽性匹配

`match` 拿一个值去对一串模式，编译器要求所有可能情况都被覆盖，漏了会直接报错，这也是 Rust 少见运行时"漏判"bug 的原因之一：

```rust
match shape {
    Shape::Circle(r) => 3.14 * r * r,
    Shape::Rectangle(w, h) => w * h,
}
```

不想穷举所有分支，用 `_` 兜底：

```rust
match n {
    1 => println!("one"),
    _ => println!("other"),
}
```

只关心一种情况时，`if let` 比 `match` 简洁：

```rust
if let Some(v) = maybe_value {
    println!("{v}");
}
```

## Option 和 Result

Rust 没有 `null`，"可能没有值"用 `Option<T>` 表示：

```rust
enum Option<T> { Some(T), None }
```

"可能失败"用 `Result<T, E>` 表示：

```rust
enum Result<T, E> { Ok(T), Err(E) }
```

两者常用的取值方法：

- `unwrap()`：是 `Some`/`Ok` 就拿出里面的值，是 `None`/`Err` 就直接 panic，不带自定义信息。适合写练习题、写测试，图快。
- `expect("说明")`：跟 `unwrap` 一样，只是 panic 时会带上你写的说明文字，方便定位问题，正式代码里比裸 `unwrap` 更常见。
- `?` 运算符：写在返回类型也是 `Result`（或 `Option`）的函数里，遇到 `Err` 就直接把这个 `Err` 返回给调用者，不用手写 `match`：

```rust
fn read_num() -> Result<i32, std::num::ParseIntError> {
    let s = "42";
    let n: i32 = s.parse()?; // 失败就直接 return Err(..)
    Ok(n)
}
```

`?` 只能用在函数返回值是 `Result`/`Option` 的地方，这也是新手常踩的一个坑——在 `main` 或普通函数里用 `?` 会报"the `?` operator can only be used in a function that returns `Result` or `Option`"。

## trait 和泛型入门

`trait` 定义一组方法签名，描述"这个类型能做什么"：

```rust
trait Summary {
    fn summarize(&self) -> String;
}
impl Summary for User {
    fn summarize(&self) -> String { format!("{}", self.name) }
}
```

函数参数想接受"任何实现了某个 trait 的类型"，用 `impl Trait` 或者泛型加 trait bound，两种写法效果类似：

```rust
fn notify(item: &impl Summary) { println!("{}", item.summarize()); }
fn notify<T: Summary>(item: &T) { println!("{}", item.summarize()); }
```

泛型让同一段代码能处理多种类型，`<T>` 是最常见的写法，配合 trait bound（比如 `T: Summary`）限制 `T` 必须具备哪些能力，编译期就能检查出类型不满足要求的调用。

## String 与 &str

`String` 拥有所有权、数据在堆上、可以修改；`&str` 是借来的字符串切片，本身不可变，可能指向堆，也可能指向程序里写死的字符串字面量。写函数参数时优先用 `&str`，因为 `String` 和字符串字面量都能自动转成 `&str` 传进去，接受面更广：

```rust
fn greet(name: &str) -> String {
    format!("hi, {name}")
}
greet("Ann");                       // 字符串字面量，直接是 &str
greet(&String::from("Ann"));        // String 的引用，自动转成 &str
```
