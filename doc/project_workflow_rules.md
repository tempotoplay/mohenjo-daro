# Project Workflow & Rules

This document captures the successful methods and architectural patterns established during the "Citadel Interior" and "Refactoring" sessions.

## 1. Architecture Patterns

### Separation of Concerns
We strictly separate Data, Logic, and Execution:
- **Registry (`src/mohenjo/registry.py`)**: Core data models (`Landmark`, `ProceduralFeature`) and loading logic. Passive data structures.
- **Scripts (`src/scripts/`)**: Executable logic for specific tasks.
    - `generate.py`: Procedural generation algorithms. Outputs to `data/`.
    - `render_map.py`: Visualization and verification. Outputs to `outputs/`.
- **Data (`src/data/`)**: YAML files serving as the single source of truth.

### Procedural Generation
- **Static Output**: Procedural scripts should generate *static data* (YAML) rather than generating on-the-fly during rendering. This allows inspection and debugging of the generated data.
- **Collision Detection**: Use a simple AABB systems with padding (separating axis theorem logic) to prevent overlap with existing landmarks.
- **Deterministic Seeds**: Always use `random.seed()` to ensure reproducible results.

## 2. File Organization Rules

- **Source Code**: All python code in `src/`.
- **Package**: Core library code in `src/mohenjo/`.
- **Scripts**: All executable entry points in `src/scripts/`.
- **Outputs**: ALL generated artifacts (SVGs, PNGs, logs) must go to `outputs/`.
    - **Never** pollute the root directory.
    - `outputs/` is git-ignored.

## 3. Visualization & Verification

- **High Contrast**: When debugging procedural geometry, use high-contrast colors (e.g., bright Red `#EF5350` for buildings, Black strokes) and **1.0 Opacity**. Transparency often hides missing geometry or overlaps.
- **SVG rendering**: Use SVG for infinite resolution debugging of mapping data.
- **rsvg-convert**: Use `rsvg-convert` to create shareable PNGs for user review.

## 4. Git Workflow

- **Atomic Commits**: Commit distinct bodies of work (e.g., "Refactor file structure" separate from "Add new feature").
- **Verification First**: Always run the generation and rendering loop *before* committing to ensure no regressions.

## 5. Archaeological Modeling

- **Morphology**: Distinguish between "Rich" (Courtyard/O-Type, U-Type) and "Common" housing.
- **Scale**: Use real-world meters for all logic, converting to pixels only at the final rendering stage.
