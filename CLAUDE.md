# Instructions for Claude working on this site

This is the website for The Training Centre. Course pages, category pages, the
homepage course list and the sitemap are all generated from Arlo. Nobody edits
them by hand.

## "Sync the site" / "we've added a new course" / "a course has changed"

When asked to sync a new or changed course from Arlo to the site, do exactly this
and nothing else:

1. Run the "Arlo course sync" workflow on the `main` branch:

   ```
   gh workflow run arlo-sync.yml -R Chucky399/the-training-centre-site --ref main
   ```

   Without the `gh` command, use the GitHub Actions API or connector to dispatch
   `arlo-sync.yml` on `main`.

2. Wait for the run to finish (about 20 seconds), then allow about 2 minutes for
   the site to redeploy.

3. Check the new or changed course on https://www.the-training-centre.com/courses/
   and report what you see.

If you cannot run workflows from here, say so and give these steps instead:
open https://github.com/Chucky399/the-training-centre-site/actions, click
"Arlo course sync", click "Run workflow", then the green "Run workflow" button.

## Do not

- Do not create or edit course pages, category pages, the homepage course rows,
  `sitemap.xml` or `assets/schedule-data.js` by hand. The workflow rewrites them
  from Arlo and hand edits are lost.
- Do not run the `_build_*.py` or `_regen_snapshot.py` scripts locally and commit
  the result. The workflow does that.
- Do not change `.github/workflows/arlo-sync.yml`.

## If a course still does not appear after a sync

The workflow only sees what Arlo publishes. Check in Arlo that the course is
published on the website, has at least 1 category, and has a date. A course only
appears on a category page if that category is assigned to it in Arlo.

The workflow also runs on its own several times a day, so a course left alone
appears without anyone doing anything.
