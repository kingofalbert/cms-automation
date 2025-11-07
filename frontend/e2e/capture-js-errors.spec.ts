import { test } from '@playwright/test';

test('capture JavaScript runtime errors', async ({ page }) => {
  const consoleMessages: Array<{ type: string; text: string; args: string[] }> = [];
  const pageErrors: Array<{name: string, message: string, stack: string}> = [];

  // Capture console messages with details
  page.on('console', async (msg) => {
    const args = await Promise.all(
      msg.args().map(async (arg) => {
        try {
          return await arg.jsonValue();
        } catch {
          return arg.toString();
        }
      })
    );
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
      args: args.map((a) => typeof a === 'object' ? JSON.stringify(a, null, 2) : String(a)),
    });
  });

  // Capture page errors with full details
  page.on('pageerror', (error) => {
    pageErrors.push({
      name: error.name,
      message: error.message,
      stack: error.stack || '',
    });
  });

  // Navigate to worklist
  await page.goto('https://storage.googleapis.com/cms-automation-frontend-cmsupload-476323/index.html#/worklist', {
    waitUntil: 'networkidle',
  });

  // Clear storage and reload
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.reload({ waitUntil: 'networkidle' });

  console.log('📍 Navigating to worklist...');
  await page.waitForTimeout(2000);

  // Click review button
  const reviewButton = page.getByRole('button', { name: /审核|review/i }).first();
  await reviewButton.click();

  console.log('🖱️ Clicked review button, waiting for errors...');
  await page.waitForTimeout(5000);

  // Log all console messages
  console.log('\n=== CONSOLE MESSAGES ===');
  if (consoleMessages.length === 0) {
    console.log('No console messages');
  } else {
    consoleMessages.forEach((msg, index) => {
      console.log(`\n[${index + 1}] ${msg.type.toUpperCase()}:`);
      console.log(`Text: ${msg.text}`);
      if (msg.args.length > 0) {
        console.log(`Args:`);
        msg.args.forEach((arg, i) => {
          console.log(`  [${i}]: ${arg}`);
        });
      }
    });
  }

  // Log page errors
  console.log('\n=== PAGE/REACT ERRORS ===');
  if (pageErrors.length === 0) {
    console.log('No page errors');
  } else {
    pageErrors.forEach((error, index) => {
      console.log(`\n[${index + 1}] ${error.name}: ${error.message}`);
      console.log(`Stack:\n${error.stack}`);
    });
  }

  // Take screenshot
  await page.screenshot({ path: '/tmp/capture-js-errors.png', fullPage: true });
  console.log('\nScreenshot saved to /tmp/capture-js-errors.png');
});
