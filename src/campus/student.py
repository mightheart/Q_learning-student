"""学生智能体实现，使用Q-learning进行智能决策。(最终版：采用Reward Shaping)"""

from __future__ import annotations

import random
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from .graph import Building, Graph, Path
from .schedule import Schedule, ScheduleEvent

# --- 组件：Personality 和 QLearningAgent (保持不变) ---
@dataclass
class Personality:
    patience: float = field(default_factory=lambda: random.uniform(0.2, 1.0))
    risk_aversion: float = field(default_factory=lambda: random.uniform(0.5, 1.5))

class QLearningAgent:
    def __init__(self, actions: List[Any]):
        self.q_table: Dict[Any, Dict[Any, float]] = {}
        self.actions = actions
        self.learning_rate: float = 0.1
        self.discount_factor: float = 0.9
        self.exploration_rate: float = 0.1

    def get_q_value(self, state: Any, action: Any) -> float:
        return self.q_table.get(state, {}).get(action, 0.0)

    def update(self, state: Any, action: Any, reward: float, next_state: Any, next_available_actions: List[Any]):
        old_value = self.get_q_value(state, action)
        next_max = 0.0
        if next_available_actions:
            next_max = max(self.get_q_value(next_state, act) for act in next_available_actions)
        new_value = old_value + self.learning_rate * (reward + self.discount_factor * next_max - old_value)
        if state not in self.q_table:
            self.q_table[state] = {}
        self.q_table[state][action] = new_value

class Student:
    """代表一个由Q-learning驱动的学生智能体。"""

    def __init__(
        self,
        student_id: str,
        class_name: str,
        schedule: Schedule,
        start_building: Building,
    ) -> None:
        self.id = student_id
        self.class_name = class_name
        self.schedule = schedule
        self.current_location: Building = start_building
        self.state: str = "idle"

        self.personality = Personality()
        self.happiness: float = 100.0
        self.base_speed: float = 80.0
        self.agent = QLearningAgent(actions=[])

        self._current_path: Optional[Path] = None
        self._travel_time_remaining: float = 0.0
        
        # 简化：last_state_action 只存储状态和动作
        self.last_state_action: Optional[Tuple[Any, Any]] = None

    def get_state(self, graph: Graph, current_minutes: float) -> Any:
        """构建当前状态，用于Q-learning决策。"""
        next_event = self.schedule.get_next_event(_format_time(current_minutes))
        
        # 统一状态表示法
        if not next_event:
            # 如果没有下一个事件，目标就是宿舍("Dorm")，且时间充裕(2)
            target_building_id = "Dorm"
            deadline_bucket = 2
        else:
            target_building_id = next_event.building_id
            minutes_to_deadline = next_event.start_minutes - current_minutes
            if minutes_to_deadline < 0: deadline_bucket = -1
            elif minutes_to_deadline < 15: deadline_bucket = 0
            elif minutes_to_deadline < 30: deadline_bucket = 1
            else: deadline_bucket = 2
        
        return (
            self.current_location.building_id,
            target_building_id,
            deadline_bucket,
        )

    def decide_and_act(self, graph: Graph, current_minutes: float):
        """决策逻辑：不再需要“老师”，AI可以完全自主学习。"""
        if self.state != "idle":
            return

        current_state = self.get_state(graph, current_minutes)
        available_actions = list(range(len(self.current_location.paths))) + ["wait"]
        
        action = None
        if random.random() < self.agent.exploration_rate:
            action = random.choice(available_actions)
        else:
            q_values = {act: self.agent.get_q_value(current_state, act) for act in available_actions}
            max_q = max(q_values.values())
            best_actions = [act for act, q_val in q_values.items() if q_val == max_q]
            if best_actions:
                action = random.choice(best_actions)

        if action is None:
            action = random.choice(available_actions)

        # 存储决策，以便 learn() 方法计算奖励
        self.last_state_action = (current_state, action)

        if action == "wait":
            # 等待动作在 learn() 中处理
            self.state = "idle"
        elif isinstance(action, int):
            chosen_path = self.current_location.paths[action]
            if chosen_path.is_bridge and not chosen_path.has_capacity():
                # 撞墙的惩罚在 learn() 中处理
                self.last_state_action = (current_state, "failed_move")
            else:
                self.state = "moving"
                self._current_path = chosen_path
                self._travel_time_remaining = chosen_path.get_travel_time(self.base_speed)
                if self._current_path.is_bridge:
                    self._current_path.current_students.append(self.id)

    def learn(self, graph: Graph, current_minutes: float):
        """根据行动结果计算奖励并更新Q-Table。"""
        if not self.last_state_action:
            return

        state, action = self.last_state_action
        reward = 0.0

        # --- 全新的奖励计算逻辑 (Reward Shaping) ---
        next_event = self.schedule.get_next_event(_format_time(current_minutes))

        if action == "wait":
            # 如果没事做或者时间充裕，等待是好事
            if not next_event or (next_event.start_minutes - current_minutes > 30):
                reward += 5.0
            else: # 否则是坏事
                reward -= 10.0
        
        elif action == "failed_move":
            reward -= 20.0 # 撞墙的惩罚
        
        elif isinstance(action, int):
            # 核心：基于到目标距离变化的奖励
            if next_event:
                target_id = next_event.building_id
                
                # 移动前的距离
                old_dist = graph.get_path_distance(state[0], target_id)
                # 移动后的距离
                new_dist = graph.get_path_distance(self.current_location.building_id, target_id)

                if old_dist is not None and new_dist is not None:
                    # 每向目标走近100米，就奖励10分
                    reward += (old_dist - new_dist) / 10.0
                
                # 如果到达了正确的目的地
                if self.current_location.building_id == target_id:
                    # 准时或提前到达，给予巨大奖励
                    if current_minutes <= next_event.start_minutes:
                        reward += 100.0
                    else: # 迟到，给予巨大惩罚
                        reward -= 100.0
            else:
                # 没事做的时候乱走，轻微惩罚
                reward -= 1.0

        # --- 更新Q-Table ---
        next_state = self.get_state(graph, current_minutes)
        next_available_actions = list(range(len(self.current_location.paths))) + ["wait"] if self.state == "idle" else []
        
        self.agent.update(state, action, reward, next_state, next_available_actions)
        
        self.happiness += reward
        self.last_state_action = None

    def update(self, delta_time: float, current_minutes: float) -> None:
        """只负责物理状态的推进。"""
        if self.state != "moving":
            return

        time_to_spend = delta_time
        if time_to_spend < self._travel_time_remaining:
            self._travel_time_remaining -= time_to_spend
        else:
            self._travel_time_remaining = 0.0
            if self._current_path.is_bridge and self.id in self._current_path.current_students:
                self._current_path.current_students.remove(self.id)
            
            self.current_location = self._current_path.end
            self._current_path = None
            self.state = "idle"

    # ... get_interpolated_position 和 _format_time 保持不变 ...
    def get_interpolated_position(self) -> Tuple[float, float]:
        if self.state != "moving" or not self._current_path:
            return (float(self.current_location.x), float(self.current_location.y))
        path = self._current_path
        total_time = path.get_travel_time(self.base_speed)
        progress = 1.0 - (self._travel_time_remaining / total_time) if total_time > 0 else 1.0
        progress = max(0.0, min(1.0, progress))
        start_pos = (float(path.start.x), float(path.start.y))
        end_pos = (float(path.end.x), float(path.end.y))
        x = start_pos[0] + (end_pos[0] - start_pos[0]) * progress
        y = start_pos[1] + (end_pos[1] - start_pos[1]) * progress
        return (x, y)

def _format_time(total_minutes: float) -> str:
    minutes = int(total_minutes) % (24 * 60)
    hour = minutes // 60
    minute = minutes % 60
    return f"{hour:02d}:{minute:02d}"

__all__ = ["Student", "Personality"]