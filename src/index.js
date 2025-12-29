const { loadUnsentEmails } = require("../scripts/phase1");
const { prepareBatches } = require("../scripts/phase2");
const { sendEmails } = require("../scripts/phase3");
const { updateSentStatus } = require("../scripts/phase4");
const path = require("path");

async function main() {
  const filePath = path.join(__dirname, "..", "data.xlsx");
  const resumePath = path.join(__dirname, "..", "resume.pdf");

  // Load passwords from env
  const openPassword = process.env.XLSX_OPEN_PASSWORD;
  const editPassword = process.env.XLSX_EDIT_PASSWORD;

  // Subject and body - update as needed
  const subject = "Seeking Opportunity in SDE / Full Stack / AI intern";
  const body = `
                Hi,

                I enjoy solving problems and am looking for opportunities to work on real-world projects while growing as an engineer. I’ve attached my resume for any SDE / Full Stack / AI roles you might have.

                Looking forward to contributing to your team.

                Thanks & Regards,
                Surya Janardhan`; 

  try {
    // Phase 1: Load unsent emails
    const allUnsentEmails = loadUnsentEmails(filePath, openPassword, editPassword);
    console.log(`Found ${allUnsentEmails.length} unsent emails`);

    // Limit to 500 emails per run
    const unsentEmails = allUnsentEmails.slice(0, 500);
    console.log(`Processing ${unsentEmails.length} emails this run`);

    // Phase 2: Prepare batches
    const batches = prepareBatches(unsentEmails);
    console.log(`Prepared ${batches.length} batches`);

    // Process each batch
    for (const batch of batches) {
      console.log(`Processing batch of ${batch.length} emails`);

      // Phase 3: Send emails
      const sentEmails = await sendEmails(batch, subject, body, resumePath);

      // Phase 4: Update sent status
      updateSentStatus(filePath, sentEmails, editPassword);

      // Optional: Delay between batches to avoid rate limits
      await new Promise((resolve) => setTimeout(resolve, 1000)); // 1 second delay
    }

    console.log("All batches processed");
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
