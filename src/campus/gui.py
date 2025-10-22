"""Pygame GUI for campus simulation visualization."""

from __future__ import annotations

from typing import List, Optional, Tuple

import pygame

from .simulation import Simulation
from .student import Student


# Color scheme
COLORS = {
    "background": (245, 245, 245),
    "building": (70, 130, 180),
    "building_text": (255, 255, 255),
    "path": (200, 200, 200),
    "student_idle": (100, 200, 100),
    "student_moving": (255, 200, 50),
    "student_in_class": (200, 100, 200),
    "panel_bg": (50, 50, 50),
    "panel_text": (255, 255, 255),
    "button": (70, 130, 180),
    "button_hover": (100, 160, 210),
}


class CampusGUI:
    """Pygame-based visualization for campus simulation."""

    def __init__(
        self,
        simulation: Simulation,
        width: int = 1280,
        height: int = 720,
    ) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Campus Life Simulation - AI Edition")
        
        self.simulation = simulation
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Control state
        self.paused = False
        self.time_scale = 60.0
        self.show_paths = True
        self.running = True
        
        # Student selection
        self.selected_student: Optional[Student] = None

    def draw_river(self) -> None:
        """Draw decorative river across the middle of the campus."""
        river_y = 300
        river_height = 120
        river_rect = pygame.Rect(0, river_y, self.width, river_height)
        pygame.draw.rect(self.screen, (135, 206, 250), river_rect)
        
        wave_color = (70, 130, 180)
        for y_offset in [20, 40, 60, 80, 100]:
            y = river_y + y_offset
            points = []
            for x in range(0, self.width + 20, 20):
                wave_y = y + 5 * (1 if (x // 20) % 2 == 0 else -1)
                points.append((x, wave_y))
            if len(points) > 1:
                pygame.draw.lines(self.screen, wave_color, False, points, 2)
        
        pygame.draw.line(self.screen, (34, 139, 34), (0, river_y), (self.width, river_y), 3)
        pygame.draw.line(self.screen, (34, 139, 34), (0, river_y + river_height), 
                        (self.width, river_y + river_height), 3)

    def draw_paths(self) -> None:
        """Draw all paths, visualizing bridge congestion based on occupancy."""
        if not self.show_paths:
            return
            
        for building in self.simulation.graph.buildings.values():
            for path in building.paths:
                start_pos = (path.start.x, path.start.y)
                end_pos = (path.end.x, path.end.y)
                
                if path.is_bridge:
                    # --- 修改：基于实际占用率来可视化拥堵 ---
                    ratio = 0.0
                    if path.capacity is not None and path.capacity > 0:
                        ratio = len(path.current_students) / path.capacity

                    if ratio >= 1.0:
                        color = (220, 20, 60)  # Crimson red
                        width = 5
                    elif ratio >= 0.7:
                        color = (255, 140, 0)  # Dark orange
                        width = 4
                    elif ratio >= 0.3:
                        color = (255, 215, 0)  # Gold
                        width = 3
                    else:
                        color = (50, 205, 50)  # Lime green
                        width = 3
                    
                    pygame.draw.line(self.screen, color, start_pos, end_pos, width)
                    
                    # --- 删除：不再显示旧的 queue 队列长度 ---
                else:
                    # Regular path - Manhattan style
                    if start_pos[0] == end_pos[0] or start_pos[1] == end_pos[1]:
                        pygame.draw.line(self.screen, COLORS["path"], start_pos, end_pos, 2)
                    else:
                        mid_point = (end_pos[0], start_pos[1])
                        pygame.draw.line(self.screen, COLORS["path"], start_pos, mid_point, 2)
                        pygame.draw.line(self.screen, COLORS["path"], mid_point, end_pos, 2)

    def draw_buildings(self) -> None:
        """Draw all buildings as solid colored blocks."""
        for building in self.simulation.graph.buildings.values():
            is_bridge_node = "bridge_" in building.building_id
            
            if is_bridge_node:
                color = (139, 69, 19)
                pygame.draw.circle(self.screen, color, (building.x, building.y), 8)
                pygame.draw.circle(self.screen, (0, 0, 0), (building.x, building.y), 8, 1)
            else:
                size = (55, 40)
                color = COLORS["building"]
                if "canteen" in building.building_id.lower(): color = (255, 140, 0)
                elif "library" in building.building_id.lower(): color = (147, 112, 219)
                elif building.building_id.startswith("D5"): color = (218, 165, 32)
                
                rect = pygame.Rect(building.x - size[0]//2, building.y - size[1]//2, size[0], size[1])
                pygame.draw.rect(self.screen, color, rect)
                
                text = self.small_font.render(building.name, True, (255, 255, 255))
                text_rect = text.get_rect(center=(building.x, building.y))
                self.screen.blit(text, text_rect)
    
    # --- 删除：不再需要绘制学生规划的完整路径 ---
    # def draw_selected_student_path(self) -> None: ...
    # def _draw_manhattan_path(...) -> None: ...
    # def _get_alternative_path(...) -> None: ...

    def draw_students(self) -> None:
        """Draw all students, color-coded by state and happiness."""
        for student in self.simulation.students:
            # --- 修改：根据幸福感决定颜色 ---
            is_unhappy = student.happiness < 0
            
            if is_unhappy:
                color = (255, 0, 0)  # 红色代表“不开心”
            elif student.state == "idle":
                color = COLORS["student_idle"]
            elif student.state == "moving":
                color = COLORS["student_moving"]
            else:  # in_class
                color = COLORS["student_in_class"]
            
            pos_x, pos_y = student.get_interpolated_position()
            pos = (int(pos_x), int(pos_y))
            
            radius = 7 if student == self.selected_student else 5
            pygame.draw.circle(self.screen, color, pos, radius)
            
            border_width = 2 if is_unhappy else 1
            border_color = (0, 0, 0)
            pygame.draw.circle(self.screen, border_color, pos, radius, border_width)
            
            if student == self.selected_student:
                pygame.draw.circle(self.screen, (255, 255, 0), pos, radius + 3, 2)

    def draw_info_panel(self) -> None:
        """Draw information panel showing time and AI-relevant stats."""
        panel_height = 120
        panel_rect = pygame.Rect(0, 0, self.width, panel_height)
        pygame.draw.rect(self.screen, COLORS["panel_bg"], panel_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), panel_rect, 2)
        
        time_text = f"Time: {self.simulation.clock.current_time_str}"
        time_surface = self.font.render(time_text, True, COLORS["panel_text"])
        self.screen.blit(time_surface, (20, 20))
        
        scale_text = f"Speed: {self.time_scale:.0f}x"
        scale_surface = self.font.render(scale_text, True, COLORS["panel_text"])
        self.screen.blit(scale_surface, (20, 50))
        
        status_text = "[PAUSED]" if self.paused else "[RUNNING]"
        status_surface = self.font.render(status_text, True, COLORS["panel_text"])
        self.screen.blit(status_surface, (self.width - 150, 20))
        
        # --- 修改：显示AI学生的新信息 ---
        if self.selected_student:
            info_y = 20
            info_texts = [
                f"Selected: {self.selected_student.id}",
                f"State: {self.selected_student.state}",
                f"Happiness: {self.selected_student.happiness:.1f}",
                f"Location: {self.selected_student.current_location.name}",
            ]
            
            next_event = self.selected_student.schedule.get_next_event(self.simulation.clock.current_time_str)
            if next_event:
                info_texts.append(f"Next: {next_event.building_id} @ {next_event.time_str}")

            p = self.selected_student.personality
            info_texts.append(f"Personality -> Patience: {p.patience:.2f} | Risk Averse: {p.risk_aversion:.2f}")

            for text in info_texts:
                surface = self.small_font.render(text, True, COLORS["panel_text"])
                self.screen.blit(surface, (self.width - 550, info_y))
                info_y += 18
        else:
            # 显示学生状态统计
            total = len(self.simulation.students)
            idle = sum(1 for s in self.simulation.students if s.state == "idle")
            moving = sum(1 for s in self.simulation.students if s.state == "moving")
            in_class = sum(1 for s in self.simulation.students if s.state == "in_class")
            stats_text = f"Students: {total} | Idle: {idle} | Moving: {moving} | In Class: {in_class}"
            stats_surface = self.small_font.render(stats_text, True, COLORS["panel_text"])
            self.screen.blit(stats_surface, (20, 80))

    def draw_controls(self) -> None:
        """Draw control hints at the bottom."""
        controls_text = "Controls: [SPACE]Pause | [UP/DOWN]Speed | [P]Toggle Paths | Click to Select | [ESC]Quit"
        controls_surface = self.small_font.render(controls_text, True, (100, 100, 100))
        self.screen.blit(controls_surface, (20, self.height - 30))
    
    # --- 删除：不再需要 statistics_panel ---
    # def draw_statistics_panel(self) -> None: ...

    def handle_events(self) -> None:
        """Process user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                elif event.key == pygame.K_SPACE: self.paused = not self.paused
                elif event.key == pygame.K_UP: self.time_scale = min(self.time_scale * 2, 960.0)
                elif event.key == pygame.K_DOWN: self.time_scale = max(self.time_scale / 2, 1.0)
                elif event.key == pygame.K_p: self.show_paths = not self.show_paths
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_student_click(event.pos)
    
    def _handle_student_click(self, pos: tuple[int, int]) -> None:
        """Handle clicking on a student to select them."""
        click_x, click_y = pos
        
        closest_student = None
        min_dist_sq = 15**2  # Click tolerance radius, squared
        
        for student in self.simulation.students:
            px, py = student.get_interpolated_position()
            dist_sq = (px - click_x)**2 + (py - click_y)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                closest_student = student
        
        self.selected_student = closest_student

    def run(self) -> None:
        """Main GUI loop. (修正版：模拟16小时后自动结束)"""
        
        # 定义模拟的开始和结束时间（分钟）
        sim_start_minutes = 7 * 60  # 07:00
        sim_end_minutes = 23 * 60   # 23:00

        while self.running:
            self.handle_events()
            
            if not self.paused:
                delta_seconds = self.clock.get_time() / 1000.0
                self.simulation.clock.time_scale = self.time_scale
                self.simulation.step(delta_seconds)

            # --- 新增：检查是否到达每日模拟的结束时间 ---
            current_minutes = self.simulation.clock.current_minutes
            # 当时间从22:59跳到23:00时，current_minutes会大于等于sim_end_minutes
            # 同时要防止在00:00-07:00之间启动时直接退出
            if current_minutes >= sim_end_minutes or current_minutes < sim_start_minutes:
                print("\nSimulation for the day has ended (23:00 reached).")
                self.running = False # 结束主循环

            # --- 绘制逻辑保持不变 ---
            self.screen.fill(COLORS["background"])
            self.draw_river()
            self.draw_paths()
            self.draw_buildings()
            self.draw_students()
            self.draw_info_panel()
            self.draw_controls()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # 在退出前稍作停留，让用户看到结束信息
        print("GUI will close in 5 seconds...")
        pygame.time.wait(5000)
        pygame.quit()

__all__ = ["CampusGUI"]
