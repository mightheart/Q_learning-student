# Campus Life Simulation

基于图论和最短路径算法的校园生活模拟系统。


## 项目结构

```
game3/
├── src/
│   ├── campus/           # 代码核心
│   │   ├── graph.py      # 图数据结构和最短路径算法
│   │   ├── schedule.py   # 课程表管理
│   │   ├── student.py    # 学生代理
│   │   └── simulation.py # 模拟引擎
│   └── tests/            # 单元测试
├── docs/                 # 更新和要求之类的文档都存在这里
├── pyproject.toml        # 项目配置
└── run.py          # 運行游戲
└── test.py         # 測試子功能
```

## 安装

1.  Python 3.11+
2. 创建虚拟环境：
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. 安装项目（开发模式）：
   ```powershell
   pip install -e .
   ```

## 快速开始

### 启动 GUI 模拟

```powershell
# 運行
python start_simulation.py

# 或者
python src/main.py
```


## 待辦事項

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
  - [ ] 分離重曡的學生
  - [ ] 增加橋容量判斷
  - [ ] 增加食堂容量判斷

## 技术栈

- Python 3.11+
- 数据结构：图、优先队列
- 算法：Dijkstra 最短路径
- GUI：Pygame 
- 测试：unittest

## 许可证

教学项目
