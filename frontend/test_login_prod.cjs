const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    console.log('1. Navigating to production URL...');
    await page.goto('https://storage.googleapis.com/cms-automation-frontend-2025/index.html', {
      waitUntil: 'networkidle'
    });
    
    console.log('   Current URL:', page.url());
    console.log('   Title:', await page.title());
    
    await page.screenshot({ path: '/tmp/prod_1_initial.png' });
    await page.waitForTimeout(2000);
    
    console.log('2. Checking for login form elements...');
    const emailInput = await page.$('input[type="email"]');
    const passwordInput = await page.$('input[type="password"]');
    
    console.log('   Email input:', emailInput ? 'FOUND' : 'NOT FOUND');
    console.log('   Password input:', passwordInput ? 'FOUND' : 'NOT FOUND');
    
    const bodyText = await page.textContent('body');
    console.log('3. Page content (first 300 chars):');
    console.log('   ', (bodyText || 'EMPTY').slice(0, 300));
    
    await page.screenshot({ path: '/tmp/prod_2_rendered.png' });
    
    if (emailInput && passwordInput) {
      console.log('4. Filling login form...');
      await emailInput.fill('allen.chen@epochtimes.com');
      await passwordInput.fill('Editor123$');
      
      await page.screenshot({ path: '/tmp/prod_3_filled.png' });
      
      console.log('5. Clicking submit button...');
      const submitBtn = await page.$('button[type="submit"]');
      if (submitBtn) {
        await submitBtn.click();
        await page.waitForTimeout(5000);
        
        await page.screenshot({ path: '/tmp/prod_4_after_login.png' });
        console.log('   URL after login:', page.url());
        
        const errorEl = await page.$('.text-red-700, .text-red-500');
        if (errorEl) {
          const errorText = await errorEl.textContent();
          console.log('   ERROR:', errorText);
        } else if (!page.url().includes('login')) {
          console.log('   SUCCESS! Redirected to:', page.url());
        } else {
          console.log('   Still on login page - checking more...');
          await page.screenshot({ path: '/tmp/prod_5_still_login.png' });
        }
      }
    } else {
      console.log('Login form not found - page may have an error');
    }
    
    console.log('\nTest completed. Screenshots in /tmp/prod_*.png');
    
  } catch (error) {
    console.error('Error:', error.message);
    await page.screenshot({ path: '/tmp/prod_error.png' });
  } finally {
    await browser.close();
  }
})();
