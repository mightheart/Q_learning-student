"""Test script to verify graph connectivity, especially riverside roads."""

from src.campus.data import create_campus_map

def test_riverside_connectivity():
    """Test that riverside roads are properly connected."""
    
    graph = create_campus_map()
    
    print("=" * 60)
    print("Testing Riverside Road Connectivity")
    print("=" * 60)
    
    # Test North bank road
    bridge_heads = [
        "bridge_west_head",
        "bridge_mid_left_head", 
        "bridge_mid_right_head",
        "bridge_east_head"
    ]
    
    print("\n🛣️  North Bank Road (Bridge Heads):")
    print("-" * 60)
    for i, head in enumerate(bridge_heads):
        building = graph.buildings.get(head)
        if not building:
            print(f"❌ {head} NOT FOUND in graph!")
            continue
        
        print(f"\n{head}:")
        print(f"  Position: ({building.x}, {building.y})")
        print(f"  Connected paths ({len(building.paths)}):")
        
        for path in building.paths:
            end_id = path.end.building_id
            is_riverside = end_id in bridge_heads
            marker = "🛣️ " if is_riverside else "  "
            print(f"    {marker}{end_id} - {path.length}m")
    
    # Test South bank road
    bridge_ends = [
        "bridge_west_end",
        "bridge_mid_left_end",
        "bridge_mid_right_end", 
        "bridge_east_end"
    ]
    
    print("\n" + "=" * 60)
    print("🛣️  South Bank Road (Bridge Ends):")
    print("-" * 60)
    for i, end in enumerate(bridge_ends):
        building = graph.buildings.get(end)
        if not building:
            print(f"❌ {end} NOT FOUND in graph!")
            continue
        
        print(f"\n{end}:")
        print(f"  Position: ({building.x}, {building.y})")
        print(f"  Connected paths ({len(building.paths)}):")
        
        for path in building.paths:
            end_id = path.end.building_id
            is_riverside = end_id in bridge_ends
            marker = "🛣️ " if is_riverside else "  "
            print(f"    {marker}{end_id} - {path.length}m")
    
    # Test a sample pathfinding using riverside roads
    print("\n" + "=" * 60)
    print("Testing Pathfinding with Riverside Roads:")
    print("-" * 60)
    
    # Test case 1: Adjacent bridges - SHOULD use riverside road
    try:
        cost, route = graph.find_shortest_path("bridge_west_head", "bridge_east_head")
        print(f"\nRoute from bridge_west_head to bridge_east_head:")
        print(f"Total cost: {cost:.2f} minutes")
        print(f"Path: {' → '.join([b.building_id for b in route])}")
        
        # This SHOULD use riverside roads
        if len(route) == 4:  # west -> mid_left -> mid_right -> east
            print("  ✅ CORRECTLY uses north bank riverside road!")
        else:
            print(f"  ⚠️  Route has {len(route)} nodes (expected 4)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test case 2: From one bridge end to another
    try:
        cost, route = graph.find_shortest_path("bridge_west_end", "bridge_east_end")
        print(f"\nRoute from bridge_west_end to bridge_east_end:")
        print(f"Total cost: {cost:.2f} minutes")
        print(f"Path: {' → '.join([b.building_id for b in route])}")
        
        if len(route) == 4:
            print("  ✅ CORRECTLY uses south bank riverside road!")
        else:
            print(f"  ⚠️  Route has {len(route)} nodes (expected 4)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test case 3: Cross-campus with potential riverside usage
    try:
        cost1, route1 = graph.find_shortest_path("F3a", "D5b")
        print(f"\nRoute from F3a (east teaching) to D5b (east dorm):")
        print(f"Total cost: {cost1:.2f} minutes")
        print(f"Path: {' → '.join([b.building_id for b in route1])}")
        
        # Check if it uses east bridge and riverside
        uses_riverside = any(
            route1[i].building_id in ["bridge_east_head", "bridge_mid_right_head"] and
            route1[i+1].building_id in ["bridge_east_end", "bridge_mid_right_end"]
            for i in range(len(route1) - 1)
        )
        if uses_riverside:
            print("  ✅ Uses appropriate bridge!")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_riverside_connectivity()
