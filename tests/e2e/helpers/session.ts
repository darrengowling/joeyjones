/**
 * Prompt C: Playwright session helper
 * Sets user data in localStorage before page navigation to prevent auth redirects
 */

import { Page } from '@playwright/test';

/**
 * Sets user session in localStorage before page loads
 * Prevents AuctionRoom from redirecting to home due to missing user
 * 
 * @param page - Playwright page object
 * @param user - User object with id, name, email
 */
export async function setUserSession(page: Page, user: any) {
  await page.addInitScript((userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
  }, user);
}
