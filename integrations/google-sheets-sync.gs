const CSV_URL = 'https://raw.githubusercontent.com/vai2110/mba-admission-portal/main/college-production-tracker.csv';
const SHEET_NAME = 'College Queue';

function syncCollegeQueue() {
  const response = UrlFetchApp.fetch(CSV_URL, {muteHttpExceptions: true});
  if (response.getResponseCode() !== 200) throw new Error('Tracker fetch failed: ' + response.getResponseCode());
  const csv = Utilities.parseCsv(response.getContentText());
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEET_NAME) || ss.insertSheet(SHEET_NAME);
  sheet.clearContents();
  if (!csv.length) return;
  sheet.getRange(1, 1, csv.length, csv[0].length).setValues(csv);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, csv[0].length).setFontWeight('bold');
  sheet.autoResizeColumns(1, csv[0].length);
}

function installFiveMinuteSync() {
  ScriptApp.getProjectTriggers().forEach(t => {
    if (t.getHandlerFunction() === 'syncCollegeQueue') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('syncCollegeQueue').timeBased().everyMinutes(5).create();
  syncCollegeQueue();
}
