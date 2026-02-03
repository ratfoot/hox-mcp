Logging InLogging in via the CLI or the web interface follows a similar process. You enter your email address, we'll send a login code to you email, and then you enter that code to get logged in.This is an interactive process, and the workflow is:

 1. Press Enter to send the email
 2. Read the email and copy the code into the terminal
 3. Optionally select a tenant, if your email is associated with multiple tenants

This login information is saved to the default profile.

ProfilesIf you work with multiple emails or multiple tenants from your machine, you can use profiles to manage these. The login command can be used with the --profile= flag to specify a profile name:If the profile doesn't exist, it will be created. If it does exist, the existing profile will be replaced with the new one. To use a specific profile with each command, the --profile= flag can be used again, e.g.Alternatively, the default profile can be set with the switch command:and then other commands can be used against the new default profile:

Finally, several commands are available to manage profiles:Profiles are stored in ~/.hox/config.json, and are a concept that is local to your machine and the hox cli binary.

Inviting New UsersTo invite new users to your tenant, use the invite command:The user will be sent an email with an invite link. After clicking on the link, they'll be able to log into the CLI via the login command, as well as the web UI.

PermissionsPermissions within a tenant are managed via:

 - users assigned to a project with list/read/write permissions, and
 - user capabilities



Project PermissionsEach resource is tied to one project, and each user has certain permissions against any number of projects:The permissions that a user can have against a project are:

 - list (l):Can list the resources of a project, this also includes resource metadata such as name, description, tags, comments. However, the resource contents are not accessible.


 - list+read (lr):In addition to the above, can also read the full contents of a resource.


 - list+read+write (lrw):In addition to the above, can also create, edit, and delete resources within that project.



In the CLI, these permissions can be managed with:and adding a user to a project they're already in will replace their permissions with the new ones.



User CapabilitiesThe other control over permissions is via user capabilities, that are assigned directly to a user. They are quite powerful, so their usage should be carefully considered, and typically limited to system administrators. They are:

 - user_admin: invite, edit and disable users
 - group_admin: create, edit, and delete projects, and assign users to projects
 - resource_admin: full access to all resources, i.e. lrw permissions



# CLI Reference

## Common Arguments

Desc: These arguments can be used across all commands
Args:
    [--profile=NAME]:     Name of the profile to use. If not provided, the default profile is used.
    [--json]:             Output in JSON format.
    [--id-only]:          Output only the ID of the resource(s), separated by new-lines.
    [--no-pretty]:        Do not pretty-print/truncate sizes, UUIDs, or timestamps.
    [--no-progress]:      Force suppression of progress bars.
    [--dump-http]:        Dump HTTP requests and responses to stderr
    [--help]:             Display help for the verb or resource type

## Resource Common

Desc: manage common resource operations. Replace <resource> with the resource type.

Verbs:
  - *get*: hox get <resource> [ID] 
    Desc: list resources or display a single resource
    Args:
      [ID]:                 ID of the resource to display

  - *inspect*: hox inspect <resource> ID 
    Desc: display metadata for a single resource
    Args:
      ID:                   ID of the resource to display

  - *search*: hox search <resource> [--prefix=PREFIX] [--name=NAME]... [--ancestor-of=ID] [--descendant-of=ID] ...
    Desc: find a resource by name or other criteria
    Args:
      [--prefix=PREFIX]:    prefix of the resource name
      [--name=NAME]...:     exact resource name. may be repeated for multiple names
      [--ancestor-of=ID]:   search only for ancestors of this resource ID
      [--descendant-of=ID]:  search only for descendants of this resource ID
      [--tags-json=TAGS-JSON]:  tags to search for, JSON-formatted
      [--tags-stdin]:       decode stdin as JSON-formatted tags
      [--sort=SORT]:        sort by column. Of the form 'COL_NAME[:asc|desc]'. Default is asc. Sort by tags with 'tags.KEY[:asc|desc]'

  - *chproj*: hox chproj <resource> ID PROJECT 
    Desc: change the project for the resource
    Args:
      ID:                   ID of the resource
      PROJECT:              name of the project

  - *rename*: hox rename <resource> ID NEW_NAME 
    Desc: rename a resource
    Args:
      ID:                   ID of the resource
      NEW_NAME:             new name for the resource

  - *tag*: hox tag <resource> ID [--set=TAGS_KVPS] [--unset=TAGS] [--stdin] 
    Desc: view, add, or modify tags for a resource. If no flags are given, displays the tags for the resource
    Args:
      ID:                   ID of the resource
      [--set=TAGS_KVPS]:    set textual tags, in the form of key1=value1,key2=value2
      [--unset=TAGS]:       clear tags by key, in the form of key1,key2
      [--stdin]:            read tags from stdin as JSON. Null values will clear a tag.

  - *delete*: hox delete <resource> ID 
    Desc: delete a resource
    Args:
      ID:                   ID of the resource to delete

  - *clone*: hox clone <resource> ID --new-name=NEW_NAME [--into-project=PROJECT] 
    Desc: clone a resource
    Args:
      ID:                   ID of the resource to clone
      --new-name=NEW_NAME:  name of the new resource
      [--into-project=PROJECT]:  target project to clone into


## Noun: profiles

Desc: Manage credentials and profiles. Profiles are stored locally under ~/.hox/config.json. Profiles can be created or replaced during login with

Alternate Names: profile, profiles
Verbs:
  - *switch*: hox switch profile NAME 
    Desc: switch between different profiles
    Args:
      NAME:                 name of the profile to switch to

  - *get*: hox get profile [NAME] 
    Desc: list profile(s)
    Args:
      [NAME]:               name of the profile to display

  - *edit*: hox edit profile 
    Desc: change the settings of the active profile

  - *delete*: hox delete profile NAME 
    Desc: delete the given profile
    Args:
      NAME:                 name of the profile to delete

  - *rename*: hox rename profile OLD_NAME NEW_NAME 
    Desc: change the name of the specified profile
    Args:
      OLD_NAME:             old name for the profile
      NEW_NAME:             new name for the profile


## Noun: family

Desc: manage family resources

Alternate Names: fm, family
Verbs:
  - *get*: hox get fm ID 
    Desc: get resource relationships
    Args:
      ID:                   ID of the resource


## Resource: assemblies

Desc: manage assembly resources

Alternate Names: asm, assemblies, assembly
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *import*: hox import asm --name=NAME --f=FILE [--force] [--ploidy-map=PLOIDY_MAP_FILE] ...
    Desc: import a FASTA-formatted assembly
    Args:
      --name=NAME:          name of the assembly
      --f=FILE:             path to the FASTA file
      [--force]:            ignore suspicious file extensions
      [--ploidy-map=PLOIDY_MAP_FILE]:  file containing a ploidy map for the assembly
      [--fixed-ploidy=FIXED_PLOIDY]:  use a constant ploidy across the whole assembly
      [--unknown-ploidy]:   deliberately omit ploidy map

  - *view*: hox view asm ID [--regions=REGIONS] 
    Desc: display part of the assembly in FASTA format
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to view, in the form of chr1:1-100,chr2:200-300

  - *attach*: hox attach asm ASSEMBLY_ID --features=FEATURES_ID 
    Desc: attach a features resource to an assembly
    Args:
      ASSEMBLY_ID:          ID of the assembly
      --features=FEATURES_ID:  ID of the features resource to attach

  - *detach*: hox detach asm ASSEMBLY_ID --features=FEATURES_ID 
    Desc: detach a features resource from an assembly
    Args:
      ASSEMBLY_ID:          ID of the assembly
      --features=FEATURES_ID:  ID of the features resource to detach

  - *export*: hox export asm ID [--regions=REGIONS] [--format=FORMAT] 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to export, in the form of chr1:1-100,chr2:200-300
      [--format=FORMAT]:    format of the exported data (default: fasta)


## Resource: individuals

Desc: manage individuals resources

Alternate Names: idv, individuals
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create idv --name=NAME 
    Desc: create a new individual
    Args:
      --name=NAME:          name of the individual

  - *attach*: hox attach idv INDIVIDUAL_ID --sample=SAMPLE_ID 
    Desc: attach a sample to an individual
    Args:
      INDIVIDUAL_ID:        ID of the individual
      --sample=SAMPLE_ID:   ID of the sample to attach

  - *detach*: hox detach idv INDIVIDUAL_ID --sample=SAMPLE_ID 
    Desc: detach a sample from an individual
    Args:
      INDIVIDUAL_ID:        ID of the individual
      --sample=SAMPLE_ID:   ID of the sample to detach


## Resource: samples

Desc: manage sample resources

Alternate Names: sample, samples, smpl
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create smp --name=NAME [--individual=INDIVIDUAL_ID] 
    Desc: create a new sample
    Args:
      --name=NAME:          name of the individual
      [--individual=INDIVIDUAL_ID]:  ID of the individual to associate with the sample

  - *attach*: hox attach smp SAMPLE_ID --reads=READS_ID 
    Desc: attach reads to a sample
    Args:
      SAMPLE_ID:            ID of the sample
      --reads=READS_ID:     ID of the reads resource to attach

  - *detach*: hox detach smp SAMPLE_ID --reads=READS_ID 
    Desc: detach reads from a sample
    Args:
      SAMPLE_ID:            ID of the sample
      --reads=READS_ID:     ID of the reads resource to detach


## Resource: sets

Desc: manage set resources

Alternate Names: set, sets, st
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create set --name=NAME 
    Desc: create a new set, with no attached reads
    Args:
      --name=NAME:          name of the set

  - *import*: hox import set --f=FILE [--force] 
    Desc: create a new set with reads via a yaml file
    Args:
      --f=FILE:             path to the yaml file describing the import
      [--force]:            ignore suspicious file extensions


## Resource: reads

Desc: manage read resources

Alternate Names: rd, read, reads
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *view*: hox view reads READS_ID [--start=START] [--limit=LIMIT] 
    Desc: show FASTQ-formatted records by index
    Args:
      READS_ID:             ID of the reads resource
      [--start=START]:      record at which to start viewing, zero-based (default: 0)
      [--limit=LIMIT]:      number of records to show (default: 10)

  - *import*: hox import reads [--name=NAME] --r1=R1_FILE --r2=R2_FILE [--paired] ...
    Desc: import a FASTQ-formatted readgroup
    Args:
      [--name=NAME]:        name of the readgroup (if --set provided, and --name not provided, assigned automatically)
      --r1=R1_FILE:         path to the R1 FASTQ file
      --r2=R2_FILE:         path to the R2 FASTQ file (for paired reads)
      [--paired]:           r1 contains interleaved read pairs
      [--set=SET_ID]:       ID of the set to attach the reads to
      [--quality-bins=QUALITY-BINS]:  perform quality binning into the given number of bins (8 is recommended)
      [--force]:            ignore suspicious file extensions
      [--from-accession=SRA_NUM]:  SRA accession number (for SRA import)
      [--name-prefix=PREFIX]:  prefix to append to SRA run IDs (for SRA import)

  - *attach*: hox attach reads READS_ID --set=SET_ID 
    Desc: attach a reads resource to a set. Note: reads may only be attached to a set once
    Args:
      READS_ID:             ID of the reads resource to attach
      --set=SET_ID:         ID of the set to attach the reads to

  - *detach*: hox detach reads READS_ID --set=SET_ID 
    Desc: detach a reads resource from a set
    Args:
      READS_ID:             ID of the reads resource to detach
      --set=SET_ID:         ID of the set to detach the reads from

  - *qc*: hox qc reads ID 
    Desc: display quality control statistics for a reads resource
    Args:
      ID:                   ID of the resource

  - *tablestat*: hox tablestat reads ID 
    Desc: show detailed storage information for a resource
    Args:
      ID:                   ID of the resource

  - *export*: hox export reads ID 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource


## Resource: alignments

Desc: manage alignment resources

Alternate Names: aln, alignment, alignments
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create aln [--name=NAME] [--set=SET_ID] [--reads=READS_IDS] --assembly=ASSEMBLY_ID 
    Desc: create an alignment by aligning reads to an assembly
    Args:
      [--name=NAME]:        name to assign to the new alignment (if --set provided and --name not provided, assigned automatically)
      [--set=SET_ID]:       ID of the set containing the reads to align
      [--reads=READS_IDS]:  IDs of the reads to align
      --assembly=ASSEMBLY_ID:  ID of the assembly against which the reads will be aligned

  - *import*: hox import aln [--name=NAME] --f=FILE [--force] [--assembly=ASSEMBLY_ID] 
    Desc: import a SAM-formatted alignment
    Args:
      [--name=NAME]:        name to assign to the new alignment
      --f=FILE:             path to the SAM file, optionally compressed (.gz, .zstd)
      [--force]:            ignore suspicious file extensions
      [--assembly=ASSEMBLY_ID]:  ID of the assembly against which the reads were aligned

  - *view*: hox view aln ALIGNMENT_ID --regions=REGIONS [--header] 
    Desc: view part of a SAM-formatted alignment
    Args:
      ALIGNMENT_ID:         ID of the alignment resource
      --regions=REGIONS:    regions to view, in the form of chr1:1-100,chr2:2000-
      [--header]:           if set, the SAM header will be included

  - *qc*: hox qc aln ID 
    Desc: display quality control statistics for an alignment
    Args:
      ID:                   ID of the resource

  - *tablestat*: hox tablestat aln ID 
    Desc: show detailed storage information for a resource
    Args:
      ID:                   ID of the resource

  - *export*: hox export aln ID [--regions=REGIONS] [--format=FORMAT] 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to export, in the form of chr1:1-100,chr2:200-300
      [--format=FORMAT]:    format of the exported data (default: sam)


## Resource: pseudoalignments

Desc: manage pseudo-alignment resources

Alternate Names: pal, pseudoalignment, pseudoalignments
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create pal [--name=NAME] [--set=SET_ID] [--reads=READS_IDS] --assembly=ASSEMBLY_ID ...
    Desc: create an pseudo-alignment by aligning reads to an assembly with attached feature annotations
    Args:
      [--name=NAME]:        name to assign to the new alignment (if --set provided and --name not provided, assigned automatically)
      [--set=SET_ID]:       ID of the set containing the reads to align
      [--reads=READS_IDS]:  IDs of the reads to align
      --assembly=ASSEMBLY_ID:  ID of the assembly against which the reads will be aligned
      --features=FEATURES_ID:  ID of the feature annotations to use
      --geometry=GEOMETRY:  the geometry specifies how the cell barcode and molecular identifier are extracted from paired reads in scRNA experiments. This may either be a literal string identifying the chemistry or a piscem geometry specification. The known chemistry strings are:

     - 10x-chromium-3p-v2 => 1{b[16]u[10]x:}2{r:}
     - 10x-chromium-3p-v3 => 1{b[16]u[12]x:}2{r:}
     - 10x-chromium-3p-v4 => 1{b[16]u[12]x:}2{r:}
     - 10x-chromium-5p-v2 => 1{b[16]u[10]x:}2!{r:}
     - 10x-chromium-5p-v3 => 1{b[16]u[12]x:}2!{r:}
     - 10x-chromium-5p-v4 => 1{b[16]u[12]x:}2!{r:}
     - hox-ont-10x-5p-v1 => HoX-specific assay


      [--type=TYPE]:        type of pseudo-alignment to perform (default: scRNA)
      [--extra-probes=ASM_IDS]:  extra assemblies to use as probe sequences for CITE-seq

  - *view*: hox view pal PSEUDOALIGNMENT_ID --regions=REGIONS 
    Desc: view part of a PAF-formatted pseudo-alignment
    Args:
      PSEUDOALIGNMENT_ID:   ID of the pseudoalignment resource
      --regions=REGIONS:    regions to view, in the form of chr1:1-100,chr2:2000-

  - *qc*: hox qc pal ID 
    Desc: display quality control statistics for a pseudo-alignment
    Args:
      ID:                   ID of the resource

  - *tablestat*: hox tablestat pal ID 
    Desc: show detailed storage information for a resource
    Args:
      ID:                   ID of the resource

  - *export*: hox export pal ID [--regions=REGIONS] [--format=FORMAT] 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to export, in the form of chr1:1-100,chr2:200-300
      [--format=FORMAT]:    format of the exported data (default: paf)


## Resource: variants

Desc: manage variants resources

Alternate Names: vars, variants
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create vars --alignments=ALIGNMENTS_IDS [--name=NAME] [--stream] [--regions=REGIONS] ...
    Desc: create or stream variants from alignments
    Args:
      --alignments=ALIGNMENTS_IDS:  IDs of the alignments to use for variant calling
      [--name=NAME]:        name of the new variants resource (if not streaming)
      [--stream]:           stream output to stdout rather than creating a resource
      [--regions=REGIONS]:  if streaming, regions to call variants in, in the form of chr1:1-100,chr2:2000-
      [--sex=SEX]:          if streaming, output genotypes with ploidy determined via sex
      [--assume-ploidy=PLOIDY]:  if streaming, output genotypes with this ploidy and ignore the ploidy map

  - *import*: hox import vars [--name=NAME] --f=FILE [--force] --assembly=ASSEMBLY_ID 
    Desc: import a VCF-formatted variants resource
    Args:
      [--name=NAME]:        name of the new variants resource
      --f=FILE:             path to the VCF file, optionally compressed (.gz, .zstd)
      [--force]:            ignore suspicious file extensions
      --assembly=ASSEMBLY_ID:  ID of the assembly the variants are called against

  - *view*: hox view vars VARIANTS_ID --regions=REGIONS 
    Desc: view part of a VCF-formatted variants resource
    Args:
      VARIANTS_ID:          ID of the variants resource
      --regions=REGIONS:    regions to view, in the form of chr1:1-100,chr2:2000-

  - *export*: hox export vars ID [--regions=REGIONS] [--format=FORMAT] 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to export, in the form of chr1:1-100,chr2:200-300
      [--format=FORMAT]:    format of the exported data (default: vcf)


## Resource: genotypes

Desc: manage genotypes resources

Alternate Names: genotypes, gts
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create genotypes --name=NAME [--variants=VARIANTS_ID] [--alignments=ALIGNMENTS_IDS] --sex=SEX 
    Desc: create a genotypes resource from variants and alignments
    Args:
      --name=NAME:          name of the new genotypes resource
      [--variants=VARIANTS_ID]:  ID of the variants resource to use for genotyping
      [--alignments=ALIGNMENTS_IDS]:  ID of the alignments resource to use for genotyping
      --sex=SEX:            sex of the sample (for determining ploidy)

  - *view*: hox view genotypes GENOTYPES_ID --regions=REGIONS 
    Desc: view part of a genotypes resource
    Args:
      GENOTYPES_ID:         ID of the genotypes resource
      --regions=REGIONS:    regions to view, in the form of chr1:1-100,chr2:2000-

  - *export*: hox export genotypes ID [--regions=REGIONS] [--format=FORMAT] 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to export, in the form of chr1:1-100,chr2:200-300
      [--format=FORMAT]:    format of the exported data (default: vcf)


## Resource: features

Desc: manage features resources

Alternate Names: features, ft
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *import*: hox import features [--name=NAME] --f=FILE [--force] 
    Desc: import a GFF3-formatted features resource
    Args:
      [--name=NAME]:        name of the new features resource
      --f=FILE:             path to the GFF3 file, optionally compressed (.gz, .zstd)
      [--force]:            ignore suspicious file extensions

  - *view*: hox view features FEATURES_ID [--regions=REGIONS] [--format=FORMAT] [--type=FEATURE_TYPE] [--attr-name=ATTRIBUTE_NAME] 
    Desc: view part of a GFF3-formatted features resource
    Args:
      FEATURES_ID:          ID of the features resource
      [--regions=REGIONS]:  regions to view, in the form of chr1:1-100,chr2:2000-
      [--format=FORMAT]:    output format, either gff3 or bed4 (default: gff3)
      [--type=FEATURE_TYPE]:  feature type to output (only for bed4 format)
      [--attr-name=ATTRIBUTE_NAME]:  attribute name to output in the name column (only for bed4 format)


## Resource: gene-matrix

Desc: manage gene-matrix resources

Alternate Names: gex, gene-matrix
Resource Common Verbs: get, inspect, search, chproj, rename, tag, delete, clone
Additional Verbs:
  - *create*: hox create gex --name=NAME --pal-id=PAL_ID --cell-filter=CELL_FILTER 
    Desc: create a gene-matrix resource from a pseudoalignment
    Args:
      --name=NAME:          name of the new gene-matrix resource
      --pal-id=PAL_ID:      ID of the pseudoalignment resource
      --cell-filter=CELL_FILTER:  Cell filter expression. Should be one of the following:

     - expect=NAssume the assay intended for there to be N true cells, and determine which barcodes correspond to "true" cells automatically. This is typically the best option when the number of input cells is known (approximately).
     - force=NForce the top N barcodes (ranked by UMI count) to be called as cells. This is typically only necessary when the "expect" method doesn't yield reasonable results.
     - umis=NForce barcodes with at least N UMIs to be called as cells.



  - *view*: hox view gex GENE_MATRIX_ID [--format=FORMAT] [--only-barcodes] [--only-genes] [--filter=FILTER] ...
    Desc: view gene matrix information
    Args:
      GENE_MATRIX_ID:       ID of the gene-matrix resource
      [--format=FORMAT]:    output format, either a CellRanger compatible MEX file, or pca3 data as a TSV (default: mex.zip)
      [--only-barcodes]:    output a TSV of per-barcode filtered UMI counts
      [--only-genes]:       output a TSV of per-gene filtered UMI counts
      [--filter=FILTER]:    filter query for non-MEX file outputs
      [--force]:            ignore suspicious format flag

  - *qc*: hox qc gex ID 
    Desc: display quality control statistics for a gene-matrix
    Args:
      ID:                   ID of the resource

  - *export*: hox export gex ID [--regions=REGIONS] [--format=FORMAT] 
    Desc: create a download-able version of a resource. If no regions are given, exports the entire resource
    Args:
      ID:                   ID of the resource
      [--regions=REGIONS]:  regions to export, in the form of chr1:1-100,chr2:200-300
      [--format=FORMAT]:    format of the exported data (default: mtx)


## Noun: exports

Desc: manage exports

Alternate Names: export, ex, exports
Verbs:
  - *get*: hox get export [EXPORT_ID] 
    Desc: list exports or display a single export
    Args:
      [EXPORT_ID]:          ID of the export to display

  - *inspect*: hox inspect export EXPORT_ID 
    Desc: display metadata for a single export
    Args:
      EXPORT_ID:            ID of the export to display

  - *download*: hox download export EXPORT_ID [--o=FILE] [--wait] 
    Desc: download a completed export
    Args:
      EXPORT_ID:            ID of the export to download
      [--o=FILE]:           Path to save the downloaded file. Defaults to a name based on the exported resource
      [--wait]:             Wait if the export is not yet complete

  - *delete*: hox delete export EXPORT_ID 
    Desc: delete an export
    Args:
      EXPORT_ID:            ID of the export to delete


## Noun: jobs

Desc: manage jobs

Alternate Names: job, jobs
Verbs:
  - *get*: hox get jobs [--resource-id=RESOURCE_ID] 
    Desc: list all jobs or display jobs related to a resource
    Args:
      [--resource-id=RESOURCE_ID]:  restrict output to only jobs related to the given resource


## Noun: users

Desc: manage users

Alternate Names: user, users, usr
Verbs:
  - *get*: hox get users [USER_ID] 
    Desc: list users or display a single user
    Args:
      [USER_ID]:            ID of the user to display

  - *invite*: hox invite users EMAIL 
    Desc: invite a new user via email
    Args:
      EMAIL:                email address of the user to invite


## Noun: projects

Desc: manage projects

Alternate Names: proj, project, projects
Verbs:
  - *get*: hox get projects [PROJECT_ID] [--user=USER_ID] 
    Desc: list projects or display a single project, optionally filtered to a specific user
    Args:
      [PROJECT_ID]:         ID of the project to display
      [--user=USER_ID]:     ID of the user to filter by

  - *inspect*: hox inspect projects PROJECT_ID 
    Desc: display metadata for a single project
    Args:
      PROJECT_ID:           ID of the project to display

  - *switch*: hox switch projects PROJECT_ID 
    Desc: change your default project
    Args:
      PROJECT_ID:           ID of the project to switch to

  - *create*: hox create projects NAME 
    Desc: create a new project
    Args:
      NAME:                 name of the project

  - *edit*: hox edit projects PROJECT_ID [--add-user=USER_ID] [--remove-user=USER_ID] [--perm=PERMISSION] 
    Desc: edit the project's members and permissions
    Args:
      PROJECT_ID:           ID of the project to edit
      [--add-user=USER_ID]:  ID of the user to add to the project
      [--remove-user=USER_ID]:  ID of the user to remove from the project
      [--perm=PERMISSION]:  permission level to assign to the user for the project (l, lr, lrw) => (list, list/read, list/read/write)

  - *rename*: hox rename projects PROJECT_ID NEW_NAME 
    Desc: rename a project
    Args:
      PROJECT_ID:           ID of the project to rename
      NEW_NAME:             new name for the project

  - *delete*: hox delete projects PROJECT_ID 
    Desc: delete a project
    Args:
      PROJECT_ID:           ID of the project to delete


## Additional Verbs

Desc: HoX Additional Commands

Verbs:
  - *login*: hox login --email=EMAIL [--tenant-id=TENANT-ID] 
    Desc: Login to the HoX server with an email
    Args:
      --email=EMAIL:        email address to login with
      [--tenant-id=TENANT-ID]:  force login to a specific tenant

  - *help*: hox help [VERB] [RESOURCE] 
    Desc: display help for a verb or resource type
    Args:
      [VERB]:               name of the verb to display help for
      [RESOURCE]:           name of the resource to display help for

