# Automatic Google Sheets sync for the CollegeDecoded Newsroom

When `data/news.json` changes on `main`, GitHub Actions sends all currently published articles to the Google Sheet. The sheet mirrors published stories; `data/news.json` remains the publishing source of truth in this first version.

## One-time setup

1. Upload the newsroom workbook template to Google Drive and open it as a Google Sheet. Keep the tab named **News Queue**.
2. In the spreadsheet, open **Extensions → Apps Script**.
3. Copy the contents of `integrations/google-sheets/NewsroomSync.gs` from this repository into the Apps Script editor and save.
4. In Apps Script, open **Project Settings → Script Properties**. Add `NEWS_SHEET_API_SECRET` with a long random value (at least 32 random characters). Do not put this secret in the sheet or repository.
5. Choose **Deploy → New deployment → Web app**. Set **Execute as** to yourself and **Who has access** to anyone, then deploy and approve the requested Google permissions. Copy the web app URL ending in `/exec`. The endpoint is publicly reachable, but requests without the secret are rejected.
6. In GitHub, open **Settings → Secrets and variables → Actions → New repository secret**. Add:
   - `NEWS_SHEET_WEBAPP_URL`: the Apps Script web app URL
   - `NEWS_SHEET_API_SECRET`: exactly the same secret as the Apps Script Script Property
7. In GitHub **Actions**, run **Sync Published News to Google Sheets** once using **Run workflow**. A successful run reports how many rows were inserted or updated.

## What syncs

- Only entries with `status: "published"` are sent.
- Rows are matched by `slug`; edits and republishing update the existing row instead of duplicating it.
- Content columns sync while spreadsheet-only fields such as `editorialNote`, `factCheckStatus`, `editor`, and `lastReviewed` are preserved.
- Drafts are never sent. If a story is later unpublished, its existing row remains as a publication record; the workflow does not delete rows.
- The workflow runs when `data/news.json` changes on `main`. The publishing change must be merged to `main`.

## Security and troubleshooting

- Keep both GitHub secrets private; never commit them.
- If the Apps Script code changes, deploy a new web-app version. Keep the same deployment URL where possible.
- If the workflow reports Unauthorized, compare the GitHub secret with the Apps Script Script Property.
- If no sync occurs, check GitHub Actions and confirm the story has `status: "published"` in `data/news.json`.
