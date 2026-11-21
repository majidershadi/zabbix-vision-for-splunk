# Zabbix Vision for Splunk 1.1.2

21 November 2026 · Public beta · Apache-2.0

The setup page now displays the specific reason for a rejected connection save when Splunk returns it. A new profile with no API token, for example, prompts you to enter a token.

- Errors identify which step failed when writing a token, optional private-key passphrase, or connection settings.
- If the connection saves and Splunk rejects the final setup flag, the page reports that the connection saved and displays a warning.
- If Splunk Web returns its own error, Setup displays the HTTP status and troubleshooting guidance.

Install the `.tar.gz` over `zabbix_vision`, restart Splunk, and reload Setup. The existing profile and credential formats are compatible with 1.1.1. If you encountered an error in 1.1.1, check **Existing connection** before submitting your token again. See [setup troubleshooting](TROUBLESHOOTING.md).

Setup behavior was verified locally with simulated Splunk responses.
