const XLSX = require("xlsx");

/**
 * Phase 4: Update sent status in XLSX file
 * @param {string} filePath - Path to the XLSX file
 * @param {Array} sentEmails - Array of emails that were sent
 * @param {string} editPassword - Password to edit the file
 */
function updateSentStatus(filePath, sentEmails, editPassword) {
  const workbook = XLSX.readFile(filePath, { password: editPassword });
  const sheetName = workbook.SheetNames[0];
  const worksheet = workbook.Sheets[sheetName];
  const data = XLSX.utils.sheet_to_json(worksheet);

  // Update sent_status for sent emails
  data.forEach((row) => {
    if (sentEmails.includes(row.email)) {
      row.sent_status = "email sent";
    }
  });

  // Write back to file with password protection
  const newWorksheet = XLSX.utils.json_to_sheet(data);
  workbook.Sheets[sheetName] = newWorksheet;
  XLSX.writeFile(workbook, filePath, { password: editPassword });

  console.log(`Updated sent status for ${sentEmails.length} emails`);
}

module.exports = { updateSentStatus };
