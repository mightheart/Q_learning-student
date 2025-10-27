"""学生智能体实现，使用Q-learning进行智能决策。(V3.0：引入'attending'状态)"""

from __future__ import annotations

import random
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
    def __init__(self, actions: List[Any] = None, exploration_rate: float = 0.1):
        self.q_table: Dict[Any, Dict[Any, float]] = {}
        self.actions = actions if actions is not None else []
        self.learning_rate: float = 0.1
        self.discount_factor: float = 0.9
        self.exploration_rate: float = exploration_rate

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
    """代表一个由Q-learning驱动的学生智能体，拥有'idle', 'moving', 'attending'三种状态。"""

    def __init__(
        self,
        student_id: str,
        class_name: str,
        schedule: Schedule,
        start_building: Building,
        agent: QLearningAgent,
    ) -> None:
        self.id = student_id
        self.class_name = class_name
        self.schedule = schedule
        self.current_location: Building = start_building
        self.state: str = "idle"  # 状态可以是: "idle", "moving", "attending"

        self.personality = Personality()
        self.happiness: float = 100.0
        self.base_speed: float = 80.0
        self.agent = agent
        self.last_state_action: Optional[Tuple[Any, Any]] = None
        
        # --- 新增：用于防止重复获取到达奖励的状态锁 ---
        self._prepared_for_event_id: Optional[str] = None
        
        # 内部状态变量
        self._current_path: Optional[Path] = None
        self._travel_time_remaining: float = 0.0

    def reset(self, start_building: Building) -> None:
        self.current_location = start_building
        self.state = "idle"
        self.happiness = 100.0
        self.last_state_action = None
        self._prepared_for_event_id = None # <-- 在重置时也清空
        self._current_path = None
        self._travel_time_remaining = 0.0

    def get_state(self, graph: Graph, current_minutes: float) -> Any:
        """构建当前状态，用于Q-learning决策。"""
        next_event = self.schedule.get_next_event(_format_time(current_minutes))
        
        if not next_event:
            target_building_id = "Dorm" # 假设宿舍是最终目标
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
        """决策逻辑：在特定条件下增加'attend_event'动作。"""
        if self.state != "idle":
            return

        current_state = self.get_state(graph, current_minutes)
        
        # 1. 确定所有可用动作
        available_actions = list(range(len(self.current_location.paths))) + ["wait"]
        
        # 检查是否可以添加 "attend_event" 动作
        event_to_attend = self.schedule.get_current_event(_format_time(current_minutes))
        if not event_to_attend:
            next_event = self.schedule.get_next_event(_format_time(current_minutes))
            if next_event and (next_event.start_minutes - current_minutes) <= 5:
                event_to_attend = next_event
        
        if event_to_attend and self.current_location.building_id == event_to_attend.building_id:
            available_actions.append("attend_event")

        # 2. Epsilon-Greedy 决策
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
            action = "wait" # 如果没有最佳动作，默认等待

        # 3. 执行动作并更新状态
        self.last_state_action = (current_state, action)

        if action == "attend_event":
            self.state = "attending"
        elif action == "wait":
            self.state = "idle"
        elif isinstance(action, int):
            chosen_path = self.current_location.paths[action]
            if chosen_path.is_bridge and not chosen_path.has_capacity():
                # 桥满了，视为排队等待，下一帧重新决策
                self.last_state_action = (current_state, "queue_wait")
                self.state = "idle"
            else:
                # 正常移动
                self.state = "moving"
                self._current_path = chosen_path
                self._travel_time_remaining = chosen_path.get_travel_time(self.base_speed)
                if self._current_path.is_bridge:
                    self._current_path.current_students.append(self.id)

    def learn(self, graph: Graph, current_minutes: float):
        """重构后的学习逻辑，围绕新状态和规则。"""
        if not self.last_state_action:
            return

        state, action = self.last_state_action
        reward = 0.0
        p = self.personality

        time_str = _format_time(current_minutes)
        current_event = self.schedule.get_current_event(time_str)
        next_event = self.schedule.get_next_event(time_str)

        # --- 新增：当下一个事件变化时，重置准备状态 ---
        if next_event and self._prepared_for_event_id != next_event.id:
            self._prepared_for_event_id = None

        # --- 核心奖励逻辑 ---
        if action == "attend_event":
            reward += 25.0 # 参与活动，获得持续高额奖励
        
        elif action == "queue_wait":
            reward += 5.0 * p.patience # 排队等待，获得耐心奖励

        elif action == "wait":
            # 只有在没事做的时候等待才加分
            if not current_event and (not next_event or next_event.start_minutes - current_minutes > 30):
                reward += 1.0 * p.patience
            else:
                # 在紧迫的时候等待，扣分
                reward -= 10.0 / max(p.patience, 0.1)
        
        elif isinstance(action, int): # 移动
            # 关键规则：只有在当前没有活动时，才计算“距离减少”的奖励
            if not current_event and next_event:
                target_id = next_event.building_id
                old_dist = graph.get_path_distance(state[0], target_id)
                new_dist = graph.get_path_distance(self.current_location.building_id, target_id)
                if old_dist is not None and new_dist is not None:
                    reward += (old_dist - new_dist) / 100.0
            
            # --- 修改：加入状态锁，防止重复刷分 ---
            # 到达奖励（只在移动后检查）
            if next_event and self.current_location.building_id == next_event.building_id:
                # 只有在尚未“准备好”的情况下才给予到达奖励
                if self._prepared_for_event_id != next_event.id:
                    time_to_event = next_event.start_minutes - current_minutes
                    if 0 <= time_to_event <= 5:
                        reward += 100.0 # 完美守时
                        self._prepared_for_event_id = next_event.id # 加锁
                    elif time_to_event > 5:
                        reward += 30.0 # 提前到达
                        self._prepared_for_event_id = next_event.id # 加锁
                    # 注意：迟到惩罚在 update 方法中通过旷课惩罚实现

        # --- 更新Q-Table ---
        next_state = self.get_state(graph, current_minutes)
        # 下一轮的可用动作在下一帧的 decide_and_act 中计算，这里简化
        next_available_actions = list(range(len(self.current_location.paths))) + ["wait", "attend_event"]
        self.agent.update(state, action, reward, next_state, next_available_actions)
        self.happiness += reward
        self.last_state_action = None

    def update(self, delta_time: float, current_minutes: float) -> None:
        """推进物理状态，并管理状态转换和持续性惩罚。"""
        current_event = self.schedule.get_current_event(_format_time(current_minutes))

        # 1. 状态转换逻辑
        if self.state == "attending" and not current_event:
            # 如果正在活动，但活动时间已过，则自动变为空闲
            self.state = "idle"
        
        # 2. 持续性惩罚逻辑 (旷课)
        # 如果当前有活动，但学生状态不是'attending'，则为旷课
        is_truant = current_event and self.state != "attending"
        if is_truant:
            penalty = -50.0 * delta_time * self.personality.risk_aversion
            self.happiness += penalty

        # 3. 物理移动逻辑
        if self.state == "moving":
            if self._travel_time_remaining > 0:
                self._travel_time_remaining -= delta_time
            
            if self._travel_time_remaining <= 0:
                self._travel_time_remaining = 0.0
                if self._current_path.is_bridge and self.id in self._current_path.current_students:
                    self._current_path.current_students.remove(self.id)
                
                self.current_location = self._current_path.end
                self._current_path = None
                self.state = "idle" # 到达后变为空闲，准备做新决策

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

__all__ = ["Student", "Personality", "QLearningAgent"]