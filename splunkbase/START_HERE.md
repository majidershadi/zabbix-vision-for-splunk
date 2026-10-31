# Splunkbase submission kit — Zabbix Vision for Splunk

Prepared 1 November 2026 for **1.1.0 public beta**. This is a submission kit, not a marketplace approval. This release adds opt-in UserParameter execution collection, a dashboard and agent deployment examples.

## Upload and copy map

| Submission item | File or value |
| --- | --- |
| Installable app | `dist/zabbix_vision-1.1.0.tar.gz` |
| SHA-256 | Verify against the accompanying release checksum file |
| Checksum file | `dist/zabbix_vision-1.1.0.tar.gz.sha256` |
| Local inspection report | `dist/appinspect-1.1.0.json`; explanation in `docs/APPINSPECT.md` |
| App name | Zabbix Vision for Splunk |
| App ID / version / status | `zabbix_vision` / `1.1.0` / Beta |
| Description and Details copy | `splunkbase/LISTING.md` |
| Installation copy | `splunkbase/INSTALLATION.md` |
| Release notes copy | `splunkbase/RELEASE_NOTES.md` |
| Troubleshooting copy | `splunkbase/TROUBLESHOOTING.md` |
| Support, privacy and license copy | `splunkbase/SUPPORT_PRIVACY.md` |
| Screenshots, order and captions | `splunkbase/SCREENSHOTS.md` |
| Icon | `zabbix_vision/static/appIcon.png` (36 × 36); 72 × 72 variant alongside |
| High-resolution original mark | `docs/assets/zabbix-vision-icon.png` (512 × 512) |
| Full user/developer guide | `README.md` and `docs/` |
| UserParameter execution detection | `docs/USERPARAMETER_API.md`; wrapper/log-item/API setup, plus independent OS telemetry in `docs/USERPARAMETER_EXECUTION.md` |

Upload the `.tar.gz` as the app. **Do not upload this submission-kit ZIP or GitHub's source ZIP as the app package.** Markdown documents are copy-ready source: use the matching listing fields or documentation links provided by the current submission interface. Do not paste this operator checklist into the public description.

## Before submitting

1. Sign in with the owner's actual Splunk.com account. Use its real author username where the submission form and launcher metadata require it. `Majid Ershadi` is the current package's display author; the Splunk.com username has not been confirmed.
2. Select **App**, Apache License 2.0, developer support via GitHub Issues, and the appropriate current IT operations/security category choices.
3. Choose hosting deliberately. Suggested selection: Splunkbase-hosted, publicly downloadable. Splunk documents that the hosting selection cannot be changed after submission.
4. Upload the verified app archive. Choose Linux Splunk Enterprise; live verification was on 10.4.1. Select only compatibility versions accepted by the portal that have actually passed your acceptance process. Do not select Splunk Cloud certification.
5. Paste the descriptions, installation and release notes. Add the documentation, support and website URLs from LISTING.md. Provide a real monitored owner contact if the portal requires email; no contact address was invented for this kit.
6. Upload the screenshots and icon. Use the 623 × 350 PNG previews if the portal requires the documented legacy splash size; keep full-resolution PNGs for gallery fields that accept them.
7. Review the AppInspect warnings. The local Windows run had 0 errors, 0 failures and 11 warnings. Hosted/Linux inspection and Splunk's manual review can differ. If any archive content or author metadata changes, rebuild and inspect the exact replacement artifact before uploading; do not silently replace the existing GitHub release binary.
8. Review the final listing preview, confirm all URLs resolve, and complete the owner's required legal agreements and submission action. This kit does not complete those account/legal steps.

## What changed in this kit

The lab's older `zabbix_connect` prototype had no `static` icon files. Its six standard icon/logo assets were restored from the public app, and browser loading of the icon was verified. The public `zabbix_vision` release already contained the correct assets and was verified separately. Screenshots in this kit show **Zabbix Vision**, not the old prototype. That icon correction was lab-only. Version 1.1.0 separately adds UserParameter runtime support; the original 1.0.0 release archive remains unchanged.

## Official submission references

- [Splunkbase publishing workflow](https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/)
- [Configure listing information](https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/submit-splunkbase-apps/configure-app-information/)
- [File and image standards](https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/approvalcriteria/)
- [App icon and logo placement](https://dev.splunk.com/enterprise/docs/developapps/manageknowledge/configureappproperties/)

References originally checked 30 October 2026. Use the actual submission form's current constraints if its gallery fields differ from the legacy package splash standard.
