# Companion upgrade, signing and recovery strategy

Version0.2.0 is an unsigned source-installer developer preview. No automatic
updater, Windows service, scheduled task, Authenticode signature or SmartScreen
acceptance is claimed. A source archive and successful tests do not establish a
safe privileged release. Finish the protected broker installation in YT.md first.

1. Review release notes, declared verification gaps and the package SHA-256 through
   a trusted release channel. Signing is a future release gate when owner signing
   credentials are available. Do not download and execute arbitrary update scripts.
2. Stop observation and disable enforcement. Stop the normal companion and broker.
   Verify owned-rule cleanup with the explicit recovery command before replacing
   code. Preserve unrelated firewall rules and all other security settings.
3. Back up `%LOCALAPPDATA%\NetSentinel\state` locally with its restricted ACLs.
   It contains secrets and network metadata: never upload it to GitHub, a public
   website, a bug report or an AI conversation. Record the version separately.
4. SQLite schema currently uses `PRAGMA user_version=1`. This version refuses
   unknown schemas. There is no v1-to-v2 migration yet. A future schema change
   needs a transactional versioned migration, backup and tested rollback.
5. Keep the old stopped installation outside the new install destination until
   the replacement passes checks. The initial installer refuses an existing
   VERSION file instead of overwriting the running installation. Review actual
   absolute paths before moving/removing any directory. Retain the private state.
6. Install the reviewed replacement, run version and authentication checks, and
   inspect retained quotas before observation/enforcement. Reusing private state
   also reuses saved opt-in enforcement/manual policies; their restart behavior
   must be reviewed rather than mistaken for a new clean installation.
7. Confirm clean startup, failed-broker behavior, metadata persistence, report
   export, stop and recovery. Validate new connections of a controlled executable
   before describing a firewall rule as traffic blocking.

The future signed release should use an administrator-protected broker runtime,
an Authenticode-signed installer/broker, signed versioned update metadata and
authenticated HTTPS delivery with hash verification. Updates must never silently
install Npcap, elevate the public/local web frameworks, start malware scans or
change existing Windows protection settings. A code-signing certificate does
not guarantee SmartScreen acceptance or software safety.

No PostgreSQL schema, research model artifact or host-v1 feature contract is
changed by companion installation. Back up/upgrade the research system separately.
