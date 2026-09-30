# LovableSEO

Diagnose technical SEO in Lovable and React projects by comparing saved raw HTML with the rendered DOM. Inspect titles, canonicals, robots directives and links, then verify a targeted repair. Includes a local Python comparator. No account connection, telemetry or ranking promises.

Install the plugin archive in a host that supports Agent Plugins, or load `skills/lovable-seo-check/SKILL.md` in a compatible skill host. It works without a LovableSEO account. Python 3 is required for the optional checker. See the skill for commands and interpretation.

Source and examples are MIT licensed. This is an independent plugin; it is not an official n8n or Lovable integration. No production service is activated by installation.

Run the local regression checks:

```sh
python3 -m unittest discover -s tests -v
```

[Privacy](PRIVACY.md) · [Support](https://github.com/smrht/lovableseo-agent-plugin/issues) · [Project](https://lovableseo.nl)
