# Interpret the evidence

| Observation | Next check |
| --- | --- |
| Raw title is generic; rendered title is specific | Inspect route metadata and current prerender/SSR support. This proves a rendering difference, not that Google failed. |
| Canonical differs from intended URL | Confirm whether this is a deliberate duplicate before changing it. Check Google-selected canonical if available. |
| `noindex` in HTML or response header | Confirm intended visibility and deployment environment. Fix only when the page should be indexed. |
| Unknown path returns 200 and the same content | Test a real missing URL. Correct server/router fallback to return a genuine 404 where appropriate. |
| Sitemap includes redirects or private routes | Derive public canonical routes from the existing route/content source and verify a sample. |
| Google crawled old HTML | Compare crawl time with deployment time. A fresh HTTP test does not change historical Search Console evidence. |

Use the comparator's exit code as a reproducible check of its limited signals: 0 means no listed findings, 1 means inspect findings, 2 means invalid inputs. Missing canonicals/descriptions/H1s are diagnostic observations, not a declaration that a URL is forbidden from indexing. A rendered link difference may be an intended navigation behavior.

Controlled fixture procedure: capture an owned local route's response and browser DOM, run the comparator with its intended canonical URL, repair that route's metadata in source, then repeat both captures. Verify an adjacent route and a missing route. Save expected results without production content. An exact URL comparison intentionally preserves trailing slashes, query strings and letter case: canonical choices are project-specific.

Sources to consult for current behavior:

- [Google JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- [Google canonical URL guidance](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google robots meta tags and headers](https://developers.google.com/search/docs/crawling-indexing/robots-meta-tag)
- [Lovable documentation](https://docs.lovable.dev/)

Use official documentation for the framework version actually installed. Do not infer server rendering from a screenshot or static markup from the presence of a React package.
