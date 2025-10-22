"""Main entry point for the campus simulation."""

from campus import (
    CampusGUI,
    Simulation,
    SimulationClock,
    Student,
    create_campus_map,
    create_class_schedules,
)


def main() -> None:
    """Initialize and run the campus simulation."""
    
    # Create campus map
    print("Creating campus map...")
    graph = create_campus_map()
    print(f"Created {len(graph.buildings)} buildings")
    
    # Create class schedules
    print("Creating class schedules...")
    schedules = create_class_schedules()
    print(f"Created {len(schedules)} class schedules")
    
    # Create students (100 students per class = 500 total) - Stress test!
    print("Creating students...")
    students = []
    
    # Map classes to their dormitories (matching schedule starting locations)
    class_dorm_mapping = {
        "CS1": "D5a",    # CS students in D5a
        "MATH": "D5b",   # Math students in D5b
        "PHYS": "D5c",   # Physics students in D5c
        "ENG": "D5d",    # English students in D5d
        "CHEM": "D5a",   # Chemistry students share D5a with CS
    }
    
    students_per_class = 100  # Increased from 20 to 100 for stress testing
    
    for class_idx, (class_code, schedule) in enumerate(schedules.items()):
        dorm_id = class_dorm_mapping.get(class_code, "D5a")
        
        for student_num in range(students_per_class):
            student_id = f"{class_code}-{student_num:03d}"  # 3 digits for 0-999
            start_building = graph.get_building(dorm_id)
            
            student = Student(
                student_id=student_id,
                class_name=schedule.class_name,
                schedule=schedule,
                start_building=start_building,
            )
            students.append(student)
    
    print(f"Created {len(students)} students distributed across 4 dorms")
    print(f"⚠️  Stress test mode: {students_per_class} students per class!")
    
    # Create simulation
    print("Initializing simulation...")
    clock = SimulationClock(start_time="07:00", time_scale=60.0)
    simulation = Simulation(graph, clock=clock)
    simulation.add_students(students)
    
    # Create and run GUI
    print("Starting GUI...")
    print("\n=== Controls ===")
    print("SPACE: Pause/Resume")
    print("↑/↓: Increase/Decrease speed")
    print("P: Toggle path visibility")
    print("ESC: Quit")
    print("================\n")
    
    gui = CampusGUI(simulation, width=1280, height=720)
    gui.run()
    
    print("\nSimulation ended.")
    print(f"Total events logged: {len(simulation.event_log)}")


if __name__ == "__main__":
    main()
