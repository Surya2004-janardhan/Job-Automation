const { loadUnsentEmails } = require("../scripts/phase1");
const { prepareBatches } = require("../scripts/phase2");
const { sendEmails } = require("../scripts/phase3");
const { updateSentStatus } = require("../scripts/phase4");
const path = require("path");

async function main() {
  const filePath = path.join(__dirname, "..", "hr_list.xlsx");
  const resumePath = path.join(__dirname, "..", "resume.pdf");

  // Subject and body - update as needed
  const subject = "Job Application"; // Replace with actual subject
  const body = ""; // Empty body as specified

  try {
    // Phase 1: Load unsent emails
    const unsentEmails = loadUnsentEmails(filePath);
    console.log(`Found ${unsentEmails.length} unsent emails`);

    // Phase 2: Prepare batches
    const batches = prepareBatches(unsentEmails);
    console.log(`Prepared ${batches.length} batches`);

    // Process each batch
    for (const batch of batches) {
      console.log(`Processing batch of ${batch.length} emails`);

      // Phase 3: Send emails
      const sentEmails = await sendEmails(batch, subject, body, resumePath);

      // Phase 4: Update sent status
      updateSentStatus(filePath, sentEmails);

      // Optional: Delay between batches to avoid rate limits
      await new Promise((resolve) => setTimeout(resolve, 1000)); // 1 second delay
    }

    console.log("All batches processed");
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
