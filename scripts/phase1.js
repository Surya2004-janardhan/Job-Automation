const XLSX = require("xlsx");
const path = require("path");

/**
 * Phase 1: Load and filter unsent emails from XLSX file
 * @param {string} filePath - Path to the XLSX file
 * @returns {Array} Array of unsent email objects
 */
function loadUnsentEmails(filePath) {
  const workbook = XLSX.readFile(filePath);
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const data = XLSX.utils.sheet_to_json(worksheet);

  // Filter emails where sent_status is not 'email sent'
  const unsentEmails = data.filter((row) => row.sent_status !== "email sent");

  return unsentEmails;
}

module.exports = { loadUnsentEmails };
