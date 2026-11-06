# Automation freeze inventory — 6 November 2026

## Control

`config/freeze.json` is the single switch. While either `freeze_content_automation` or `freeze_page_mutations` is true, the shared guard exits with status 78. The Vercel build treats that status as a deliberate no-op: it deploys checked-in static files without running page generators, link repairers, metadata/schema rewrites, or injection steps. Guarded GitHub Actions stop immediately after checkout and before their mutation steps.

## Confirmed workflow inventory

The following 47 workflow files contain a `git push` command in the repository's workflow source search. They are the confirmed auto-commit/push workflow set and have the freeze guard inserted after checkout:

- `.github/workflows/generate-sitemap.yml`
- `.github/workflows/apply-homepage-v2.yml`
- `.github/workflows/college-production.yml`
- `.github/workflows/enhance-kjsim-pages.yml`
- `.github/workflows/lpu-content-cleanup.yml`
- `.github/workflows/technical-seo-audit.yml`
- `.github/workflows/remove-location-note.yml`
- `.github/workflows/glim-content-upgrade.yml`
- `.github/workflows/upes-page-fix.yml`
- `.github/workflows/cusat-keyword-kickoff.yml`
- `.github/workflows/iim-amritsar-hero-fix.yml`
- `.github/workflows/strip-hash-navigation.yml`
- `.github/workflows/repair-internal-links.yml`
- `.github/workflows/imi-delhi-mobile-tables.yml`
- `.github/workflows/fix-chitkara-navigation.yml`
- `.github/workflows/iim-amritsar-on-page-fix.yml`
- `.github/workflows/lpu-no-cluster-nav-guard.yml`
- `.github/workflows/publish-location-template.yml`
- `.github/workflows/remove-glim-college-strip.yml`
- `.github/workflows/bimtech-navigation-cleanup.yml`
- `.github/workflows/dashboard-refresh-after-audit.yml`
- `.github/workflows/apply-clean-section-urls.yml`
- `.github/workflows/add-editorial-meta.yml`
- `.github/workflows/clean-visible-escaped-newlines.yml`
- `.github/workflows/nmims-benchmark-rerun.yml`
- `.github/workflows/cusat-keyword-direct.yml`
- `.github/workflows/content-audit.yml`
- `.github/workflows/remove-inline-citation-artifacts.yml`
- `.github/workflows/mnnit-final-fix.yml`
- `.github/workflows/college-production-recovery.yml`
- `.github/workflows/tapmi-mobile-tables.yml`
- `.github/workflows/finalize-iima.yml`
- `.github/workflows/tapmi-course-dates.yml`
- `.github/workflows/tapmi-final-cleanup.yml`
- `.github/workflows/migrate-clean-urls.yml`
- `.github/workflows/welingkar-reference-upgrade.yml`
- `.github/workflows/college-existing-page-audit.yml`
- `.github/workflows/iit-roorkee-typography-repair.yml`
- `.github/workflows/iit-roorkee-final-design-lock.yml`
- `.github/workflows/fix-agent-and-resume.yml`
- `.github/workflows/cusat-keyword-refresh.yml`
- `.github/workflows/bimtech-final-page-fix.yml`
- `.github/workflows/update-jain-pages.yml`
- `.github/workflows/lpu-cluster-navigation.yml`
- `.github/workflows/mnnit-placement-archive-rebuild.yml`
- `.github/workflows/xim-content-depth-upgrade.yml`
- `.github/workflows/iim-amritsar-placement-overview-fix.yml`

## Workflows granted `contents: write`

The repository has 52 workflow files declaring `permissions: contents: write`. All active checkout-based jobs in this set have the same freeze guard. Three files are currently non-mutating no-ops/disabled jobs (`new-college-agent.yml`, `irma-official-data-fix.yml`, `mnnit-executive-fee-fix.yml`) and remain no-op/disabled; no checkout-based mutation step exists in those files.

- `.github/workflows/ux-mobile-audit.yml`
- `.github/workflows/generate-sitemap.yml`
- `.github/workflows/apply-homepage-v2.yml`
- `.github/workflows/new-college-agent.yml`
- `.github/workflows/college-production.yml`
- `.github/workflows/enhance-kjsim-pages.yml`
- `.github/workflows/lpu-content-cleanup.yml`
- `.github/workflows/technical-seo-audit.yml`
- `.github/workflows/glim-upgrade-trigger.yml`
- `.github/workflows/remove-location-note.yml`
- `.github/workflows/glim-content-upgrade.yml`
- `.github/workflows/upes-page-fix.yml`
- `.github/workflows/cusat-keyword-kickoff.yml`
- `.github/workflows/iim-amritsar-hero-fix.yml`
- `.github/workflows/strip-hash-navigation.yml`
- `.github/workflows/repair-internal-links.yml`
- `.github/workflows/irma-official-data-fix.yml`
- `.github/workflows/fix-chitkara-navigation.yml`
- `.github/workflows/mnnit-executive-fee-fix.yml`
- `.github/workflows/iim-amritsar-on-page-fix.yml`
- `.github/workflows/lpu-no-cluster-nav-guard.yml`
- `.github/workflows/publish-location-template.yml`
- `.github/workflows/remove-glim-college-strip.yml`
- `.github/workflows/bimtech-navigation-cleanup.yml`
- `.github/workflows/dashboard-refresh-after-audit.yml`
- `.github/workflows/apply-clean-section-urls.yml`
- `.github/workflows/add-editorial-meta.yml`
- `.github/workflows/clean-visible-escaped-newlines.yml`
- `.github/workflows/independent-college-content-agent.yml`
- `.github/workflows/nmims-benchmark-rerun.yml`
- `.github/workflows/cusat-keyword-direct.yml`
- `.github/workflows/remove-inline-citation-artifacts.yml`
- `.github/workflows/mnnit-final-fix.yml`
- `.github/workflows/college-production-recovery.yml`
- `.github/workflows/v8-rank30.yml`
- `.github/workflows/finalize-iima.yml`
- `.github/workflows/tapmi-course-dates.yml`
- `.github/workflows/tapmi-final-cleanup.yml`
- `.github/workflows/migrate-clean-urls.yml`
- `.github/workflows/content-audit.yml`
- `.github/workflows/welingkar-reference-upgrade.yml`
- `.github/workflows/college-existing-page-audit.yml`
- `.github/workflows/iit-roorkee-typography-repair.yml`
- `.github/workflows/iit-roorkee-final-design-lock.yml`
- `.github/workflows/fix-agent-and-resume.yml`
- `.github/workflows/cusat-keyword-refresh.yml`
- `.github/workflows/bimtech-final-page-fix.yml`
- `.github/workflows/lpu-cluster-navigation.yml`
- `.github/workflows/mnnit-placement-archive-rebuild.yml`
- `.github/workflows/xim-content-depth-upgrade.yml`
- `.github/workflows/iim-amritsar-placement-overview-fix.yml`
- `.github/workflows/controlled-iit-kanpur-test.yml`

Three of the 47 push-capable workflows do not appear in the `contents: write` permission search: `imi-delhi-mobile-tables.yml`, `tapmi-mobile-tables.yml`, and `update-jain-pages.yml`. They are guarded as well. The non-publishing `validate-news-build.yml` workflow is also guarded because it runs the hub and news generators in its CI workspace; the GitHub Pages deploy workflow is guarded too.

## Page-writing scripts and build stages

### Content generation / rewriting entry points
- `scripts/independent_college_content_agent.py`
- `scripts/independent_college_content_agent_v2.py` through `scripts/independent_college_content_agent_v8.py`
- `scripts/run_independent_college_content_agent.py`
- `scripts/run_independent_college_content_agent_post.py`
- `scripts/auto_content_fixer.py`
- `scripts/college_queue_agent.py`, `scripts/college_queue_agent_local.py`, `scripts/college_audit_queue_agent.py`

### Build-invoked page mutators (all skipped by the Vercel freeze gate)
- `scripts/repair_malformed_seo_head.py`
- `scripts/normalize-clean-urls.js`
- `scripts/generate_college_guides_hub.py`
- `scripts/seo_metadata_cleanup.py`
- `scripts/seo_structured_data_cleanup.py`
- `scripts/repair_internal_links_v2.py`, `scripts/repair_internal_links.py`, `scripts/repair_orphan_links.py`
- `scripts/repair_cutoff_page_links.py`, `scripts/repair_location_images.py`
- `scripts/inject-guidance-flow.js`, `scripts/build-news.js`, `scripts/inject-related-news.js`, `scripts/inject-ai-advisor.js`
- `scripts/clean_iim_ahmedabad_post_faq.py`
- `scripts/repair_invalid_jsonld.py`

### Direct script guard coverage in this PR
The shared guard is called directly by content-agent versions v1–v8, both independent-agent runners, the POST launcher, `auto_content_fixer.py`, and the college queue/audit-queue agent entry points. All build-invoked scripts are protected by the early Vercel build gate; all listed workflow-triggered mutations are protected by workflow-level guards.

## Verification limitation

The GitHub source inventory was queried against the current default-branch tree and code search. The repository checkout/build runtime is not available inside this GitHub-only editing session, so the full `scripts/vercel-build.sh` has not yet been executed here. A PR preview/build must confirm that the shell and workflow YAML parse and that the frozen build produces zero HTML-file diffs before merge.
