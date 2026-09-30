# Check a migration against saved evidence

Use two saved URL-set sitemaps, one before and one after the change. If either is a sitemap index, collect and combine the child URL sets first. Keep intentionally removed pages, such as a deliberate 410, separate from the migration set and document that exclusion. Never redirect a removed page to an unrelated page just to make a checker pass.

Capture each old URL, each redirect hop and each new URL with redirects disabled. Record status and Location before following it. Use an authorized environment to collect the pages. Extract the final page's canonical, title, description, robots meta and X-Robots-Tag header. An empty string means the field was checked and absent; a missing robots field means it was not checked. Inspect duplicate canonical/meta tags separately with the HTML comparator. Retain the capture time alongside the report, so old evidence is not presented as a fresh production check.

The response file is a JSON object keyed by absolute URL:

```json
{
  "https://example.com/old": {"status": 301, "location": "/new"},
  "https://example.com/new": {
    "status": 200,
    "canonical": "https://example.com/new",
    "title": "Bike repairs",
    "description": "Book a repair for your bike.",
    "robots": "",
    "x_robots_tag": ""
  }
}
```

The mapping file explicitly assigns the intended replacement for each moved URL:

```json
{"https://example.com/old": "https://example.com/new"}
```

Run from the skill directory:

```sh
python3 scripts/check_migration.py --old old-sitemap.xml --new new-sitemap.xml --responses responses.json --mapping mapping.json --baseline previous-responses.json
```

`--baseline` is optional. It uses the same capture format and highlights changed titles/descriptions for editorial review. A changed title can be intentional; document that decision instead of restoring old text blindly. Without a baseline, the checker detects missing metadata but cannot prove previous wording was preserved.

Exit 0 means the supplied evidence has no findings, exit 1 means findings require investigation and exit 2 means invalid or unreadable input. Missing captures fail the check. The helper performs no requests, installs nothing and writes no files. It cannot verify content equivalence, completeness of the original sitemap, soft 404s, Google indexing or ranking. Compare important pages visually and use Search Console/backlink evidence to identify valuable URLs absent from the original sitemap.

After an authorized repair, recapture the affected routes, run the same comparison and check one untouched route. Report which findings were repaired and which reflect an intentional change. Do not equate a local fixture passing with a live migration passing.
