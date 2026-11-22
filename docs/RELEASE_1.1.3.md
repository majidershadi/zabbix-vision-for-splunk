# Zabbix Vision for Splunk 1.1.3

22 November 2026 · Public beta · Apache-2.0

Corrects Linux file permissions in the install archive for Splunk AppInspect's `check_for_bin_files` check. The example UserParameter wrapper and other interpreter-run files are packaged as `0644`. The modular input remains executable. CI now checks the permissions in the generated archive.

Use the 1.1.3 install archive for Splunkbase review or upgrade an existing `zabbix_vision` installation using the [installation guide](INSTALLATION.md). The setup fix from 1.1.2 is included.
