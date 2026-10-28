# Local AppInspect review

The public release candidate was inspected in precert mode with Splunk AppInspect 4.4.0 on Windows. The completed run reported **0 errors, 0 failures, 0 future failures**. The release includes the report for the final archive.

Ten warning checks remain. They cover Windows-unavailable binary architecture/symlink checks, a SplunkJS informational check, Python-script inventory guidance for old Splunk versions, the presence of a modular input, indexer/Cloud configuration distribution, custom configuration replication, Cloud sc_admin role access and data-model disk usage.

This app targets Linux Splunk Enterprise. There are no bundled native binaries or symlinks. Cloud, Victoria and search-head-cluster placement are not certified; the deployment guide requires one active collector per scope and explains how to place parsing/search knowledge. Metadata intentionally restricts setup and credentials to Enterprise admin. Data-model acceleration is off and summary-storage decisions are documented.

The trusted-library metadata refresh failed during the local run, so the tool used its bundled data. Review with the hosted AppInspect service/Linux environment before marketplace acceptance; the local result may differ from the hosted service. No marketplace or Cloud approval is inferred.

Release fixes included explicit 3.9/3.13 runtime declarations, app ID/version metadata, a reload trigger for the custom connection config and first-run setup state. Saving the first profile marks the app configured. Both python.version (legacy compatibility) and python.required (newer runtime selection) are provided where the extension supports them.
