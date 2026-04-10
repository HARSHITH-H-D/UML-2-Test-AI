# IFA Football Management System - UML/PlantUML Files

This directory contains PlantUML (.puml) files for the International Football Association (IFA) management system based on the use case requirements document.

## File Structure

### Use Case Diagrams (3 variations each)
Following the training dataset pattern, each use case has 3 variations showing different perspectives or abstraction levels:

#### UC1: Report Game
- `report_game_001.puml` - Sequential flow from start to submit
- `report_game_002.puml` - Event-focused with multiple event types
- `report_game_003.puml` - System architecture perspective

#### UC2: Give Availability
- `give_availability_001.puml` - Basic availability submission flow
- `give_availability_002.puml` - Multi-actor perspective with validation
- `give_availability_003.puml` - Notification-focused flow

#### UC3: Schedule Referees
- `schedule_referees_001.puml` - Complete scheduling workflow
- `schedule_referees_002.puml` - Policy-driven scheduling
- `schedule_referees_003.puml` - Automated scheduler perspective

#### UC4: Rank Games
- `rank_games_001.puml` - Approval to publication flow
- `rank_games_002.puml` - Multi-actor with team viewing
- `rank_games_003.puml` - Rules engine focused

#### UC5: Manage Resources
- `manage_resources_001.puml` - Transaction validation flow
- `manage_resources_002.puml` - Resource type operations
- `manage_resources_003.puml` - Policy engine and override flow

#### UC6: Audit Budgets
- `audit_budgets_001.puml` - Basic audit workflow
- `audit_budgets_002.puml` - Approval/disapproval branches
- `audit_budgets_003.puml` - Quarterly compliance checking

### Comprehensive Diagrams

#### Class Diagram
- `ifa_class_diagram.puml` - Complete domain model showing:
  - All entities (Referee, Team, GameReport, etc.)
  - Relationships and multiplicities
  - Key attributes and methods
  - System components

#### Sequence Diagrams
- `report_game_sequence.puml` - Detailed interaction for game reporting
- `schedule_referees_sequence.puml` - Scheduling workflow with timing
- `manage_resources_sequence.puml` - Resource management with approval/override flows

## Key Actors

- **Referee**: Reports games, gives availability
- **IFAAdministration**: Schedules referees, approves reports, audits budgets, manages resources
- **Team**: Manages resources, views rankings

## Key System Components

- **GameReportSystem**: Handles game reporting and event tracking
- **SchedulingSystem**: Automates referee scheduling based on availability and policy
- **RankingSystem**: Calculates and publishes league rankings
- **ResourceManagementSystem**: Validates and tracks team resource transactions
- **BudgetAuditSystem**: Performs quarterly budget audits

## Usage for Training

These files are designed to train models on:
1. **Use case modeling** - Different abstraction levels and perspectives
2. **Actor interactions** - Multiple stakeholder viewpoints
3. **System workflows** - Sequential and branching flows
4. **Domain modeling** - Entity relationships and attributes
5. **Sequence diagrams** - Detailed interaction patterns

## PlantUML Compilation

To generate diagrams from these files:
```bash
plantuml *.puml
```

Or online at: https://www.plantuml.com/plantuml/

## Source Requirements

Based on the IFA Football Management System requirements document (g03-uc-req-cm.pdf) which includes:
- 6 detailed use cases with preconditions, scenarios, and special requirements
- Stakeholder interests and concerns
- System constraints and business rules
- Integration points between use cases
