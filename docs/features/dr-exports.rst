.. _dr-exports:

DR exports
==========

This fork exports confirmed adjudicator feedback, tournament adjudication
counts, complete tournament results and league seasons' published break standings
to DR. Open **Site tools → API
Exports**, select tournaments, choose **Feedback**, **Judge activity**, **Both**
or **Results** (*Výsledky*), and click **Export to DR**. Nothing is sent
automatically when feedback or ballots are saved or confirmed.

The request saves a job and returns immediately. A separate worker prepares
records in batches of 100 and sends batches of 25, one HTTP request at a time.
It keeps processing without further clicks or an open browser. Ordinary exports
skip records whose content has already been acknowledged. **Force re-export**
resends unchanged content using the same DR idempotency keys.

Results
-------

The **Results** stream sends one complete snapshot per tournament to
``POST /api/v1/results/``, following the contract in Databáza SDA's
``docs/results-api.md`` (v1). A snapshot contains:

* the tournament with its format (teams per debate, speakers per team, replies,
  cross-examinations, and the team and speaker standings precedence and extra
  metrics as metric keys in their configured order) and, when the tournament is in a Breaks season, the season,
  league and break-tournament metadata;
* institutions used by the tournament's teams and adjudicators, break categories
  and speaker categories;
* teams with their speakers (name, optional email, the ``anonymous`` flag and
  speaker categories) and the linked Breaks season team;
* adjudicators (name, optional email, institution and the anonymous, trainee,
  independent and adjudication-core flags);
* rounds with their motions, and every debate that has a **confirmed** ballot:
  sides, win/points/score/votes, speaker scores including replies and ghost
  speeches, score-criterion breakdowns, cross-examination scores and the panel.
  Draft, unconfirmed and discarded ballots are never sent;
* the team tab and speaker tabs after the last preliminary round, generated with
  the tournament's configured standings metrics: the open speaker tab, one tab per
  speaker category, and the reply tab;
* the breaking teams of each break category.

Silent rounds are included; Databáza SDA decides what is public. Many debaters
are minors, so the payload carries only what the contract lists: no phone
numbers, gender, pronouns, URL keys, private URLs or IP addresses.

Each snapshot replaces everything DR stored for that tournament. Its
idempotency key is ``tabbycat-sda:results:<tournament id>:<content hash>:v1``,
where the hash covers the content but not ``generated_at``. Exporting an
unchanged tournament again is skipped as *Unchanged*; any correction produces a
new key, and **Force re-export** resends the identical body with its original key
and ``generated_at``. Bodies over 1 MB are sent with ``Content-Encoding: gzip``.
Snapshots are prepared three tournaments per batch, so long tabs stay inside the
worker lease.

The stream is **disabled by default** because DR's endpoint is new. A 404 from DR
is treated like a configuration problem: the results stream is blocked (other
streams continue) until the URL is fixed or DR is deployed, then **Resume**.

To inspect a snapshot without sending anything::

    python tabbycat/manage.py feedbackexport results-payload <tournament id>

``feedbackexport queue-results [--tournament <slug>] [--force]`` creates a
results job from the command line. An example payload generated from the test
fixture is kept in ``docs/features/dr-results-payload-example.json`` for the DR
side to test against (IDs come from the test database); regenerate it from the
``tabbycat`` directory with::

    RESULTS_EXAMPLE_PATH=../docs/features/dr-results-payload-example.json \
        python manage.py test -t . feedbackexport.tests.test_results

Season breaks
-------------

Each league season's published break standings go to
``POST /api/v1/season-breaks/`` (payload v1, *Season breaks payload* in
Databáza SDA's ``docs/tabbycat-api.md``). Unlike the other streams this one is
triggered by the editor: clicking **Publish public snapshot** on a break season's
overview page saves an export job for that season, and the export worker sends it.
The body is::

    {"version": 1, "source_system": "tabbycat-sda", "generated_at": "…",
     "season": "2026/2027",
     "snapshot": <BreakSeason.public_snapshot>}

``snapshot`` is the published snapshot exactly as stored; nothing is recomputed,
and Databáza SDA never recomputes it either. ``season`` is read from the
snapshot's season name or slug (``2026/2027`` or ``2026-2027``) and is left out
when neither names one; DR then derives it from ``snapshot.published_at``.

The idempotency key is ``tabbycat-sda:season-breaks:<season id>:<published_at>``.
A published snapshot never changes, so a republish always gets a new key and
replaces the season in DR, while a retry of the same snapshot resends the
identical body (``generated_at`` is fixed when the snapshot is first prepared).
An older snapshot is never delivered after a newer one of the same season.

The overview page's *Public snapshot* card shows the last send status (queued,
sent with its HTTP status, or the DR error) and a **Send again to Databáza SDA**
button, which queues a forced re-send of the current snapshot. Publishing never
fails because of the export: if the stream is off or no job can be saved, the
snapshot is still published and the card says so. Snapshots published while the
stream was off can be sent later with that button or with
``feedbackexport queue-season-breaks [--season <slug>] [--force]``.

The stream uses the results token (``results:write`` scope) and, unless set
explicitly, follows the results stream's switch and host. A 404 blocks this
stream until the URL is fixed, like the results stream. Bodies are plain JSON;
DR accepts gzip only for results. To inspect a payload::

    python tabbycat/manage.py feedbackexport season-breaks-payload <season id>

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
* ``SDA_JUDGES_RESULTS_EXPORT_ENABLED`` (default off) and
  ``SDA_JUDGES_RESULTS_API_URL`` (e.g. ``https://rozhodcovia.sda.sk/api/v1/results/``)
* ``SDA_JUDGES_RESULTS_API_TOKEN`` (falls back to the feedback token; DR needs the
  ``results:write`` scope on the ``tabbycat`` client)
* ``SDA_JUDGES_SEASON_BREAKS_EXPORT_ENABLED`` (default: the value of
  ``SDA_JUDGES_RESULTS_EXPORT_ENABLED``) and ``SDA_JUDGES_SEASON_BREAKS_API_URL``
  (default: the results URL's host + ``/api/v1/season-breaks/``); the results
  token is used. Blank values count as unset.
* ``FEEDBACK_EXPORT_TIMEOUT`` and ``ADJUDICATOR_STATS_EXPORT_TIMEOUT`` (default
  10 seconds), ``RESULTS_EXPORT_TIMEOUT`` (default 30 seconds) and
  ``SEASON_BREAKS_EXPORT_TIMEOUT`` (default 10 seconds), bounded to
  1–30 seconds in the HTTP transport

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
  (``feedback``/``activity``/``results``), ``force`` and a UUID ``submission_token``. Reusing
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
``feedbackexport.tests.test_results`` builds a small tournament (replies, a ghost
speech, criteria, cross-examinations, an elimination round, a speaker category,
an anonymous speaker and an unconfirmed ballot) and checks the results payload
against the contract, plus skipping, forced resends, corrections, gzip and the
404 block.
