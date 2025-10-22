"""Main entry point for the campus simulation."""

import pickle
from pathlib import Path

from campus import (
    CampusGUI,
    Simulation,
    SimulationClock,
    Student,
    create_campus_map,
    create_class_schedules,
)

# --- 新增：加载训练好的Q-Table ---
TRAINED_DATA_FILE = "trained_q_tables.pkl"

def load_q_tables() -> dict:
    """从文件中加载预训练的Q-Table。"""
    # 训练文件位于项目根目录，即 src 文件夹的上一级
    file_path = Path(__file__).parent.parent / TRAINED_DATA_FILE
    if not file_path.exists():
        print(f"⚠️  警告: 未找到训练数据文件 '{file_path}'。学生将从零知识开始。")
        return {}
    
    try:
        with open(file_path, "rb") as f:
            q_tables = pickle.load(f)
        print(f"✅ 成功从 '{file_path}' 加载了 {len(q_tables)} 个预训练的Q-Table。")
        return q_tables
    except Exception as e:
        print(f"❌ 加载训练数据时出错: {e}。将从零知识开始。")
        return {}

def main() -> None:
    """Initialize and run the campus simulation."""
    
    # --- 新增：在程序开始时加载数据 ---
    trained_q_tables = load_q_tables()
    
    # Create campus map
    print("创建校园地图...")
    graph = create_campus_map()
    print(f"已创建 {len(graph.buildings)} 个建筑")
    
    # Create class schedules
    print("创建课程表...")
    schedules = create_class_schedules()
    print(f"已创建 {len(schedules)} 个班级的课程表")
    
    # Create students
    print("创建拥有独立AI大脑的学生智能体...")
    students = []
    
    class_dorm_mapping = {
        "CS1": "D5a", "MATH": "D5b", "PHYS": "D5c", "ENG": "D5d", "CHEM": "D5a",
    }
    
    students_per_class = 50 # <--- 修改这里，从 100 改为 50
    
    for class_idx, (class_code, schedule) in enumerate(schedules.items()):
        dorm_id = class_dorm_mapping.get(class_code, "D5a")
        
        for student_num in range(students_per_class):
            student_id = f"{class_code}-{student_num:03d}"
            start_building = graph.get_building(dorm_id)
            
            student = Student(
                student_id=student_id,
                class_name=schedule.class_name,
                schedule=schedule,
                start_building=start_building,
            )

            # --- 新增：将加载的“大脑”注入学生 ---
            if student_id in trained_q_tables:
                student.agent.q_table = trained_q_tables[student_id]
                # 在GUI模式下，我们希望学生主要利用学到的知识，而不是随机探索
                student.agent.exploration_rate = 0.01 # 设置一个非常低的探索率
            
            students.append(student)
    
    print(f"已创建 {len(students)} 名学生。")
    
    # Create simulation
    print("初始化模拟环境...")
    clock = SimulationClock(start_time="07:00", time_scale=60.0)
    simulation = Simulation(graph, clock=clock)
    simulation.add_students(students)
    
    # Create and run GUI
    print("启动图形界面...")
    print("\n=== 控制说明 ===")
    print("空格: 暂停/继续")
    print("↑/↓: 加速/减速")
    print("P: 切换路径可见性")
    print("ESC: 退出")
    print("================\n")
    
    gui = CampusGUI(simulation, width=1280, height=720)
    gui.run()
    
    print("\n模拟结束。")
    print(f"总共记录事件数: {len(simulation.event_log)}")


if __name__ == "__main__":
    main()