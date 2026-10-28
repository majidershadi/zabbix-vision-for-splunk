# LinkedIn post — copy only the post body

Zabbix tells you that a trigger fired. During an investigation, I usually need a few more answers:

Who changed the configuration?
Was there a failed login?
Which action asked an agent to run a command?
Did the agent record it?

I built Zabbix Vision for Splunk to bring those records into the same investigation workflow.

The first public beta includes six dashboards, token-based collection, custom API paths, CA and mutual-TLS controls, native Splunk credential storage, and data models for the searches that benefit from them.

The less visible work took just as much attention: version-aware Zabbix authentication, checkpoints that stop on a potentially truncated second, empty snapshot markers, and collection health you can monitor from Zabbix itself.

Core live testing covered Zabbix 6.0, 7.0 and 7.4 on Splunk Enterprise 10.4.1. The suite has 33 automated tests; all 32 dashboard searches passed in the lab.

One boundary matters: API audit records do not describe every agent process. The guide explains where agent logs, auditd, Sysmon or EDR evidence are needed. I would rather make that gap explicit than turn an empty panel into a claim of complete visibility.

The source, release and engineering write-up are in the first comment. If you operate Zabbix and Splunk together, I would be interested in the investigation question your current integration struggles to answer.

#Splunk #Zabbix #Observability #SecurityOperations #OpenSource

---

## First comment — post immediately after the main post

Engineering write-up and deployment context:
https://majidershadi.github.io/articles/zabbix-vision-for-splunk/

Source, documentation and issues:
https://github.com/majidershadi/zabbix-vision-for-splunk

Install package and checksum:
https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0

## Image

Attach `zabbix-vision-linkedin.png`. Alt text: Red Zabbix infrastructure and audit/agent evidence cards converge into an eye-shaped search lens beside the title Zabbix Vision for Splunk. Conceptual product illustration, not a dashboard screenshot or an exact data-flow diagram; agent logs need a separate forwarding path.

## Publishing notes

Keep URLs in the first comment as in the REST Profiler workflow. This is a prepared post, not a claim that LinkedIn has published it. Add the actual Medium permalink later only if that article is published; do not substitute an invented URL.
