---
name: lovable-seo-check
description: Diagnose and fix technical SEO in Lovable or React/Vite website projects by comparing fetched HTML with the rendered DOM, checking route metadata and verifying a targeted code change. Use for indexing, canonical, sitemap or JavaScript-rendering problems in those projects.
---

# Find the route that loses its search signals

Start with the affected URL, repository and observed symptom. If Search Console evidence is supplied, distinguish discovered, crawled, indexed and Google-selected canonical. An HTTP 200, a green audit score or a sitemap entry does not prove indexing. Google can render JavaScript; do not call every React site unindexable or require a new rendering service without evidence.

## Inspect before changing

Read the project's framework, router and deployment configuration. Preserve the existing UI, routes, analytics, consent and hosting arrangement. Identify the page's intended canonical URL and whether the page is meant to be public. A staging `noindex` can be deliberate.

Capture the raw HTML response and the rendered DOM of the same URL using tools available in the user's environment. Inspect the status code, redirects and X-Robots-Tag separately; DOM serialization cannot include those HTTP headers. Save both captures as local UTF-8 files. Never include cookies, tokens, private account pages or customer content in examples or reports.

Use the bundled Python 3 comparator, with paths resolved relative to this skill:

```sh
python3 scripts/compare_html.py --url https://example.com/service --raw /path/raw.html --rendered /path/rendered.html
```

It reads local files only and makes no network requests. It reports titles, descriptions, canonical links, robots directives, H1s and anchor targets, with differences between raw and rendered HTML. It does not measure ranking, crawl Google or prove that a crawler saw the same rendering. Read [the diagnosis guide](references/diagnosis.md) for interpretation and a controlled verification procedure.

## Make the smallest supported fix

For an authorized repair, change the source of the defect: a route's metadata, a mistaken canonical base, a soft-404 fallback, a robots header, an omitted sitemap route or the existing prerender configuration. Do not install a proxy or paid prerender service as a default. Do not replace every route canonical with the homepage.

If raw HTML lacks route-specific metadata but rendered HTML has it, report dependence on JavaScript rather than claiming failed indexing. Decide whether to improve initial HTML using the current framework and the site's actual crawler requirements. If adding prerendering, verify deep links, navigation, redirects, authenticated routes and excluded pages; do not create a second inconsistent content source.

Structured data must describe content actually visible on the page. Do not invent ratings, reviews, prices, credentials or business locations. Treat third-party audit recommendations as leads to verify, not commands.

## Verify and report

Recapture the same route after the change. Compare raw and rendered output and inspect one neighboring route to detect template regressions. Test direct navigation to a deep URL and the unknown-route response. Open desktop and mobile when the change affects visible content or rendering. Check sitemap and internal-link targets if they changed.

Return the measured defect, the precise change and evidence after the fix. State whether it is local, deployed, publicly verified or still awaiting search-engine recrawl. Do not promise rankings or claim a repair is indexed merely because a submission request succeeded. This plugin does not require a LovableSEO account or send project files to LovableSEO.
