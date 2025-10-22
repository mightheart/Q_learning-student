"""Pygame GUI for campus simulation visualization."""

from __future__ import annotations

from typing import Optional

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

    def draw_paths(self) -> None:
        """Draw all paths between buildings."""
        
        if not self.show_paths:
            return
            
        for building in self.simulation.graph.buildings.values():
            for path in building.paths:
                start_pos = (path.start.x, path.start.y)
                end_pos = (path.end.x, path.end.y)
                pygame.draw.line(
                    self.screen,
                    COLORS["path"],
                    start_pos,
                    end_pos,
                    2,
                )

    def draw_buildings(self) -> None:
        """Draw all buildings as rectangles with labels."""
        
        for building in self.simulation.graph.buildings.values():
            # Draw building rectangle
            rect = pygame.Rect(building.x - 30, building.y - 20, 60, 40)
            pygame.draw.rect(self.screen, COLORS["building"], rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 2)
            
            # Draw building name
            text = self.small_font.render(building.name, True, COLORS["building_text"])
            text_rect = text.get_rect(center=(building.x, building.y))
            self.screen.blit(text, text_rect)
    
    def draw_selected_student_path(self) -> None:
        """Draw the planned path for the selected student."""
        
        if not self.selected_student or not self.selected_student.path_to_destination:
            return
        
        # Draw path line
        path = self.selected_student.path_to_destination
        for i in range(len(path) - 1):
            start_pos = (path[i].x, path[i].y)
            end_pos = (path[i + 1].x, path[i + 1].y)
            pygame.draw.line(self.screen, (255, 200, 0), start_pos, end_pos, 4)
            
        # Draw destination marker
        if path:
            dest = path[-1]
            pygame.draw.circle(self.screen, (255, 200, 0), (dest.x, dest.y), 15, 3)

    def draw_students(self) -> None:
        """Draw all students with colors based on their state."""
        
        for student in self.simulation.students:
            # Determine color based on state
            if student.state == "idle":
                color = COLORS["student_idle"]
            elif student.state == "moving":
                color = COLORS["student_moving"]
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
        in_class_count = sum(1 for s in self.simulation.students if s.state == "in_class")
        
        stats_text = f"Students: {total_students} | Idle: {idle_count} | Moving: {moving_count} | In Class: {in_class_count}"
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
            
            for text in info_texts:
                surface = self.small_font.render(text, True, (255, 255, 100))
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
            
            # Draw everything
            self.screen.fill(COLORS["background"])
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
