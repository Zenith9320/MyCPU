# Assassyn 关键点笔记

## 项目概述

Assassyn 是一个下一代硬件敏捷设计和实现项目，通过提供仿真和 RTL 生成的统一接口来简化硬件开发流程。

### 项目结构
- `developer/`: 开发者指南，包括人类或 AI 代理贡献项目的指导
- `imag/`: 文档中嵌入的图像
- `design/`: Assassyn 生成架构的高级设计决策
- `vm/`: 虚拟机相关文档

## 架构设计

### 核心架构模型
Assassyn 采用基于信用(credit)的流水线阶段架构：
- 当架构有待处理的激活时，获得一个信用
- 成功激活后，消耗一个信用
- 架构从前一阶段的 FIFO 接受数据

### 跨阶段组合通信
基于信用的流水线阶段可以有组合引脚连接到下游模块，下游模块可以递归连接到其他下游模块或其他流水线阶段。

### 执行模型

#### 驱动模块
- `Driver` 是一个特殊的模块，作为流水线阶段
- 类似于软件中的"main"函数，充当 Verilog 系统的"时钟"
- 每个周期无条件激活以执行内部逻辑并驱动后续阶段

#### 阶段间顺序通信
- 当 `Driver` 使用异步调用激活另一个阶段时发生
- 采用基于信用的流控制机制
- 阶段寄存器实现为 FIFO 模板

#### 阶段间组合通信
- 通过组合连接实现跨模块同周期通信
- 数据可以在同一周期内从多个源到达目标模块

## 内存系统

### SRAM
- 模拟 ASAP7 的独占单读写 SRAM 行为
- 具有一个周期的读取延迟
- 作为下游模块处理

### DRAM
- 依赖 Ramulator2 模拟内存系统
- 具有可变延迟
- 提供两个内部函数检查内存请求是否返回
- 当前限制：没有 LSQ 内存顺序强制

## 语言设计

### DSL 抽象
Assassyn 采用基于跟踪的 DSL，所有在跟踪范围内完成的操作都被重载。例如，`a + b` 不会计算加法结果，而是创建一个 `Add` 节点。

### 命名系统
基于跟踪的前端与基于解析器的前端之间的关键权衡是变量命名。大多数运算符可以重载，但左值赋值 `a = b` 无法重载，因为它会改变 Python 全局环境。

### 插入点
Assassyn 提供两个装饰器来注释函数作为跟踪的入口点：
- `@module.combinational`
- `@downstream.combinational`

### 条件处理
使用 `Condition(xxx)` 在跟踪式 DSL 中注入条件块，在进入此 `with` 上下文时在 AST 中注入条件块。

## 内置函数

### 执行控制内置函数
- `push_condition(condition)` / `pop_condition()`: 管理保护后续操作的谓词栈
- `get_pred()`: 返回当前谓词（所有活动条件的 AND）
- `log(fmt, *values)`: 发出受当前谓词保护的格式化跟踪消息
- `wait_until(condition)`: 阻塞执行直到条件变为真
- `finish()`: 终止模拟
- `assume(condition)`: 断言条件为真

### 内存内置函数
- `send_read_request(memory, read_enable, address)`: 向内存发送读取请求
- `send_write_request(memory, write_enable, address, data)`: 向内存发送写入请求
- `has_mem_resp(memory)`: 检查内存是否有待处理响应
- `get_mem_resp(memory)`: 获取内存响应数据

### 系统状态内置函数
- `fifo_valid(fifo)`: 检查 FIFO 是否有有效数据
- `fifo_peek(fifo)`: 查看 FIFO 数据而不消耗
- `module_triggered(module)`: 检查模块是否在此周期触发
- `value_valid(value)`: 检查值是否有效
- `current_cycle()`: 获取当前全局周期计数

## 数据类型系统

### 基本数据类型
- `UInt(bits)`: 无符号整数，范围 0 到 2^bits - 1
- `Int(bits)`: 有符号整数，使用二进制补码表示
- `Bits(bits)`: 原始位向量，无算术解释
- `Float()`: 32 位浮点数，使用 IEEE 754 标准
- `void()`: void/单元类型，用于没有返回值的函数

### 复合数据类型
- `ArrayType(dtype, size)`: 同质元素的固定大小数组
- `Record(*args, **kwargs)`: 具有命名字段和可配置位布局的结构化数据类型

### 操作结果类型
- 算术操作：根据操作数类型和位宽确定结果类型
- 位操作：通常返回 `Bits` 类型
- 比较操作：返回 `Bits(1)` 类型
- 类型转换：支持位转换、零扩展、符号扩展等

## 内部实现

### 数组所有权模型
- 每个 IR 数组暴露一个 `owner` 属性，指向负责存储的运行时对象
- 寄存器数组：系统范围内实例化的数组 `owner = None`，模块内创建的数组存储对该模块的引用
- 内存支持的数组：内存构造函数将其内部数组的 `owner` 设置为 `self`

### 构建系统架构
- 物理机与 VM 构建分离
- 补丁管理系统：在物理机上应用补丁，避免路径不匹配问题
- 构建目标依赖关系：确保补丁在构建前应用
- 缓存管理：包括补丁文件、构建工件、子模块哈希等

### 类型强制系统
- `@enforce_type` 装饰器实现了 Assassyn Python 前端的运行时类型系统
- 提供编译时类似的类型安全性
- 采用"选择性加入"模型，允许函数逐步迁移到使用类型强制
- 零开销设计：当类型正确时，装饰器具有零性能影响

### 命名系统设计
- 提供语义命名以实现可读的代码生成和调试
- 结合 AST 重写、面向类型的命名和分层上下文管理
- 核心组件：
  - `NamingManager`: 中央协调器
  - `TypeOrientedNamer`: 基于 IR 节点类型和操作生成语义名称
  - `UniqueNameCache`: 通过基于计数器的后缀确保名称唯一性
  - AST 重写系统：拦截 Python 赋值以启用语义命名

### Verilog 流水线生成
- 实现基于信用的流水线架构
- 分析预传递：在发出任何 Verilog 之前执行元数据预传递
- 信用流控制实现：使用计数器和控制逻辑
- 阶段 FIFO 实现：使用 FIFO 模板实现阶段寄存器
- 组合下游模块：实现为纯组合逻辑
- 寄存器数组实现：支持多端口并发访问模式

### Rust 模拟器
- 生成 Rust 代码以协调模拟
- 模拟器上下文包含全局时间戳、寄存器数组、模块簿记、暴露值和 DRAM 接口
- 模拟方法包括通用方法、每模块调用器和模拟器主机
- 使用半"周期滴答"机制模拟硬件的边沿触发行为

## 外部 SystemVerilog 支持

### ExternalSV 概述
- 在 Assassyn 系统内无缝对接已有的 SystemVerilog 模块
- `ExternalSV` 继承自 `Downstream`，通过 `@external` 装饰器与 `WireIn` / `WireOut` / `RegOut` 注解描述模块边界
- 输入连接通过 `ExternalIntrinsic` 的参数完成，输出读取由 `PureIntrinsic(EXTERNAL_OUTPUT_READ)` 表示

### Verilog 生成
- 基于 ExternalSV 声明生成 PyCDE wrapper
- 在 Top Harness 中区分 ExternalSV 与普通模块
- 每个 external 模块都会被一个 downstream_wrapper 封装接口

### 模拟器支持
- 收集对外可见的表达式，生成模拟器所需的缓存与调度信息
- 为每个 ExternalSV 创建独立 Verilator FFI crate
- 生成的 Rust 代码会为组合模块在读出前自动调用 `eval()`，对时序模块使用 `clock_tick()`

## 开发指南

### 代码格式
- Rust 代码：使用 `cargo fmt` 格式化，使用 `cargo clippy` 进行静态分析
- Python 代码：使用 Pylint 检查格式

### Git 提交消息格式
```
[tag] Summarize your changes.
[path/to/file1] Describe the changes to file1.
[path/to/file2] Describe the changes to file2.
Optionally, justify the changes you made.
```

### GitHub 使用
- 格式化：将 `assassyn/utils/pre-commit` 复制到 `.git/hooks/pre-commit`
- 添加新功能：Fork 仓库，创建新分支，提交 PR
- 解决冲突：通过将 master 分支变基到开发分支来解决冲突

## Docker 虚拟机

### 使用 Docker
- 采用混合风格的编码、工具和开发，代码库位于物理机上，执行在 docker 虚拟机中
- 构建镜像：`docker build -t assassyn:latest .`
- 运行容器：使用 `docker run` 命令，注意内存限制设置
- 构建初始化：首次使用时运行 `docker exec -it ./init.sh`

## 设计原则

### 文档编写规则
- 避免使用"我们"或"我"，使用被动语态更客观
- 尽量避免提及 `src/` 文件夹中的特定实现代码
- 设计文档应首先讨论高级设计思想，包括设计内容、具体设计决策及其优缺点

### 架构设计原则
- 低侵入性：最小化对现有代码的侵入
- 语义清晰：生成的名称反映操作的语义含义
- 唯一性保证：确保所有生成的名称都是唯一的
- Rust 兼容性：名称设计兼容 Rust 命名约定

### 性能考虑
- 缓存：使用 `UniqueNameCache` 避免重复名称生成
- 延迟评估：仅在需要时生成名称
- 最小开销：AST 重写仅应用于装饰的函数
- 高效查找：使用基于字典的操作码和类映射

## 未来扩展

### 类型系统
- 嵌套泛型验证：深度验证 `List[List[int]]` 内容
- 协议支持：验证 `typing.Protocol` 接口
- 自定义验证器：允许用户定义的验证函数
- 警告模式：开发时警告而不是错误

### 命名系统
- 自定义命名策略：可以向 `TypeOrientedNamer` 添加新的命名策略
- 附加上下文类型：可以向 `NamingManager` 添加新的上下文类型
- 增强 AST 重写：可以添加更复杂的 AST 转换
- 命名策略：可以为不同的目标语言实现可配置的命名策略

### 内存系统
- 解决 LSQ 内存顺序强制限制
- 设计更好的 LSQ 以支持内存操作顺序保证

### 构建系统
- 补丁冲突检测和解决
- 自动化补丁验证
- 补丁依赖管理
- 与子模块更新过程集成