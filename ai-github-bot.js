"use strict";

// This legacy bot previously committed and pushed AI-generated code directly.
// It is intentionally disabled until a reviewed branch/PR workflow and tests exist.
function run() {
  throw new Error(
    "AI GitHub auto-edit/push is disabled. Use a reviewed branch and pull request workflow instead."
  );
}

if (require.main === module) {
  try {
    run();
  } catch (error) {
    process.stderr.write(`DISABLED: ${error.message}\n`);
    process.exitCode = 1;
  }
}

module.exports = { run };
