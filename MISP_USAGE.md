## How to Use MISP Data in the Visual Lab

Once MISP is connected and the live feed is active, the knowledge graph updates automatically. Here is what actually happens and how to read it.

---

### What MISP Sends

Every hour the scheduler pulls recent events from your MISP instance. Each MISP event contains attributes — structured observations about a threat. For example:

- An IP address observed communicating with a known C2 server
- A file hash matching a malware sample
- A domain used in a phishing campaign
- A threat actor name with linked TTPs

Each attribute gets converted to a STIX 2.1 object and enters the graph as a new node — connected to existing threat actors or campaigns where attribution is confident enough.

---

### Reading the Graph After MISP Ingestion

**New nodes appear with a provenance badge.** Any node ingested from MISP carries `x_oi_source` and `x_oi_trust_level` fields. Click a node in the Visual Lab and the detail panel shows:

- **Source** — which MISP instance reported it (`MISP-Local`, `MISP-CIRCL`, etc.)
- **Trust level** — a score from 0.0 to 1.0 derived from the MISP threat level and source trust prior
- **Ingested at** — when OI Lab pulled it
- **Staleness** — flagged if the intelligence is older than 90 days

**Nodes with low trust look different.** The graph dims nodes with trust levels below 0.5 — useful for immediately spotting the difference between high-confidence curated data and unverified live feeds.

---

### Querying Ingested Data via the API

The API exposes the live object store directly:

**See everything ingested from MISP:**
```
http://localhost:8000/ingest/objects?source=MISP-Local
```

**Filter by trust level (only high-confidence objects):**
```
http://localhost:8000/ingest/objects?min_trust=0.8
```

**See ingestion run history (what was pulled, when, how many objects):**
```
http://localhost:8000/ingest/run-log
```

**Live store summary (total objects, breakdown by type and source):**
```
http://localhost:8000/ingest/store/summary
```

**Export everything as a STIX bundle (for Splunk/Sentinel):**
```
http://localhost:8000/ingest/bundle
```

---

### What the MISP Status Panel Means

In the Visual Lab right sidebar you see the MISP Integration panel:

| Status | Meaning |
|---|---|
| **MISP Client — Configured** | The client module is loaded and ready |
| **Live Feed — Active** | `MISP_URL` and `MISP_KEY` are set, scheduler is running |
| **Live Feed — Requires MISP Instance** | Env vars not set — running on static data only |
| **TAXII Ingestor — Module Ready** | Can pull from external TAXII feeds when configured |
| **Provenance — Chain-of-Custody Active** | Every ingested object is being stamped and validated |

---

### Adding More MISP Feeds

You are not limited to one MISP instance. The scheduler supports multiple feeds. To add a second one, call the API directly:

```bash
curl -X POST http://localhost:8000/ingest/misp \
  -H "Content-Type: application/json" \
  -d '{
    "label": "MISP-CIRCL",
    "base_url": "https://misp.circl.lu",
    "api_key": "your-circl-key",
    "pull_days": 7,
    "verify_ssl": true
  }'
```

This registers the feed and immediately runs an ingestion cycle. The run log at `/ingest/run-log` shows the result.

---

### Adding External TAXII Feeds

Beyond MISP, any TAXII 2.1 compatible feed works the same way:

```bash
curl -X POST http://localhost:8000/ingest/taxii \
  -H "Content-Type: application/json" \
  -d '{
    "label": "TAXII-OpenCTI",
    "server_url": "https://your-opencti.example.org/taxii/",
    "api_key": "your-key",
    "pull_days": 7
  }'
```

---

### Trust Prior Reference

Not all sources are treated equally. The provenance engine applies a named trust prior to each source before computing the final trust level:

| Source | Trust Prior |
|---|---|
| MISP-CISA | 1.00 |
| MISP-CERT-EU | 0.95 |
| MISP-CIRCL | 0.95 |
| MISP-NATO | 0.95 |
| MISP-Community | 0.75 |
| TAXII-OpenCTI | 0.85 |
| TAXII-Commercial | 0.80 |
| TAXII-Unknown | 0.60 |

Objects older than 90 days receive an additional −0.20 staleness penalty. Objects that fall below 0.10 after all adjustments are rejected and never enter the graph.
