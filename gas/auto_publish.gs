/**
 * Google Apps Script: Auto-Publish Pipeline
 *
 * Scans a Google Sheet for rows where column D = "待貼稿", triggers the
 * auto-publish pipeline on the backend, and writes the WordPress draft URL
 * back to column L.
 *
 * Setup:
 *   1. Open the target Google Sheet.
 *   2. Extensions > Apps Script > paste this code.
 *   3. Run setupApiKey() once to store the API key.
 *   4. Create two time-driven triggers (Edit > Current project's triggers):
 *      - autoPublishScan  -> every 1-5 minutes
 *      - pollTaskStatus   -> every 1-5 minutes
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

var CONFIG = {
  // Backend URL (Cloud Run)
  BACKEND_URL: "https://cms-automation-backend-297291472291.us-east1.run.app",

  // Sheet configuration
  SHEET_NAME: "工作清單",     // Name of the sheet tab

  // Column indices (1-based)
  COL_STATUS:   4,  // D - status column ("待貼稿", "處理中", "已上稿", "失敗")
  COL_DOC_URL:  6,  // F - Google Doc URL
  COL_WP_URL:  12,  // L - WordPress draft URL (output)
  COL_TASK_ID: 13,  // M - helper column for Celery task ID (hidden)

  // Status values
  STATUS_PENDING:    "待貼稿",
  STATUS_PROCESSING: "處理中",
  STATUS_DONE:       "已上稿",
  STATUS_FAILED:     "失敗",
};


// ---------------------------------------------------------------------------
// One-time Setup
// ---------------------------------------------------------------------------

/**
 * Run this function once to store the API key securely.
 * You will be prompted to authorize access to script properties.
 */
function setupApiKey() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.prompt(
    "API Key Setup",
    "Enter the CMS API key for GAS automation:",
    ui.ButtonSet.OK_CANCEL
  );

  if (response.getSelectedButton() === ui.Button.OK) {
    var apiKey = response.getResponseText().trim();
    if (apiKey) {
      PropertiesService.getScriptProperties().setProperty("CMS_API_KEY", apiKey);
      ui.alert("API key saved successfully.");
    } else {
      ui.alert("No API key entered. Setup cancelled.");
    }
  }
}


// ---------------------------------------------------------------------------
// Main Functions (set up as time-driven triggers)
// ---------------------------------------------------------------------------

/**
 * Scan the sheet for rows with status "待貼稿" and trigger auto-publish.
 * Set up as a time-driven trigger (every 1-5 minutes).
 */
function autoPublishScan() {
  var sheet = _getSheet();
  if (!sheet) return;

  var apiKey = _getApiKey();
  if (!apiKey) {
    Logger.log("ERROR: API key not configured. Run setupApiKey() first.");
    return;
  }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return; // No data rows

  // Read all relevant columns at once for efficiency
  var statusRange  = sheet.getRange(2, CONFIG.COL_STATUS,  lastRow - 1, 1).getValues();
  var docUrlRange  = sheet.getRange(2, CONFIG.COL_DOC_URL, lastRow - 1, 1).getValues();
  var wpUrlRange   = sheet.getRange(2, CONFIG.COL_WP_URL,  lastRow - 1, 1).getValues();
  var taskIdRange  = sheet.getRange(2, CONFIG.COL_TASK_ID, lastRow - 1, 1).getValues();

  var triggered = 0;

  for (var i = 0; i < statusRange.length; i++) {
    var rowNum = i + 2; // 1-based row in sheet
    var cellStatus = String(statusRange[i][0]).trim();
    var docUrl     = String(docUrlRange[i][0]).trim();
    var wpUrl      = String(wpUrlRange[i][0]).trim();
    var taskId     = String(taskIdRange[i][0]).trim();

    // Skip if not pending, no doc URL, already has task ID, or already has result
    if (cellStatus !== CONFIG.STATUS_PENDING) continue;
    if (!docUrl || !_isGoogleDocUrl(docUrl)) continue;
    if (taskId) continue;
    if (wpUrl) continue;

    // Trigger auto-publish
    try {
      var result = _callAutoPublish(apiKey, docUrl, rowNum);

      if (result && result.task_id) {
        // Write task ID to helper column
        sheet.getRange(rowNum, CONFIG.COL_TASK_ID).setValue(result.task_id);

        // Update status to "處理中"
        sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_PROCESSING);

        // If completed synchronously, write result immediately
        if (result.status === "completed" && result.result && result.result.wordpress_draft_url) {
          sheet.getRange(rowNum, CONFIG.COL_WP_URL).setValue(result.result.wordpress_draft_url);
          sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_DONE);
        }

        triggered++;
        Logger.log("Triggered auto-publish for row " + rowNum + ": " + docUrl);
      }
    } catch (e) {
      Logger.log("ERROR triggering auto-publish for row " + rowNum + ": " + e.message);
      sheet.getRange(rowNum, CONFIG.COL_WP_URL).setValue("Error: " + e.message);
      sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_FAILED);
    }
  }

  if (triggered > 0) {
    Logger.log("autoPublishScan: triggered " + triggered + " new tasks.");
  }
}


/**
 * Poll task status for rows in "處理中" state.
 * Set up as a time-driven trigger (every 1-5 minutes).
 */
function pollTaskStatus() {
  var sheet = _getSheet();
  if (!sheet) return;

  var apiKey = _getApiKey();
  if (!apiKey) return;

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  var statusRange = sheet.getRange(2, CONFIG.COL_STATUS,  lastRow - 1, 1).getValues();
  var taskIdRange = sheet.getRange(2, CONFIG.COL_TASK_ID, lastRow - 1, 1).getValues();

  var polled = 0;

  for (var i = 0; i < statusRange.length; i++) {
    var rowNum = i + 2;
    var cellStatus = String(statusRange[i][0]).trim();
    var taskId     = String(taskIdRange[i][0]).trim();

    // Only poll rows that are processing and have a task ID
    if (cellStatus !== CONFIG.STATUS_PROCESSING) continue;
    if (!taskId) continue;

    try {
      var taskStatus = _getTaskStatus(apiKey, taskId);

      if (taskStatus.status === "completed") {
        var wpUrl = (taskStatus.result && taskStatus.result.wordpress_draft_url) || "";
        sheet.getRange(rowNum, CONFIG.COL_WP_URL).setValue(wpUrl || "Published (no URL)");
        sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_DONE);
        polled++;
        Logger.log("Row " + rowNum + " completed: " + wpUrl);
      } else if (taskStatus.status === "failed") {
        var errorMsg = taskStatus.error || "Unknown error";
        sheet.getRange(rowNum, CONFIG.COL_WP_URL).setValue("Error: " + errorMsg);
        sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_FAILED);
        polled++;
        Logger.log("Row " + rowNum + " failed: " + errorMsg);
      }
      // "pending" and "processing" -> keep waiting
    } catch (e) {
      Logger.log("ERROR polling status for row " + rowNum + ": " + e.message);
    }
  }

  if (polled > 0) {
    Logger.log("pollTaskStatus: updated " + polled + " rows.");
  }
}


// ---------------------------------------------------------------------------
// Test / Debug Helpers
// ---------------------------------------------------------------------------

/**
 * Test connectivity with the backend.
 * Run manually from the Apps Script editor.
 */
function testConnection() {
  var apiKey = _getApiKey();
  if (!apiKey) {
    Logger.log("ERROR: API key not configured. Run setupApiKey() first.");
    return;
  }

  var url = CONFIG.BACKEND_URL + "/health";
  try {
    var response = UrlFetchApp.fetch(url, {
      method: "get",
      muteHttpExceptions: true,
      headers: { "X-API-Key": apiKey },
    });

    Logger.log("Health check status: " + response.getResponseCode());
    Logger.log("Response: " + response.getContentText());
  } catch (e) {
    Logger.log("Connection test failed: " + e.message);
  }
}


/**
 * Test auto-publish with a specific Google Doc URL.
 * Run manually from the Apps Script editor.
 */
function testAutoPublish() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.prompt(
    "Test Auto-Publish",
    "Enter a Google Docs URL to test:",
    ui.ButtonSet.OK_CANCEL
  );

  if (response.getSelectedButton() !== ui.Button.OK) return;

  var docUrl = response.getResponseText().trim();
  if (!docUrl) return;

  var apiKey = _getApiKey();
  var result = _callAutoPublish(apiKey, docUrl, null);
  Logger.log("Test result: " + JSON.stringify(result, null, 2));
  ui.alert("Result: " + JSON.stringify(result, null, 2));
}


// ---------------------------------------------------------------------------
// Internal Helpers
// ---------------------------------------------------------------------------

function _getSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(CONFIG.SHEET_NAME);
  if (!sheet) {
    Logger.log("ERROR: Sheet '" + CONFIG.SHEET_NAME + "' not found.");
    return null;
  }
  return sheet;
}

function _getApiKey() {
  return PropertiesService.getScriptProperties().getProperty("CMS_API_KEY");
}

function _isGoogleDocUrl(url) {
  return url.indexOf("docs.google.com/document") !== -1;
}

/**
 * Call POST /v1/pipeline/auto-publish
 */
function _callAutoPublish(apiKey, googleDocUrl, sheetRow) {
  var url = CONFIG.BACKEND_URL + "/v1/pipeline/auto-publish";
  var payload = {
    google_doc_url: googleDocUrl,
  };
  if (sheetRow !== null && sheetRow !== undefined) {
    payload.sheet_row = sheetRow;
  }

  var options = {
    method: "post",
    contentType: "application/json",
    headers: { "X-API-Key": apiKey },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true,
  };

  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();
  var body = response.getContentText();

  if (code >= 200 && code < 300) {
    return JSON.parse(body);
  } else {
    throw new Error("HTTP " + code + ": " + body);
  }
}

/**
 * Call GET /v1/pipeline/auto-publish/{taskId}/status
 */
function _getTaskStatus(apiKey, taskId) {
  var url = CONFIG.BACKEND_URL + "/v1/pipeline/auto-publish/" + encodeURIComponent(taskId) + "/status";

  var options = {
    method: "get",
    headers: { "X-API-Key": apiKey },
    muteHttpExceptions: true,
  };

  var response = UrlFetchApp.fetch(url, options);
  var code = response.getResponseCode();
  var body = response.getContentText();

  if (code >= 200 && code < 300) {
    return JSON.parse(body);
  } else {
    throw new Error("HTTP " + code + ": " + body);
  }
}
