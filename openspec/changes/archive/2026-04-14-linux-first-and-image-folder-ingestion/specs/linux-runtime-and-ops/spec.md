## ADDED Requirements

### Requirement: Linux-first runtime defaults
The system SHALL default to Linux-oriented configuration, filesystem paths, and operator guidance when no platform-specific override is provided.

#### Scenario: Linux host uses Linux defaults
- **WHEN** the service starts on a Linux host without explicit override paths
- **THEN** it MUST resolve its default config and runtime paths using Linux-appropriate locations and examples

#### Scenario: Windows compatibility remains override-based
- **WHEN** the service starts on a Windows host
- **THEN** it MUST allow explicit Windows-compatible paths and continue to operate without Linux-only assumptions

### Requirement: Linux-first operational guidance
The project MUST document Linux as the primary deployment and service-management environment for the background worker and related runtime setup.

#### Scenario: Operator follows setup documentation
- **WHEN** an operator reads the runbook for deployment and restart steps
- **THEN** the primary instructions MUST describe Linux service setup, restart, and configuration reload workflows

#### Scenario: Background worker is installed as a long-running Linux service
- **WHEN** an operator deploys the background worker on Linux
- **THEN** the documented service model MUST support automatic startup and explicit restart after configuration changes
