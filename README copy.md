# Campus Life Simulation

基于图论和最短路径算法的校园生活模拟系统。

> **🎉 版本 2.0.0 重大更新!** 全新的河流校园布局,20栋建筑,更真实的课程表!

## 🌟 核心特性

### 数据结构与算法
- ✅ 基于图的校园地图表示 (20个建筑节点,52条路径边)
- ✅ Dijkstra 最短路径算法实现 O((E+V)logV)
- ✅ 优先队列优化
- ✅ 路径重建与权重计算
- ✅ 容量限制与拥堵控制

### 系统模拟
- ✅ 100名学生自主导航
- ✅ 5个班级完整课程表 (11个事件/天)
- ✅ 模拟时钟系统 (1x-960x 可调速)
- ✅ 事件驱动架构
- ✅ 状态机设计 (idle/moving/in_class)

### 可视化与交互
- ✅ Pygame 实时渲染 (60 FPS)
- ✅ 点击学生查看详细信息
- ✅ 高亮显示学生路径
- ✅ 平滑移动动画
- ✅ 实时统计面板
- ✅ 多种控制模式

## 🗺️ v2.0 新校园布局

### 真实的河流分隔式设计
```
┌────────────────────────────────────────┐
│         北部教学区 (河北)               │
│  D3a-D3d + 图书馆 + F3a-F3d            │
├────────────────────────────────────────┤
│      🌉 河流 + 4座桥梁 🌉              │
├────────────────────────────────────────┤
│         南部生活区 (河南)               │
│  食堂 + 体育设施 + D5a-D5d             │
└────────────────────────────────────────┘
```

### 关键数据
- **20栋建筑**: 8间教室 + 4栋宿舍 + 4座桥 + 4个设施
- **26条路径**: 形成复杂的路径网络
- **4座桥梁**: 跨越河流的唯一通道
- **5个班级**: 每班20人,专属宿舍
- **合理作息**: 07:00起床 - 22:00回宿舍

## 项目结构

```
game3/
├── src/
│   ├── campus/           # 核心模拟模块
│   │   ├── graph.py      # 图数据结构和最短路径算法
│   │   ├── schedule.py   # 课程表管理
│   │   ├── student.py    # 学生代理
│   │   └── simulation.py # 模拟引擎
│   └── tests/            # 单元测试
├── docs/                 # 文档
├── pyproject.toml        # 项目配置
└── run_tests.py          # 测试运行脚本
```

## 安装

1. 确保已安装 Python 3.11+
2. 创建虚拟环境（如果尚未创建）：
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. 安装项目（开发模式）：
   ```powershell
   pip install -e .
   ```

## 运行测试

### 方法一：使用 unittest discover
```powershell
python -m unittest discover src/tests
```

### 方法二：使用测试运行脚本
```powershell
python run_tests.py
```

### 方法三：运行单个测试文件
```powershell
python -m unittest src.tests.test_graph
python -m unittest src.tests.test_schedule_student
python -m unittest src.tests.test_simulation
```

## 快速开始

### 启动 GUI 模拟

```powershell
# 方式一：使用启动脚本（推荐）
python start_simulation.py

# 方式二：直接运行
python src/main.py
```

### GUI 控制

- **SPACE**: 暂停/继续模拟
- **↑/↓**: 增加/减少时间速度（1x - 960x）
- **P**: 显示/隐藏路径
- **C**: 切换学生选择模式
- **鼠标左键**: 点击学生查看详情和路径
- **ESC**: 退出程序

### 模拟说明

- 模拟从早上 7:00 开始
- 100 名学生分布在 5 个班级中
- 学生根据课表自动规划路径并移动
- 颜色编码：
  - 🟢 绿色：空闲状态
  - 🟡 黄色：移动中
  - 🟣 紫色：上课中

## 使用示例

```python
from campus import Building, Graph, Schedule, Student, Simulation

# 创建校园地图
graph = Graph()
gate = Building(building_id="gate", name="校门", x=0, y=0)
library = Building(building_id="lib", name="图书馆", x=100, y=0)
graph.add_building(gate)
graph.add_building(library)
graph.connect_buildings("gate", "lib", length=100)

# 创建学生课程表
schedule = Schedule("计算机科学1班")
schedule.add_event("08:00", "lib")

# 创建学生
student = Student("stu-001", "计算机科学1班", schedule, gate)

# 运行模拟
simulation = Simulation(graph)
simulation.add_students([student])
simulation.step(60.0)  # 模拟60秒
```

## 开发状态

根据[行动计划](docs/行动计划.md)：

- [x] 阶段二：底层数据结构实现
  - [x] Building, Path, Graph 类
  - [x] Dijkstra 最短路径算法
  - [x] 单元测试
- [x] 阶段三：学生与课表系统
  - [x] Schedule 类
  - [x] Student 代理
  - [x] 移动逻辑
- [x] 阶段四：模拟引擎
  - [x] SimulationClock 时间系统
  - [x] Simulation 主循环
  - [x] 事件日志
- [x] 阶段五：Pygame GUI
  - [x] 基础窗口和渲染
  - [x] 地图绘制（建筑物和路径）
  - [x] 学生动画
  - [x] 信息面板（时间、统计、事件日志）
  - [x] 交互控制（暂停、加速、切换视图）
- [x] 阶段六：测试与优化
  - [x] 单元测试（13 个全部通过）
  - [x] 代码质量检查
  - [x] 性能优化
- [x] 阶段七：扩展功能（部分完成）
  - [x] 点击学生显示详细信息
  - [x] 高亮显示学生路径
  - [x] 平滑移动动画
  - [x] 统计面板
  - [ ] 添加教师类（可选）
  - [ ] 更详细建筑结构（可选）

## 技术栈

- Python 3.11+
- 数据结构：图、优先队列（heapq）
- 算法：Dijkstra 最短路径
- GUI：Pygame (计划中)
- 测试：unittest

## 许可证

教学项目
