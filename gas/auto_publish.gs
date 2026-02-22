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
  SHEET_NAME: "發佈排程",     // Name of the sheet tab
  LOG_SHEET_NAME: "自動上稿日誌", // Log sheet tab (auto-created if missing)

  // Column indices (1-based)
  COL_STATUS:   4,  // D - status column ("待貼稿", "處理中", "已上稿", "失敗")
  COL_DOC_URL:  6,  // F - Google Doc URL
  COL_WP_URL:  12,  // L - WordPress draft URL (output)
  COL_TASK_ID: 15,  // O - helper column for Celery task ID (hidden)

  // Status values
  STATUS_PENDING:    "待貼稿",
  STATUS_PROCESSING: "貼稿中",
  STATUS_DONE:       "自動貼稿完成",
  STATUS_FAILED:     "自動上稿失敗",
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
  var docUrlRich   = sheet.getRange(2, CONFIG.COL_DOC_URL, lastRow - 1, 1).getRichTextValues();
  var docUrlFormulas = sheet.getRange(2, CONFIG.COL_DOC_URL, lastRow - 1, 1).getFormulas();
  var docUrlValues = sheet.getRange(2, CONFIG.COL_DOC_URL, lastRow - 1, 1).getValues();
  var wpUrlRange   = sheet.getRange(2, CONFIG.COL_WP_URL,  lastRow - 1, 1).getValues();
  var taskIdRange  = sheet.getRange(2, CONFIG.COL_TASK_ID, lastRow - 1, 1).getValues();

  var triggered = 0;

  for (var i = 0; i < statusRange.length; i++) {
    var rowNum = i + 2; // 1-based row in sheet
    var cellStatus = String(statusRange[i][0]).trim();
    var docUrl     = _extractHyperlinkUrl(docUrlRich[i][0], docUrlFormulas[i][0], docUrlValues[i][0]);
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

          // Trigger storage cleanup for synchronous completion
          var syncItemId = result.result.worklist_item_id;
          if (syncItemId) {
            try {
              _callCleanup(apiKey, syncItemId);
              Logger.log("Row " + rowNum + " sync cleanup triggered for worklist_item_id=" + syncItemId);
            } catch (cleanupErr) {
              Logger.log("Row " + rowNum + " sync cleanup failed (non-critical): " + cleanupErr.message);
            }
          }
        }

        // Log: sync completion or task queued
        if (result.status === "completed") {
          _logToSheet(rowNum, docUrl, "完成", "同步完成，WordPress URL: " + (result.result.wordpress_draft_url || "N/A"), result.task_id);
        } else {
          _logToSheet(rowNum, docUrl, "已提交", "Task queued", result.task_id);
        }

        triggered++;
        Logger.log("Triggered auto-publish for row " + rowNum + ": " + docUrl);
      }
    } catch (e) {
      Logger.log("ERROR triggering auto-publish for row " + rowNum + ": " + e.message);
      sheet.getRange(rowNum, CONFIG.COL_WP_URL).setValue("Error: " + e.message);
      sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_FAILED);
      _logToSheet(rowNum, docUrl, "失敗", e.message, "");
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
        _logToSheet(rowNum, "", "完成", "WordPress URL: " + (wpUrl || "N/A"), taskId);

        // Trigger storage cleanup for the published item
        var worklistItemId = taskStatus.result && taskStatus.result.worklist_item_id;
        if (worklistItemId) {
          try {
            _callCleanup(apiKey, worklistItemId);
            Logger.log("Row " + rowNum + " cleanup triggered for worklist_item_id=" + worklistItemId);
          } catch (cleanupErr) {
            Logger.log("Row " + rowNum + " cleanup failed (non-critical): " + cleanupErr.message);
          }
        }
      } else if (taskStatus.status === "failed") {
        var errorMsg = taskStatus.error || "Unknown error";
        sheet.getRange(rowNum, CONFIG.COL_WP_URL).setValue("Error: " + errorMsg);
        sheet.getRange(rowNum, CONFIG.COL_STATUS).setValue(CONFIG.STATUS_FAILED);
        polled++;
        Logger.log("Row " + rowNum + " failed: " + errorMsg);
        _logToSheet(rowNum, "", "失敗", errorMsg, taskId);
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
  if (!url) return false;
  // Standard: docs.google.com/document/d/...
  if (url.indexOf("docs.google.com/document") !== -1) return true;
  // Drive open: drive.google.com/open?id=...
  if (url.indexOf("drive.google.com") !== -1 && url.indexOf("open?id=") !== -1) return true;
  return false;
}

/**
 * Extract the actual Google Doc URL from a cell that may contain a hyperlink.
 * Handles: rich text links, HYPERLINK() formulas, plain text URLs, and pure Doc IDs.
 */
function _extractHyperlinkUrl(richTextValue, formula, displayValue) {
  // 1. Try rich text link runs (handles partial links & HYPERLINK formula residue)
  if (richTextValue) {
    var runs = richTextValue.getRuns();
    for (var j = 0; j < runs.length; j++) {
      // Check hyperlink URL on this run
      var linkUrl = runs[j].getLinkUrl();
      if (linkUrl) {
        var id = _parseDocId(linkUrl);
        if (id) return _buildDocUrl(id, linkUrl);
      }
      // Check run text for embedded URLs
      var runText = runs[j].getText();
      var id = _parseDocId(runText);
      if (id) return _buildDocUrl(id, runText);
    }
    // Try top-level link
    var topUrl = richTextValue.getLinkUrl();
    if (topUrl) {
      var id = _parseDocId(topUrl);
      if (id) return _buildDocUrl(id, topUrl);
    }
  }

  // 2. Try HYPERLINK() formula
  if (formula) {
    var match = String(formula).match(/HYPERLINK\s*\(\s*"([^"]+)"/i);
    if (match) {
      var id = _parseDocId(match[1]);
      if (id) return _buildDocUrl(id, match[1]);
    }
  }

  // 3. Fall back to display value (plain text URL or Doc ID)
  var text = String(displayValue).trim();
  var id = _parseDocId(text);
  if (id) return _buildDocUrl(id, text);

  return text;
}

/**
 * Parse a Google Doc ID from various URL formats.
 * Supports:
 *   - /document/d/DOC_ID/
 *   - open?id=DOC_ID
 *   - Pure Doc ID (25+ alphanumeric chars)
 */
function _parseDocId(text) {
  if (!text) return null;
  text = String(text).trim();

  // Format 1: /document/d/DOC_ID/
  var match1 = text.match(/\/document\/d\/([a-zA-Z0-9_-]+)/);
  if (match1) return match1[1];

  // Format 2: open?id=DOC_ID
  var match2 = text.match(/open\?id=([a-zA-Z0-9_-]+)/);
  if (match2) return match2[1];

  // Format 3: Pure Doc ID (25+ alphanumeric/dash/underscore chars)
  if (/^[a-zA-Z0-9_-]{25,}$/.test(text)) return text;

  return null;
}

/**
 * Build a canonical Google Doc URL from a Doc ID.
 * If the original text is already a full URL, returns it; otherwise constructs one.
 */
function _buildDocUrl(docId, originalText) {
  if (originalText && originalText.indexOf("docs.google.com/document") !== -1) {
    return originalText;
  }
  return "https://docs.google.com/document/d/" + docId + "/edit";
}

/**
 * Get or create the log sheet. Auto-creates with headers if missing.
 */
function _getOrCreateLogSheet() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var logSheet = ss.getSheetByName(CONFIG.LOG_SHEET_NAME);
  if (!logSheet) {
    logSheet = ss.insertSheet(CONFIG.LOG_SHEET_NAME);
    logSheet.appendRow(["時間戳", "行號", "Google Doc URL", "狀態", "詳細信息", "Task ID"]);
    logSheet.getRange(1, 1, 1, 6).setFontWeight("bold");
    logSheet.setColumnWidth(1, 160);
    logSheet.setColumnWidth(3, 300);
    logSheet.setColumnWidth(5, 400);
  }
  return logSheet;
}

/**
 * Write a log entry to the "自動上稿日誌" sheet.
 */
function _logToSheet(rowNum, docUrl, status, detail, taskId) {
  try {
    var logSheet = _getOrCreateLogSheet();
    var timestamp = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd HH:mm:ss");
    logSheet.appendRow([timestamp, rowNum || "", docUrl || "", status, detail || "", taskId || ""]);
  } catch (e) {
    Logger.log("WARNING: Failed to write log: " + e.message);
  }
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

/**
 * Call POST /v1/pipeline/cleanup to free Supabase storage after publishing.
 * Non-critical: failures are logged but do not affect the publish status.
 */
function _callCleanup(apiKey, worklistItemId) {
  var url = CONFIG.BACKEND_URL + "/v1/pipeline/cleanup";
  var payload = {
    worklist_item_id: worklistItemId,
  };

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
    var result = JSON.parse(body);
    Logger.log("Cleanup result: freed ~" + result.freed_bytes_estimate + " bytes");
    return result;
  } else {
    throw new Error("Cleanup HTTP " + code + ": " + body);
  }
}
