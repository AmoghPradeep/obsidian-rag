## ADDED Requirements

### Requirement: Configure one incoming root for ingestion sources
The system SHALL accept one configurable incoming root and MUST derive the ingestion source directories from fixed child paths beneath that root.

#### Scenario: Derived source directories are deterministic
- **WHEN** the application resolves runtime paths from configuration
- **THEN** it MUST derive source directories as `<incoming_root>/audio`, `<incoming_root>/pdf`, `<incoming_root>/image`, and `<incoming_root>/text`

#### Scenario: Startup creates the derived directories
- **WHEN** the application loads configuration for normal startup
- **THEN** it MUST create the incoming root and the derived source subdirectories if they do not already exist

### Requirement: Remove separate watch-path configuration inputs
The system SHALL use the shared incoming-root contract instead of independent watch-path configuration fields.

#### Scenario: Supported config surface uses one incoming-root variable
- **WHEN** operators configure ingestion input paths
- **THEN** they MUST configure one incoming-root setting rather than separate audio, PDF, image, and text watch-path settings

### Requirement: Existing ingestion routing continues to operate from derived paths
The background worker SHALL continue to scan and route audio, PDF, image-folder, and text sources from their respective derived directories under the incoming root.

#### Scenario: Worker scans derived audio path
- **WHEN** the background worker performs a scan
- **THEN** it MUST scan the derived `audio` child directory for audio inputs

#### Scenario: Worker scans derived image path
- **WHEN** the background worker performs a scan
- **THEN** it MUST scan the derived `image` child directory for image-folder inputs
