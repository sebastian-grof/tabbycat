.. _dr-exports:

DR exports
==========

This fork exports confirmed adjudicator feedback and tournament adjudication
counts to DR. Open **Site tools → API Exports**, select tournaments, choose
**Feedback**, **Judge activity**, or **Both**, and click **Export to DR**.
Nothing is sent automatically when feedback is saved or confirmed.

The request saves a job and returns immediately. A separate worker prepares
records in batches of 100 and sends batches of 25, one HTTP request at a time.
It keeps processing without further clicks or an open browser. Ordinary exports
skip records whose content has already been acknowledged. **Force re-export**
resends unchanged content using the same DR idempotency keys.

Progress and recovery
---------------------

The progress page shows preparation, sending, waiting, failed and unchanged
records, and resumes its display after a reload. It polls every two seconds while
visible, slows down on connection errors, and stops frequent polling when complete.
History is paginated and can be filtered by tournament, data type and outcome.

* **Pause** stops after the in-flight request. **Resume** continues the saved job.
* Temporary network errors, HTTP 429 and server errors retry automatically up to
  eight attempts, with exponential backoff, jitter and ``Retry-After`` support.
* A 401/403 or disabled/unconfigured endpoint blocks that data stream. The other
  stream in the same job can finish. Fix configuration and click **Resume**.
* Invalid source data and other client errors require attention. Correct source
  data and start a new export; **Retry failed** retries an existing prepared
  snapshot without rebuilding it. HTTP 409 is a conflict, not a successful send.
* Jobs run in creation order. A paused or blocked oldest job holds later jobs.
* A crashed worker's claim is recovered after its 120-second lease expires.
  Results from an expired worker cannot overwrite the recovered job.

Each record is frozen when prepared, rather than when the start button is clicked.
New records beyond the source-ID upper bound captured at job creation wait for a
new export. Source edits after preparation are exported only in a later manual
job. Saved payloads survive deletion of their local source. A failed older version
cannot overwrite a newer version already delivered to DR.

Delivery is at least once: if DR accepts a request but its response is lost, the
worker retries the identical body and idempotency key. DR must honor that key to
prevent duplicates. The existing v2 payload and HTTP 200/201 acknowledgement
contract are unchanged; no bulk API endpoint is required.

Deployment
----------

Apply migrations before starting the new web and worker versions::

    python tabbycat/manage.py migrate
    python tabbycat/manage.py collectstatic --noinput

Build frontend assets using the normal deployment build. Set these variables on
both the web and export worker services:

* ``SDA_JUDGES_FEEDBACK_EXPORT_ENABLED`` and ``SDA_JUDGES_FEEDBACK_API_URL``
* ``SDA_JUDGES_FEEDBACK_API_TOKEN``
* ``SDA_JUDGES_ACTIVITY_EXPORT_ENABLED`` and ``SDA_JUDGES_ACTIVITY_API_URL``
* ``SDA_JUDGES_ACTIVITY_API_TOKEN`` (falls back to the feedback token)
* ``FEEDBACK_EXPORT_TIMEOUT`` and ``ADJUDICATOR_STATS_EXPORT_TIMEOUT`` (default
  10 seconds, bounded to 1–30 seconds in the HTTP transport)

The existing non-SDA environment-variable aliases remain supported. Enabled flags
now authorize sending; they do not enable automatic exports. Credentials and
endpoint URLs are never included in the workspace's status API.

Run the dedicated process under a supervisor::

    python tabbycat/manage.py feedbackexport worker

The Docker and Dokploy compose files include an independent ``exports`` service
with restart/health monitoring; rebuild and start it alongside ``web`` and
``worker``. It uses the same database/configuration as the web service, waits for
web startup/migrations, and has a 45-second graceful-shutdown period. The existing
Channels worker continues to handle notifications, allocation and venues.
The ``Procfile`` exposes an ``exports`` process separately; provision that process
on Procfile-based hosts. Local ``npm run serve`` and Render's existing npm start
command also launch the exporter. The queue and retry schedule live in PostgreSQL,
not Redis; source preparation still uses the application's normal preference cache.

Check readiness with::

    python tabbycat/manage.py feedbackexport healthcheck

A heartbeat older than 45 seconds is unhealthy. The UI displays this condition;
structured worker logs contain job/item IDs, type, outcome, HTTP status and attempt
count, without request bodies or API tokens. ``worker --once`` processes one batch
and exits, which is useful for diagnostics. A continuously running worker is needed
for automatic draining and retries.

The migration preserves existing events and payloads, and creates no runnable
jobs. The workspace offers **Resume existing backlog** for previously unowned
pending/failed records. Old web forms redirect to the new workspace. Legacy CLI
``queue``, ``send``, and ``retry-failed`` commands create jobs; they no longer send
synchronously. ``--limit`` is accepted for compatibility but jobs drain the whole
selected backlog. Payload inspection and ``--dry-run`` do not send.

Storage and retention
---------------------

Successful events keep a compact receipt, source identifiers, content hash,
idempotency key, delivery time, attempt count and HTTP status. The duplicate
payload and full response are cleared on acknowledgement. Error messages are
limited to 2 KB and response diagnostics to 4 KB.

Prepared events are versioned by content key so a new export cannot overwrite an
older failed snapshot. Multiple jobs referencing the same version share its
payload. Unresolved payloads are retained. Completed, error-free jobs and their
item history are removed after 90 days; unresolved jobs remain available. Older
successful event versions without retained jobs are pruned, keeping the latest
successful receipt per source for deduplication. Receipts for deleted tournaments
remain visible in history, but cannot reconstruct a successful payload after it
has been cleared.

After verifying the new worker on a controlled endpoint and a selected small
export, compact successful legacy records::

    python tabbycat/manage.py feedbackexport cleanup --dry-run
    python tabbycat/manage.py feedbackexport cleanup --batch-size 100

Cleanup is resumable and idempotent. It only compacts successful events and reports
row counts, table/index sizes and payload/response byte totals before and after.
PostgreSQL normally reuses freed space internally; table files may not shrink
immediately. Cleanup does not run a blocking table rewrite or remove unresolved
snapshots. Back up the database before rollout. Do not reverse the old one-event-
per-source schema after multiple prepared versions exist.

Internal endpoints
------------------

All endpoints require existing global export permissions. POST actions require
manage access, session authentication and CSRF protection.

* ``POST /feedback-export/jobs/`` accepts ``tournament_ids``, ``export_types``
  (``feedback``/``activity``), ``force`` and a UUID ``submission_token``. Reusing
  the token returns the same job. JSON clients receive HTTP 202 and job/status URLs.
* ``GET /feedback-export/jobs/<id>/status/`` returns progress and worker health.
* ``GET /feedback-export/jobs/<id>/items/`` returns 50 records per page; accepts
  ``page`` and ``status``. It never returns payloads.
* ``POST /feedback-export/jobs/<id>/pause/``, ``resume/`` and ``retry/`` control a job.

Verification
------------

Run the export suite against PostgreSQL::

    python tabbycat/manage.py test feedbackexport

It covers a 1,000-record export, duplicate submission, competing workers, recovery
and stale-result fencing, fixed retry payloads, rate limits, authentication errors,
retry exhaustion, source deletion, migration of legacy events, compact receipts,
permissions, CSRF, and workspace rendering without rebuilding payloads.
