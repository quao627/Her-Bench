# cargo 基础命令与 exercism 练习流程

> 来源：https://doc.rust-lang.org/cargo/guide/creating-a-new-project.html ，https://exercism.org/docs/tracks/rust/tests ，https://github.com/exercism/rust/blob/main/docs/TESTS.md

## cargo 基础命令

`cargo` 是 Rust 的包管理工具兼构建工具，日常写代码基本靠它就够了。

- `cargo new 项目名`：新建一个项目，默认是二进制项目（带 `src/main.rs`），加 `--lib` 就是库项目（`src/lib.rs`）。生成的目录里 `Cargo.toml` 是项目配置文件，写依赖和元信息。
- `cargo build`：编译项目，产物在 `target/debug/`。默认是 debug 模式，编译快但跑起来慢；加 `--release` 是发布模式，编译慢一些但运行快，产物在 `target/release/`。
- `cargo run`：编译加运行一步到位，日常写练习题基本都用这个，不用自己去 `target/debug/` 底下找可执行文件。
- `cargo test`：跑项目里所有的测试用例，函数上标了 `#[test]` 的都会被执行，输出里能看到哪些过了哪些没过。

## exercism.io 的练习流程

exercism 上的 Rust 练习一般是给你一个骨架项目，`src/lib.rs` 里放你要实现的函数，`tests/` 目录下已经写好了测试。基本流程是个循环：

1. 打开 `src/lib.rs`，把要实现的函数或类型写上（一开始往往是空的或者只有签名）。
2. 跑 `cargo test`，看测试结果。
3. 大部分练习默认只开着第一个测试，后面的测试函数上带着 `#[ignore]`。一个测试过了，就去测试文件里把下一个 `#[ignore]` 删掉，让下一个测试跑起来。
4. 看报错信息改代码。测试失败的输出（包括前面提到的那些借用检查器报错）会直接告诉你哪里不对，照着报错改，不用一次性把整个功能都想清楚，够用就行，测试会一步步把你引导到完整实现。
5. 反复 2-4，直到 `cargo test` 全绿。
6. 想提交，用 exercism 官方 CLI 跑 `exercism submit src/lib.rs`（如果用了外部 crate，把 `Cargo.toml` 也一起提交），命令会把解答传到 exercism 网站，并打印出解答页面的链接。

这个"改代码 → `cargo test` → 看报错 → 改代码"的循环基本就是 Rust 早期练习的日常节奏，借着编译器和测试的报错一步步逼近正确实现，比自己空想代码该怎么写要踏实。
