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
        pygame.display.set_caption("Campus Life Simulation")
        
        self.simulation = simulation
        self.width = width
        self.height = height
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Control state
        self.paused = False
        self.time_scale = 60.0  # Default: 60x speed
        self.show_paths = True
        self.running = True
        
        # Student selection
        self.selected_student: Optional[Student] = None
        self.selection_mode = False

    def draw_river(self) -> None:
        """Draw decorative river across the middle of the campus."""
        # River position (y=360 center, spanning ~300-420)
        river_y = 300
        river_height = 120
        
        # Main river body (light blue)
        river_rect = pygame.Rect(0, river_y, self.width, river_height)
        pygame.draw.rect(self.screen, (135, 206, 250), river_rect)  # Sky blue
        
        # Add wave effects (darker blue lines)
        wave_color = (70, 130, 180)  # Steel blue
        for y_offset in [20, 40, 60, 80, 100]:
            y = river_y + y_offset
            # Draw wavy lines
            points = []
            for x in range(0, self.width + 20, 20):
                wave_y = y + 5 * (1 if (x // 20) % 2 == 0 else -1)
                points.append((x, wave_y))
            if len(points) > 1:
                pygame.draw.lines(self.screen, wave_color, False, points, 2)
        
        # Add river banks (dark borders)
        pygame.draw.line(self.screen, (34, 139, 34), (0, river_y), (self.width, river_y), 3)  # Top bank
        pygame.draw.line(self.screen, (34, 139, 34), (0, river_y + river_height), 
                        (self.width, river_y + river_height), 3)  # Bottom bank

    def draw_paths(self) -> None:
        """Draw all paths between buildings using Manhattan-style (only horizontal/vertical lines)."""
        
        if not self.show_paths:
            return
            
        for building in self.simulation.graph.buildings.values():
            for path in building.paths:
                start_pos = (path.start.x, path.start.y)
                end_pos = (path.end.x, path.end.y)
                
                # 🌉 Bridge congestion visualization
                if path.is_bridge:
                    # Determine color based on congestion level
                    congestion = path.get_congestion_level()
                    if congestion == 'full':
                        color = (220, 20, 60)  # Crimson red
                        width = 5
                    elif congestion == 'heavy':
                        color = (255, 140, 0)  # Dark orange
                        width = 4
                    elif congestion == 'moderate':
                        color = (255, 215, 0)  # Gold
                        width = 3
                    else:  # clear
                        color = (50, 205, 50)  # Lime green
                        width = 3
                    
                    # Bridges are vertical, draw directly
                    pygame.draw.line(self.screen, color, start_pos, end_pos, width)
                    
                    # Draw bridge icon (double line effect)
                    offset = 3
                    pygame.draw.line(
                        self.screen, color,
                        (start_pos[0] + offset, start_pos[1]),
                        (end_pos[0] + offset, end_pos[1]),
                        1
                    )
                    pygame.draw.line(
                        self.screen, color,
                        (start_pos[0] - offset, start_pos[1]),
                        (end_pos[0] - offset, end_pos[1]),
                        1
                    )
                else:
                    # Regular path - Manhattan style (horizontal + vertical)
                    # If nodes are on same X or Y, draw direct line
                    if start_pos[0] == end_pos[0] or start_pos[1] == end_pos[1]:
                        # Already aligned - draw direct line
                        pygame.draw.line(
                            self.screen,
                            COLORS["path"],
                            start_pos,
                            end_pos,
                            2,
                        )
                    else:
                        # Not aligned - use L-shaped path (horizontal then vertical)
                        mid_point = (end_pos[0], start_pos[1])
                        # Draw horizontal segment
                        pygame.draw.line(
                            self.screen,
                            COLORS["path"],
                            start_pos,
                            mid_point,
                            2,
                        )
                        # Draw vertical segment
                        pygame.draw.line(
                            self.screen,
                            COLORS["path"],
                            mid_point,
                            end_pos,
                            2,
                        )

    def draw_buildings(self) -> None:
        """Draw all buildings as solid colored blocks."""
        
        for building in self.simulation.graph.buildings.values():
            # Check if this is a bridge node (head or end)
            is_bridge_node = "bridge_" in building.building_id and ("_head" in building.building_id or "_end" in building.building_id)
            
            if is_bridge_node:
                # Bridge nodes: smaller circles with special color
                color = (139, 69, 19) if "_head" in building.building_id else (160, 82, 45)  # Saddle brown
                pygame.draw.circle(self.screen, color, (building.x, building.y), 12)
                pygame.draw.circle(self.screen, (0, 0, 0), (building.x, building.y), 12, 2)
                
                # Add bridge icon (two small vertical lines)
                pygame.draw.line(self.screen, (255, 255, 255), 
                               (building.x - 4, building.y - 6), (building.x - 4, building.y + 6), 2)
                pygame.draw.line(self.screen, (255, 255, 255), 
                               (building.x + 4, building.y - 6), (building.x + 4, building.y + 6), 2)
                
                # Smaller text for bridge nodes
                text = self.small_font.render(building.name[:12], True, (255, 255, 255))
                text_rect = text.get_rect(center=(building.x, building.y - 20))
                # Background for text
                bg_rect = text_rect.inflate(4, 2)
                pygame.draw.rect(self.screen, (0, 0, 0, 128), bg_rect)
                self.screen.blit(text, text_rect)
            else:
                # Regular buildings: SOLID colored squares/rectangles
                # Determine size and color based on building type
                if "library" in building.building_id.lower():
                    # Library: larger, purple
                    size = (70, 50)
                    color = (147, 112, 219)  # Medium purple
                elif "canteen" in building.building_id.lower():
                    # Canteen: large, orange
                    size = (70, 50)
                    color = (255, 140, 0)  # Dark orange
                elif "gym" in building.building_id.lower():
                    # Gym: medium, red
                    size = (60, 45)
                    color = (220, 20, 60)  # Crimson
                elif "playground" in building.building_id.lower():
                    # Playground: medium, green
                    size = (60, 45)
                    color = (34, 139, 34)  # Forest green
                elif building.building_id.startswith("D3"):
                    # Teaching rooms: medium, blue
                    size = (55, 40)
                    color = (70, 130, 180)  # Steel blue
                elif building.building_id.startswith("F3"):
                    # Teaching rooms: medium, cyan
                    size = (55, 40)
                    color = (0, 139, 139)  # Dark cyan
                elif building.building_id.startswith("D5"):
                    # Dorms: medium, golden
                    size = (60, 45)
                    color = (218, 165, 32)  # Goldenrod
                else:
                    # Default: medium square
                    size = (50, 40)
                    color = COLORS["building"]
                
                # Draw solid filled rectangle
                rect = pygame.Rect(building.x - size[0]//2, building.y - size[1]//2, size[0], size[1])
                pygame.draw.rect(self.screen, color, rect)
                
                # Draw building name on top with white text
                text = self.small_font.render(building.name, True, (255, 255, 255))
                text_rect = text.get_rect(center=(building.x, building.y))
                self.screen.blit(text, text_rect)
    
    def draw_selected_student_path(self) -> None:
        """Draw the planned path for the selected student using Manhattan-style routing."""
        
        if not self.selected_student or not self.selected_student.path_to_destination:
            return
        
        # Draw best path (current path) in green
        path = self.selected_student.path_to_destination
        self._draw_manhattan_path(path, (50, 205, 50), 4)  # Lime green
            
        # Draw destination marker
        if path:
            dest = path[-1]
            pygame.draw.circle(self.screen, (50, 205, 50), (dest.x, dest.y), 15, 3)
        
        # Draw alternative path if available
        if self.selected_student.state in ["moving", "waiting"]:
            alt_path = self._get_alternative_path()
            if alt_path:
                self._draw_manhattan_path(alt_path, (255, 215, 0), 3)  # Gold/yellow
                # Mark alternative destination
                if alt_path:
                    alt_dest = alt_path[-1]
                    pygame.draw.circle(self.screen, (255, 215, 0), (alt_dest.x, alt_dest.y), 12, 2)
    
    def _draw_manhattan_path(self, path: List, color: Tuple[int, int, int], width: int) -> None:
        """Draw path using Manhattan-style (horizontal then vertical) segments."""
        
        for i in range(len(path) - 1):
            start_pos = (path[i].x, path[i].y)
            end_pos = (path[i + 1].x, path[i + 1].y)
            
            if start_pos[0] == end_pos[0] or start_pos[1] == end_pos[1]:
                # Already aligned - draw direct line
                pygame.draw.line(self.screen, color, start_pos, end_pos, width)
            else:
                # L-shaped path: horizontal then vertical
                mid_point = (end_pos[0], start_pos[1])
                # Horizontal segment
                pygame.draw.line(self.screen, color, start_pos, mid_point, width)
                # Vertical segment
                pygame.draw.line(self.screen, color, mid_point, end_pos, width)
    
    def _get_alternative_path(self) -> Optional[List]:
        """Get the alternative (second best) path for the selected student."""
        
        if not self.selected_student or not self.selected_student._last_graph:
            return None
        
        if not self.selected_student.active_event:
            return None
        
        start_id = self.selected_student.current_location.building_id
        target_id = self.selected_student.active_event.building_id
        
        if start_id == target_id:
            return None
        
        try:
            # Get current best path
            best_cost, best_route = self.simulation.graph.find_shortest_path(start_id, target_id)
            
            # Try to find alternative by temporarily blocking best path edges
            graph = self.simulation.graph
            alternative_routes = []
            
            # Block each edge in best path and find alternative
            for i in range(len(best_route) - 1):
                current = best_route[i]
                next_node = best_route[i + 1]
                
                # Find and temporarily block this edge
                for path in current.paths:
                    if path.end.building_id == next_node.building_id:
                        original_capacity = path.capacity
                        original_students = path.current_students.copy()
                        
                        # Block it
                        path.capacity = 0
                        path.current_students = ["__BLOCKED__"]
                        
                        try:
                            alt_cost, alt_route = graph.find_shortest_path(start_id, target_id)
                            if alt_cost > best_cost:
                                alternative_routes.append((alt_cost, alt_route))
                        except ValueError:
                            pass
                        
                        # Restore
                        path.capacity = original_capacity
                        path.current_students = original_students
                        break
            
            # Return the best alternative (shortest among alternatives)
            if alternative_routes:
                alternative_routes.sort(key=lambda x: x[0])
                return alternative_routes[0][1]
            
        except (ValueError, AttributeError):
            pass
        
        return None

    def draw_students(self) -> None:
        """Draw all students with colors based on their state."""
        
        for student in self.simulation.students:
            # Determine color based on state
            if student.state == "idle":
                color = COLORS["student_idle"]
            elif student.state == "moving":
                color = COLORS["student_moving"]
            elif student.state == "waiting":
                color = (255, 165, 0)  # Orange for waiting
            else:  # in_class
                color = COLORS["student_in_class"]
            
            # Get smooth interpolated position for animation
            pos_x, pos_y = student.get_interpolated_position()
            pos = (int(pos_x), int(pos_y))
            
            radius = 7 if student == self.selected_student else 5
            pygame.draw.circle(self.screen, color, pos, radius)
            pygame.draw.circle(self.screen, (0, 0, 0), pos, radius, 2 if student == self.selected_student else 1)
            
            # Draw highlight ring for selected student
            if student == self.selected_student:
                pygame.draw.circle(self.screen, (255, 255, 0), pos, radius + 3, 2)
            
            # Draw "W" indicator for waiting students
            if student.state == "waiting":
                wait_text = self.small_font.render("W", True, (255, 255, 255))
                text_rect = wait_text.get_rect(center=(int(pos_x), int(pos_y) - 12))
                # Draw background for better visibility
                bg_rect = text_rect.inflate(4, 2)
                pygame.draw.rect(self.screen, (255, 0, 0), bg_rect)
                self.screen.blit(wait_text, text_rect)

    def draw_info_panel(self) -> None:
        """Draw information panel showing time and statistics."""
        
        panel_height = 120
        panel_rect = pygame.Rect(0, 0, self.width, panel_height)
        pygame.draw.rect(self.screen, COLORS["panel_bg"], panel_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), panel_rect, 2)
        
        # Current time
        time_text = f"Time: {self.simulation.clock.current_time_str}"
        time_surface = self.font.render(time_text, True, COLORS["panel_text"])
        self.screen.blit(time_surface, (20, 20))
        
        # Time scale
        scale_text = f"Speed: {self.time_scale:.0f}x"
        scale_surface = self.font.render(scale_text, True, COLORS["panel_text"])
        self.screen.blit(scale_surface, (20, 50))
        
        # Student statistics
        total_students = len(self.simulation.students)
        idle_count = sum(1 for s in self.simulation.students if s.state == "idle")
        moving_count = sum(1 for s in self.simulation.students if s.state == "moving")
        waiting_count = sum(1 for s in self.simulation.students if s.state == "waiting")
        in_class_count = sum(1 for s in self.simulation.students if s.state == "in_class")
        
        stats_text = f"Students: {total_students} | Idle: {idle_count} | Moving: {moving_count} | Waiting: {waiting_count} | In Class: {in_class_count}"
        stats_surface = self.small_font.render(stats_text, True, COLORS["panel_text"])
        self.screen.blit(stats_surface, (20, 80))
        
        # Status
        status_text = "[PAUSED]" if self.paused else "[RUNNING]"
        status_surface = self.font.render(status_text, True, COLORS["panel_text"])
        self.screen.blit(status_surface, (self.width - 150, 20))
        
        # Recent events or selected student info
        if self.selected_student:
            # Show selected student details
            info_y = 50
            info_texts = [
                f"Selected: {self.selected_student.id}",
                f"Class: {self.selected_student.class_name}",
                f"State: {self.selected_student.state}",
                f"Location: {self.selected_student.current_location.name}",
            ]
            if self.selected_student.active_event:
                info_texts.append(f"Next: {self.selected_student.active_event.building_id} @ {self.selected_student.active_event.time_str}")
            
            # Add path analysis data
            if self.selected_student.state == "moving" or self.selected_student.state == "waiting":
                current_cost = self.selected_student.get_current_path_cost()
                if current_cost > 0:
                    info_texts.append(f"Current Path Cost: {current_cost:.1f} min")
                
                alt_cost = self.selected_student.get_alternative_path_cost()
                if alt_cost is not None:
                    info_texts.append(f"Alt Path Cost: {alt_cost:.1f} min")
                    # Show cost difference
                    if current_cost > 0:
                        diff = alt_cost - current_cost
                        diff_text = f"(+{diff:.1f} min)" if diff > 0 else f"({diff:.1f} min)"
                        info_texts.append(f"Savings: {diff_text}")
            
            for text in info_texts:
                surface = self.small_font.render(text, True, (0, 0, 0))  # Black text for high contrast
                self.screen.blit(surface, (self.width - 350, info_y))
                info_y += 18
        elif self.simulation.event_log:
            # Show recent events
            recent_events = self.simulation.event_log[-3:]
            event_y = 50
            for event in recent_events:
                event_text = f"{event.timestamp} - {event.student_id}: {event.description}"
                event_surface = self.small_font.render(event_text, True, COLORS["panel_text"])
                self.screen.blit(event_surface, (self.width - 550, event_y))
                event_y += 20

    def draw_controls(self) -> None:
        """Draw control hints at the bottom."""
        
        controls_text = "Controls: [SPACE]Pause | [UP/DOWN]Speed | [P]Toggle Paths | [C]Click Student | [ESC]Quit"
        controls_surface = self.small_font.render(controls_text, True, (100, 100, 100))
        self.screen.blit(controls_surface, (20, self.height - 30))
    
    def draw_statistics_panel(self) -> None:
        """Draw detailed statistics on the right side."""
        
        panel_width = 200
        panel_x = self.width - panel_width - 10
        panel_y = 150
        panel_height = 200
        
        # Background
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, (40, 40, 40), panel_rect)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, 1)
        
        # Title
        title = self.font.render("Statistics", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 10, panel_y + 10))
        
        # Class distribution
        class_counts = {}
        for student in self.simulation.students:
            class_name = student.class_name
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        y_offset = panel_y + 40
        for class_name, count in sorted(class_counts.items())[:5]:
            # Shorten class name
            short_name = class_name.split()[0] if " " in class_name else class_name[:10]
            text = f"{short_name}: {count}"
            surface = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(surface, (panel_x + 10, y_offset))
            y_offset += 20
        
        # Path statistics
        y_offset += 10
        moving = sum(1 for s in self.simulation.students if s.state == "moving")
        if len(self.simulation.students) > 0:
            moving_pct = (moving / len(self.simulation.students)) * 100
            text = f"Moving: {moving_pct:.1f}%"
            surface = self.small_font.render(text, True, (200, 200, 200))
            self.screen.blit(surface, (panel_x + 10, y_offset))

    def handle_events(self) -> None:
        """Process user input events."""
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                
                elif event.key == pygame.K_UP:
                    self.time_scale = min(self.time_scale * 2, 960.0)
                
                elif event.key == pygame.K_DOWN:
                    self.time_scale = max(self.time_scale / 2, 1.0)
                
                elif event.key == pygame.K_p:
                    self.show_paths = not self.show_paths
                
                elif event.key == pygame.K_c:
                    self.selection_mode = not self.selection_mode
                    if not self.selection_mode:
                        self.selected_student = None
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self._handle_student_click(event.pos)
    
    def _handle_student_click(self, pos: tuple[int, int]) -> None:
        """Handle clicking on a student to select them."""
        
        click_x, click_y = pos
        click_radius = 10  # Click tolerance
        
        # Find closest student to click
        closest_student = None
        min_distance = click_radius
        
        for student in self.simulation.students:
            dx = student.current_location.x - click_x
            dy = student.current_location.y - click_y
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance < min_distance:
                min_distance = distance
                closest_student = student
        
        if closest_student:
            self.selected_student = closest_student
            self.selection_mode = True

    def run(self) -> None:
        """Main GUI loop."""
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update simulation (unless paused)
            if not self.paused:
                # Scale time based on FPS and time_scale
                delta_seconds = 1.0 / 60.0  # 60 FPS
                self.simulation.clock.time_scale = self.time_scale
                self.simulation.step(delta_seconds)
            
            # Draw everything (order matters: background -> river -> paths -> buildings -> students -> UI)
            self.screen.fill(COLORS["background"])
            self.draw_river()  # Draw river first as background
            self.draw_paths()
            self.draw_selected_student_path()
            self.draw_buildings()
            self.draw_students()
            self.draw_info_panel()
            self.draw_statistics_panel()
            self.draw_controls()
            
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        pygame.quit()


__all__ = ["CampusGUI"]
