"""
Headless (no GUI) training script for the Q-learning student agents.
This script will simulate many days to train the agents and save their learned Q-tables.
"""

import sys
import pickle
from pathlib import Path

# --- Setup project path ---
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from campus import (
    Simulation,
    SimulationClock,
    Student,
    create_campus_map,
    create_class_schedules,
)

# --- Training Configuration ---
TRAINING_DAYS = 1000  # 总共训练多少个模拟日
STUDENTS_PER_CLASS = 50 # 训练时的学生密度
SIM_START_TIME = "07:00"
SIM_END_TIME = "23:00" # 每天模拟到晚上11点
TIME_SCALE = 960.0 # 使用非常高的时间倍率以加速

# Epsilon-decay parameters (学习率衰减)
EPSILON_START = 0.5  # 初始探索率
EPSILON_DECAY = 0.995 # 每过一天，探索率乘以这个值
EPSILON_MIN = 0.01   # 最终最小探索率

OUTPUT_FILE = "trained_q_tables.pkl" # 训练结果保存文件名

def run_training():
    """Main training loop."""
    print("--- Campus Life AI Training Script ---")

    # 1. Initialize Environment
    graph = create_campus_map()
    schedules = create_class_schedules()
    
    # 2. Create Students
    students = []
    class_dorm_mapping = {
        "CS1": "D5a", "MATH": "D5b", "PHYS": "D5c", "ENG": "D5d", "CHEM": "D5a",
    }
    for class_code, schedule in schedules.items():
        dorm_id = class_dorm_mapping.get(class_code, "D5a")
        start_building = graph.get_building(dorm_id)
        for i in range(STUDENTS_PER_CLASS):
            # 修正：学生ID格式化，以匹配main.py
            student_id = f"{class_code}-{i:03d}"
            student = Student(student_id, schedule.class_name, schedule, start_building)
            student.agent.exploration_rate = EPSILON_START
            students.append(student)

    print(f"Created {len(students)} students for training.")
    
    # 3. Start Training Loop (Day by Day)
    for day in range(1, TRAINING_DAYS + 1):
        # --- Daily Reset ---
        clock = SimulationClock(start_time=SIM_START_TIME, time_scale=TIME_SCALE)
        simulation = Simulation(graph, clock)
        
        # Reset students to their dorms and reset happiness, but keep their learned brains!
        for student in students:
            class_code = student.id.split('-')[0]
            dorm_id = class_dorm_mapping.get(class_code, "D5a")
            student.current_location = graph.get_building(dorm_id)
            student.state = "idle"
            student.happiness = 100.0
            student._current_path = None
            # student._active_event = None # <--- 已删除此行错误代码

        simulation.add_students(students)
        
        # --- Simulate One Full Day ---
        simulation_duration_minutes = 16 * 60
        day_elapsed_minutes = 0
        while day_elapsed_minutes < simulation_duration_minutes:
            delta_minutes = simulation.step(delta_seconds=1/60)
            day_elapsed_minutes += delta_minutes

        # --- Daily Report and Epsilon Decay ---
        avg_happiness = sum(s.happiness for s in students) / len(students)
        current_epsilon = students[0].agent.exploration_rate

        print(f"Day {day}/{TRAINING_DAYS} | Epsilon: {current_epsilon:.4f} | Avg Happiness: {avg_happiness:.2f}")

        # Decay epsilon for the next day
        new_epsilon = max(EPSILON_MIN, current_epsilon * EPSILON_DECAY)
        for student in students:
            student.agent.exploration_rate = new_epsilon

    # 4. Save Trained Q-Tables
    print("\nTraining finished. Saving Q-tables...")
    all_q_tables = {student.id: student.agent.q_table for student in students}
    
    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(all_q_tables, f)
        
    print(f"Successfully saved {len(all_q_tables)} Q-tables to {OUTPUT_FILE}")

if __name__ == "__main__":
    run_training()