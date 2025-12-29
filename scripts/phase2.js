/**
 * Phase 2: Prepare batches of 50 emails each
 * @param {Array} emails - Array of email objects
 * @param {number} batchSize - Size of each batch (default 50)
 * @returns {Array} Array of batches, each containing up to batchSize emails
 */
function prepareBatches(emails, batchSize = 50) {
  const batches = [];
  for (let i = 0; i < emails.length; i += batchSize) {
    batches.push(emails.slice(i, i + batchSize));
  }
  return batches;
}

module.exports = { prepareBatches };
