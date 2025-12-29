const XLSX = require("xlsx");
const path = require("path");

/**
 * Phase 1: Load and filter unsent emails from XLSX file
 * @param {string} filePath - Path to the XLSX file
 * @param {string} openPassword - Password to open the file
 * @param {string} editPassword - Password to edit the file
 * @returns {Array} Array of unsent email objects
 */
function loadUnsentEmails(filePath, openPassword, editPassword) {
  const workbook = XLSX.readFile(filePath, {
    password: openPassword, // Password to open the file
    // Note: xlsx library may not support edit password directly, but open password should work
  });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const data = XLSX.utils.sheet_to_json(worksheet);

  // Filter emails where sent_status is not 'email sent'
  const unsentEmails = data.filter((row) => row.sent_status !== "email sent");

  return unsentEmails;
}

module.exports = { loadUnsentEmails };
