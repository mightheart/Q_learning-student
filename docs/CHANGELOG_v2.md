# Changelog

All notable changes to the Campus Life Simulation project will be documented in this file.

## [2.0.0] - 2025-10-21 🎉 Major Redesign

### Added - Campus Redesign
- **New realistic campus layout with river and bridges**
  - North Area (河北): 8 teaching rooms (D3a-d, F3a-d) + library
  - River with 4 bridges as the only north-south connection
  - South Area (河南): Canteen, gym, playground, 4 dormitories (D5a-d)
  - Total: 20 buildings (doubled from v1.0)
- **Enhanced path network**
  - 26 paths (52 directed edges)
  - Strategic bridge placement creates natural bottlenecks
  - Average walking distance: 130 meters (1-2 minutes)
- **Improved class schedules**
  - Realistic daily routines (07:00 wake up, 21:00-22:00 return to dorm)
  - Reasonable meal times (30-40 minutes each)
  - No midnight classes (v1.0 issue fixed)
  - 11 events per class per day
- **Dormitory assignment system**
  - CS Class 1 → D5a
  - Math Class 2 → D5b
  - Physics Class 3 → D5c
  - English Class 4 → D5d
  - Chemistry Class 5 → D5a (shares with CS)

### Changed - Major Refactoring
- Complete redesign of `create_campus_map()` function
  - Old: 10 buildings, simple layout
  - New: 20 buildings, river-separated zones
- Complete rewrite of `create_class_schedules()` function
  - Old: Basic time slots, some unrealistic timings
  - New: Full daily schedule with realistic transitions
- Updated test suite to match new building IDs
  - Changed assertions from old building names to new ones
  - All 13 tests still passing

### Technical Improvements
- Better graph complexity for algorithm demonstration
  - More diverse path lengths (80m to 250m)
  - Multiple route options between zones
  - Natural choke points at bridges
- Enhanced educational value
  - More realistic pathfinding scenarios
  - Observable congestion at bridges during rush hours
  - Clear visualization of north-south separation

### Documentation
- Created comprehensive "校园地图设计v2.md"
  - Detailed building catalog with coordinates
  - Road network design principles
  - Class schedule examples
  - Algorithm analysis (O((E+V)logV) with actual numbers)

## [1.1.0] - 2025-10-21

### Added
- Interactive student selection feature
  - Click on any student to select them
  - Selected student is highlighted with yellow circle
  - Detailed information panel shows student ID, class, location, and destination
- Path visualization for selected student
  - Orange highlighted path from current position to destination
  - Destination marker with circle
  - Real-time path updates as student moves
- Smooth movement animation
  - Students now interpolate between path segments
  - Eliminates jerky movement
  - Maintains 60 FPS performance
- Statistics panel
  - Right-side panel showing class distribution
  - Real-time percentage of students moving
  - Clean, organized display

### Changed
- All GUI text converted to English
  - Building names: Gate, Library, Teaching A/B, etc.
  - Class names: CS Class 1, Math Class 2, etc.
  - UI labels: Time, Speed, Students, etc.
  - Control hints: Complete English instructions
- Improved visual clarity with new color scheme for selection

### Fixed
- Chinese character display issues in Pygame

## [1.0.0] - 2025-10-20

### Added
- Initial release with core functionality
- Graph data structure with Dijkstra's algorithm
- Student agent system with schedules
- Simulation engine with time management
- Pygame GUI with real-time visualization
- 10 buildings, 100 students, 5 classes
- Comprehensive test suite (13 tests)
- Complete documentation set

---

**Project**: Campus Life Simulation  
**Repository**: l:\datastructure_class_ws\game3  
**Maintainer**: Campus Simulation Team
