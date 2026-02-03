PRD: Warehouse.Core - Unified Access
Version: 0.8 (January 2026)
Status: First Draft
Target User: ML-Bio Principle Investigator 
1. Executive Summary
As a researcher, I want to perform analysis on petabyte-scale data assets that are walled gardens, and also curate my own data and data from collaborator labs. This requires a platform that enables researchers to work within a single, normalized interface where local, peer, and global data can be integrated and compared as a unified dataset, eliminating the need for manual reconciliation of mismatched formats and multi-silo management.
I am also subject to host of privacy and sovereignty regulations which increase the compliance and cost burden on my team and budget. 
2. Problem Statement
Data Immobility: Walled-garden assets (e.g., NCBI SRA, UK Biobank) cannot be moved or downloaded due to their scale and residency requirements.
Access Fragmentation: Ingressing peer-provided data and restricted global assets requires navigating multiple distinct protocols, portals, and proprietary toolsets.
Schema Discordance: Mismatched metadata formats between curated local assets and large-scale external databases prevent direct data comparison and analysis.
3. Functional Requirements
3.1. Unified Data Access (The "Virtual Bridge")
Immovable Asset Mounting: The platform must provide a virtualized file system layer that mounts restricted remote data as local read-only volumes.
Direct-Stream Access: Enable analysis tools to "stream" specific data segments from remote walled gardens on-demand, bypassing the need for bulk data transfers.
Collaborator Ingress Portals: Automated, encrypted drop-zones for peer labs to push data directly into a project-specific ingress bucket.
3.2. Normalized Metadata & Ingress
Automated Schema Mapping: The system must automatically map incoming local and collaborator metadata to a global standard upon ingress.
Biotype Reconciliation: Automated unit and nomenclature conversion to ensure collaborator data is immediately comparable with the "Gold Standard" restricted datasets.
Unified Discovery Index: A single, searchable catalog that indexes the metadata of local, collaborator, and walled-garden assets simultaneously.
3.3. Project-Based Data Organization
The "Single View" Interface: A unified workspace where restricted datasets, local curated files, and collaborator inputs appear in a single, consistent directory structure.
Multi-Source Data Linking: Ability to create logical links between disparate datasets within a single project view.
Curation Workspaces: Dedicated staging areas for "mucking" and cleaning collaborator data before it is promoted into the unified project index.

4. Technical Constraints
Egress Prevention: The data access layer must enforce strict "Read-Only" permissions for all remote walled-garden assets.
API Mapping to Hox CLI: The platform must support native API-level integration with specialized data portals to facilitate metadata retrieval.
Latency Management: Implementation of aggressive metadata caching to allow for high-speed browsing of petabyte-scale remote directory structures.

5. Success Metrics
Normalization Efficiency: 80% reduction in time spent on manual schema reconciliation and "mucking" scripts.
Ingress Velocity: Immediate availability of collaborator data within the unified interface post-upload.
Data Transparency: Zero-friction navigation across local and remote data assets in a single terminal or GUI session.

