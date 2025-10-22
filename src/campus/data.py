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
    # GRID LAYOUT: All buildings aligned to facilitate horizontal/vertical paths
    # Grid spacing: 160 pixels horizontally, 120 pixels vertically
    # Y coordinate: smaller = north (top), larger = south (bottom)
    # River is at y=300-420, bridges cross from 300 to 420
    buildings_data = [
        # North Area - Teaching Buildings (河北区域) - Grid Y=150
        # Northwest block - Teaching Building D (left side)
        ("D3a", "Room D3a", 160, 150),
        ("D3b", "Room D3b", 320, 150),
        ("D3c", "Room D3c", 480, 150),
        ("D3d", "Room D3d", 640, 150),
        
        # Northeast block - Teaching Building F (right side)
        ("F3a", "Room F3a", 800, 150),
        ("F3b", "Room F3b", 960, 150),
        ("F3c", "Room F3c", 1120, 150),
        
        # North Center - Library (Grid Y=230, centered)
        ("library", "Library", 640, 230),
        ("F3d", "Room F3d", 1120, 230),
        
        # 🌉 Bridge Structure (4 bridges, each with head and end nodes)
        # Grid Y=300 (north bank) and Y=420 (south bank)
        # West Bridge (大桥 - Large) - X=160
        ("bridge_west_head", "West Bridge (N)", 160, 300),
        ("bridge_west_end", "West Bridge (S)", 160, 420),
        
        # Mid-Left Bridge (小桥 - Small) - X=480
        ("bridge_mid_left_head", "Mid-L Bridge (N)", 480, 300),
        ("bridge_mid_left_end", "Mid-L Bridge (S)", 480, 420),
        
        # Mid-Right Bridge (小桥 - Small) - X=800
        ("bridge_mid_right_head", "Mid-R Bridge (N)", 800, 300),
        ("bridge_mid_right_end", "Mid-R Bridge (S)", 800, 420),
        
        # East Bridge (大桥 - Large) - X=1120
        ("bridge_east_head", "East Bridge (N)", 1120, 300),
        ("bridge_east_end", "East Bridge (S)", 1120, 420),
        
        # South Area - Living Facilities (河南区域)
        # Southwest - Canteen - Grid Y=520
        ("canteen", "Canteen", 160, 520),
        
        # South Center - Sports Area - Grid Y=520, Y=600
        ("gym", "Gym", 480, 520),
        ("playground", "Playground", 480, 600),
        
        # Southeast - Dormitory Buildings (4 dorms) - Grid Y=520, Y=600
        ("D5a", "Dorm D5a", 800, 520),
        ("D5b", "Dorm D5b", 960, 520),
        ("D5c", "Dorm D5c", 800, 600),
        ("D5d", "Dorm D5d", 960, 600),
    ]
    
    for building_id, name, x, y in buildings_data:
        graph.add_building(Building(building_id=building_id, name=name, x=x, y=y))
    
    # Define paths with realistic distances (in meters)
    # Format: (start, end, length, difficulty, capacity, is_bridge, congestion_factor)
    paths_data = [
        # === North Area Paths (河北区域) ===
        # Teaching Building D - horizontal connections
        ("D3a", "D3b", 80, 1.0, None, False, 0.0),
        ("D3b", "D3c", 80, 1.0, None, False, 0.0),
        ("D3c", "D3d", 80, 1.0, None, False, 0.0),
        
        # Teaching Building F - horizontal connections
        ("F3a", "F3b", 80, 1.0, None, False, 0.0),
        ("F3b", "F3c", 80, 1.0, None, False, 0.0),
        ("F3c", "F3d", 80, 1.0, None, False, 0.0),
        
        # Connect D buildings to library
        ("D3d", "library", 120, 1.0, None, False, 0.0),
        
        # Connect F buildings to library
        ("F3a", "library", 120, 1.0, None, False, 0.0),
        
        # === Connect teaching buildings to bridge heads (north side) ===
        # To West Bridge
        ("D3a", "bridge_west_head", 150, 1.0, None, False, 0.0),
        ("D3b", "bridge_west_head", 200, 1.0, None, False, 0.0),
        
        # To Mid-Left Bridge
        ("D3c", "bridge_mid_left_head", 180, 1.0, None, False, 0.0),
        ("D3d", "bridge_mid_left_head", 150, 1.0, None, False, 0.0),
        ("library", "bridge_mid_left_head", 150, 1.0, None, False, 0.0),
        
        # To Mid-Right Bridge
        ("library", "bridge_mid_right_head", 150, 1.0, None, False, 0.0),
        ("F3a", "bridge_mid_right_head", 150, 1.0, None, False, 0.0),
        ("F3b", "bridge_mid_right_head", 180, 1.0, None, False, 0.0),
        
        # To East Bridge
        ("F3c", "bridge_east_head", 200, 1.0, None, False, 0.0),
        ("F3d", "bridge_east_head", 150, 1.0, None, False, 0.0),
        
        # === Riverside Roads (沿河道路) ===
        # 🛣️ North bank road - connects all bridge heads horizontally
        ("bridge_west_head", "bridge_mid_left_head", 320, 1.0, None, False, 0.0),
        ("bridge_mid_left_head", "bridge_mid_right_head", 320, 1.0, None, False, 0.0),
        ("bridge_mid_right_head", "bridge_east_head", 320, 1.0, None, False, 0.0),
        
        # 🛣️ South bank road - connects all bridge ends horizontally
        ("bridge_west_end", "bridge_mid_left_end", 320, 1.0, None, False, 0.0),
        ("bridge_mid_left_end", "bridge_mid_right_end", 320, 1.0, None, False, 0.0),
        ("bridge_mid_right_end", "bridge_east_end", 320, 1.0, None, False, 0.0),
        
        # === River Crossing (4 bridges) ===
        # 🌉 West Bridge (大桥 - Large bridge, unlimited capacity)
        # Bridge span: head to end (120 meters across river)
        ("bridge_west_head", "bridge_west_end", 120, 1.0, None, True, 0.0),
        
        # 🌉 Mid-Left Bridge (小桥 - Small bridge, limited capacity)
        # Bridge span: head to end (120 meters across river)
        ("bridge_mid_left_head", "bridge_mid_left_end", 120, 1.0, 15, True, 1.5),
        
        # 🌉 Mid-Right Bridge (小桥 - Small bridge, limited capacity)
        # Bridge span: head to end (120 meters across river)
        ("bridge_mid_right_head", "bridge_mid_right_end", 120, 1.0, 15, True, 1.5),
        
        # 🌉 East Bridge (大桥 - Large bridge, unlimited capacity)
        # Bridge span: head to end (120 meters across river)
        ("bridge_east_head", "bridge_east_end", 120, 1.0, None, True, 0.0),
        
        # === Connect bridge ends to south area ===
        # From West Bridge
        ("bridge_west_end", "canteen", 150, 1.0, None, False, 0.0),
        
        # From Mid-Left Bridge
        ("bridge_mid_left_end", "canteen", 120, 1.0, None, False, 0.0),
        ("bridge_mid_left_end", "gym", 150, 1.0, None, False, 0.0),
        
        # From Mid-Right Bridge
        ("bridge_mid_right_end", "gym", 150, 1.0, None, False, 0.0),
        ("bridge_mid_right_end", "D5a", 120, 1.0, None, False, 0.0),
        
        # From East Bridge
        ("bridge_east_end", "D5b", 150, 1.0, None, False, 0.0),
        
        # === South Area Paths (河南区域) ===
        # Connect living facilities horizontally
        ("canteen", "gym", 200, 1.0, None, False, 0.0),
        ("gym", "playground", 80, 1.0, None, False, 0.0),
        ("gym", "D5a", 180, 1.0, None, False, 0.0),
        ("playground", "D5c", 180, 1.0, None, False, 0.0),
        
        # Dormitory connections
        ("D5a", "D5b", 80, 1.0, None, False, 0.0),
        ("D5c", "D5d", 80, 1.0, None, False, 0.0),
        ("D5a", "D5c", 80, 1.0, None, False, 0.0),
        ("D5b", "D5d", 80, 1.0, None, False, 0.0),
        
        # Connect canteen to dorms (for meal times)
        ("canteen", "playground", 250, 1.0, None, False, 0.0),
    ]
    
    for start, end, length, difficulty, capacity, is_bridge, congestion_factor in paths_data:
        graph.connect_buildings(
            start, end, length, 
            difficulty=difficulty, 
            capacity=capacity,
            is_bridge=is_bridge,
            congestion_factor=congestion_factor
        )
    
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
