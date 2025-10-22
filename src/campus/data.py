"""Campus map and schedule data for the simulation."""

from .graph import Building, Graph
from .schedule import Schedule


def create_campus_map() -> Graph:
    """Create a realistic campus map with river, bridges, and structured layout.
    
    Layout:
    - North Area (河北): Teaching buildings and library
        - Northwest: D3a, D3b, D3c, D3d (Teaching Building D)
        - North Center: Library
        - Northeast: F3a, F3b, F3c, F3d (Teaching Building F)
    - Central: River with 4 bridges
    - South Area (河南): Living facilities
        - Southwest: Canteen
        - South Center: Sports Area (Gym & Playground)
        - Southeast: D5a, D5b, D5c, D5d (Dormitory)
    """
    
    graph = Graph()
    
    # Define buildings with GUI coordinates (1280x720 window)
    # Y coordinate: smaller = north (top), larger = south (bottom)
    buildings_data = [
        # North Area - Teaching Buildings (河北区域)
        # Northwest block - Teaching Building D (left side)
        ("D3a", "Room D3a", 120, 120),
        ("D3b", "Room D3b", 240, 120),
        ("D3c", "Room D3c", 360, 120),
        ("D3d", "Room D3d", 480, 120),
        
        # North Center - Library
        ("library", "Library", 640, 100),
        
        # Northeast block - Teaching Building F (right side)
        ("F3a", "Room F3a", 800, 120),
        ("F3b", "Room F3b", 920, 120),
        ("F3c", "Room F3c", 1040, 120),
        ("F3d", "Room F3d", 1160, 120),
        
        # River Bridges (4 bridges connecting north and south)
        ("bridge_west", "West Bridge", 200, 360),
        ("bridge_mid_left", "Mid-Left Bridge", 450, 360),
        ("bridge_mid_right", "Mid-Right Bridge", 830, 360),
        ("bridge_east", "East Bridge", 1080, 360),
        
        # South Area - Living Facilities (河南区域)
        # Southwest - Canteen (larger area)
        ("canteen", "Canteen", 280, 580),
        
        # South Center - Sports Area
        ("gym", "Gym", 640, 560),
        ("playground", "Playground", 640, 640),
        
        # Southeast - Dormitory Buildings (4 dorms)
        ("D5a", "Dorm D5a", 920, 560),
        ("D5b", "Dorm D5b", 1040, 560),
        ("D5c", "Dorm D5c", 920, 640),
        ("D5d", "Dorm D5d", 1040, 640),
    ]
    
    for building_id, name, x, y in buildings_data:
        graph.add_building(Building(building_id=building_id, name=name, x=x, y=y))
    
    # Define paths with realistic distances (in meters)
    # Format: (start, end, length, difficulty, capacity)
    paths_data = [
        # === North Area Paths (河北区域) ===
        # Teaching Building D - horizontal connections
        ("D3a", "D3b", 80, 1.0, None),
        ("D3b", "D3c", 80, 1.0, None),
        ("D3c", "D3d", 80, 1.0, None),
        
        # Teaching Building F - horizontal connections
        ("F3a", "F3b", 80, 1.0, None),
        ("F3b", "F3c", 80, 1.0, None),
        ("F3c", "F3d", 80, 1.0, None),
        
        # Connect D buildings to library
        ("D3d", "library", 120, 1.0, None),
        
        # Connect F buildings to library
        ("F3a", "library", 120, 1.0, None),
        
        # Connect teaching buildings to bridges (north side)
        ("D3a", "bridge_west", 150, 1.0, None),
        ("D3b", "bridge_west", 200, 1.0, None),
        ("D3c", "bridge_mid_left", 180, 1.0, None),
        ("D3d", "bridge_mid_left", 150, 1.0, None),
        ("library", "bridge_mid_left", 150, 1.0, None),
        ("library", "bridge_mid_right", 150, 1.0, None),
        ("F3a", "bridge_mid_right", 150, 1.0, None),
        ("F3b", "bridge_mid_right", 180, 1.0, None),
        ("F3c", "bridge_east", 200, 1.0, None),
        ("F3d", "bridge_east", 150, 1.0, None),
        
        # === River Crossing (4 bridges) ===
        # Bridges connect north to south (these are the only river crossings!)
        ("bridge_west", "canteen", 150, 1.0, None),
        ("bridge_mid_left", "canteen", 120, 1.0, None),
        ("bridge_mid_left", "gym", 150, 1.0, None),
        ("bridge_mid_right", "gym", 150, 1.0, None),
        ("bridge_mid_right", "D5a", 120, 1.0, None),
        ("bridge_east", "D5b", 150, 1.0, None),
        
        # === South Area Paths (河南区域) ===
        # Connect living facilities horizontally
        ("canteen", "gym", 200, 1.0, None),
        ("gym", "playground", 80, 1.0, None),
        ("gym", "D5a", 180, 1.0, None),
        ("playground", "D5c", 180, 1.0, None),
        
        # Dormitory connections
        ("D5a", "D5b", 80, 1.0, None),
        ("D5c", "D5d", 80, 1.0, None),
        ("D5a", "D5c", 80, 1.0, None),
        ("D5b", "D5d", 80, 1.0, None),
        
        # Connect canteen to dorms (for meal times)
        ("canteen", "playground", 250, 1.0, None),
    ]
    
    for start, end, length, difficulty, capacity in paths_data:
        graph.connect_buildings(start, end, length, difficulty=difficulty, capacity=capacity)
    
    return graph


def create_class_schedules() -> dict[str, Schedule]:
    """Create realistic schedules for 5 different classes.
    
    Schedule follows typical university timetable:
    - Morning: 08:00-12:00 (classes in teaching buildings)
    - Lunch: 12:00-13:30 (canteen, 30-40 min)
    - Afternoon: 14:00-17:00 (classes/library/sports)
    - Dinner: 18:00-19:00 (canteen, 30-40 min)
    - Evening: 19:00-22:00 (library/dorm)
    - Night: 22:00+ (dorm/sleep)
    """
    
    schedules = {}
    
    # === Class 1: Computer Science ===
    cs_schedule = Schedule("CS Class 1")
    cs_schedule.add_event("07:00", "D5a")          # Wake up in dorm
    cs_schedule.add_event("07:30", "canteen")      # Breakfast (30 min)
    cs_schedule.add_event("08:00", "D3a")          # Morning class 1
    cs_schedule.add_event("10:00", "D3b")          # Morning class 2
    cs_schedule.add_event("12:00", "canteen")      # Lunch (40 min)
    cs_schedule.add_event("12:40", "library")      # Noon break/study
    cs_schedule.add_event("14:00", "F3a")          # Afternoon class 1
    cs_schedule.add_event("16:00", "F3b")          # Afternoon class 2
    cs_schedule.add_event("18:00", "canteen")      # Dinner (30 min)
    cs_schedule.add_event("18:30", "library")      # Evening study
    cs_schedule.add_event("21:30", "D5a")          # Back to dorm
    schedules["CS1"] = cs_schedule
    
    # === Class 2: Mathematics ===
    math_schedule = Schedule("Math Class 2")
    math_schedule.add_event("07:00", "D5b")        # Wake up in dorm
    math_schedule.add_event("07:40", "canteen")    # Breakfast
    math_schedule.add_event("08:20", "F3c")        # Morning class 1
    math_schedule.add_event("10:10", "F3d")        # Morning class 2
    math_schedule.add_event("12:00", "canteen")    # Lunch
    math_schedule.add_event("12:35", "playground") # Noon break/walk
    math_schedule.add_event("14:00", "library")    # Self-study session
    math_schedule.add_event("16:00", "D3c")        # Afternoon class
    math_schedule.add_event("18:00", "canteen")    # Dinner
    math_schedule.add_event("18:40", "library")    # Evening study
    math_schedule.add_event("22:00", "D5b")        # Back to dorm
    schedules["MATH"] = math_schedule
    
    # === Class 3: Physics ===
    physics_schedule = Schedule("Physics Class 3")
    physics_schedule.add_event("07:00", "D5c")     # Wake up in dorm
    physics_schedule.add_event("07:30", "canteen") # Breakfast
    physics_schedule.add_event("08:10", "D3d")     # Morning class 1
    physics_schedule.add_event("10:00", "F3a")     # Morning class 2
    physics_schedule.add_event("12:00", "canteen") # Lunch
    physics_schedule.add_event("12:40", "D5c")     # Noon rest in dorm
    physics_schedule.add_event("14:00", "library") # Afternoon study
    physics_schedule.add_event("15:30", "gym")     # PE class
    physics_schedule.add_event("17:30", "playground") # Sports activity
    physics_schedule.add_event("18:00", "canteen") # Dinner
    physics_schedule.add_event("18:35", "library") # Evening study
    physics_schedule.add_event("21:00", "D5c")     # Back to dorm
    schedules["PHYS"] = physics_schedule
    
    # === Class 4: English ===
    english_schedule = Schedule("English Class 4")
    english_schedule.add_event("07:00", "D5d")     # Wake up in dorm
    english_schedule.add_event("07:35", "canteen") # Breakfast
    english_schedule.add_event("08:15", "F3b")     # Morning class 1
    english_schedule.add_event("10:10", "library") # Morning reading
    english_schedule.add_event("12:00", "canteen") # Lunch
    english_schedule.add_event("12:40", "playground") # Noon walk
    english_schedule.add_event("14:00", "D3b")     # Afternoon class 1
    english_schedule.add_event("16:00", "D3c")     # Afternoon class 2
    english_schedule.add_event("18:00", "canteen") # Dinner
    english_schedule.add_event("18:30", "library") # Evening study
    english_schedule.add_event("20:30", "D5d")     # Back to dorm
    schedules["ENG"] = english_schedule
    
    # === Class 5: Chemistry ===
    chem_schedule = Schedule("Chemistry Class 5")
    chem_schedule.add_event("07:00", "D5a")        # Wake up in dorm
    chem_schedule.add_event("07:30", "canteen")    # Breakfast
    chem_schedule.add_event("08:00", "F3d")        # Morning class 1
    chem_schedule.add_event("10:00", "D3a")        # Morning class 2 (lab)
    chem_schedule.add_event("12:00", "canteen")    # Lunch
    chem_schedule.add_event("12:30", "library")    # Noon reading
    chem_schedule.add_event("14:00", "F3c")        # Afternoon class
    chem_schedule.add_event("16:00", "library")    # Lab report writing
    chem_schedule.add_event("18:00", "canteen")    # Dinner
    chem_schedule.add_event("18:40", "gym")        # Exercise
    chem_schedule.add_event("19:30", "library")    # Evening study
    chem_schedule.add_event("21:30", "D5a")        # Back to dorm
    schedules["CHEM"] = chem_schedule
    
    return schedules


__all__ = ["create_campus_map", "create_class_schedules"]
