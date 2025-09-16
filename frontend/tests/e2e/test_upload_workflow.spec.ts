/**
 * End-to-end test for complete upload workflow with Playwright
 */

import { test, expect, Page } from '@playwright/test';
import path from 'path';

// Test configuration
const TEST_FILE_PATH = path.join(__dirname, '../fixtures/test_data.xlsx');
const INVALID_FILE_PATH = path.join(__dirname, '../fixtures/invalid_data.xlsx');
const LARGE_FILE_PATH = path.join(__dirname, '../fixtures/large_data.xlsx');

test.describe('FundFlow Upload Workflow', () => {
  let page: Page;

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    await page.goto('/');
  });

  test.afterEach(async () => {
    await page.close();
  });

  test('should display upload interface on home page', async () => {
    // Check for upload component
    await expect(page.locator('[data-testid="file-upload"]')).toBeVisible();

    // Check for drag and drop area
    await expect(page.locator('text=Drag & drop your Excel file here')).toBeVisible();

    // Check for template download link
    await expect(page.locator('text=Download Excel Template')).toBeVisible();
  });

  test('should download template file', async () => {
    // Start download
    const downloadPromise = page.waitForEvent('download');
    await page.click('text=Download Excel Template');
    const download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toBe('fundflow_investor_template.xlsx');

    // Save and verify file exists
    const filePath = path.join(__dirname, '../downloads', download.suggestedFilename());
    await download.saveAs(filePath);

    // Verify file was saved (basic check)
    expect(await download.path()).toBeTruthy();
  });

  test('should validate file type and show error for invalid files', async () => {
    // Try uploading a non-Excel file
    const fileInput = page.locator('input[type="file"]');

    // Create a temporary text file for testing
    await fileInput.setInputFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('This is not an Excel file')
    });

    // Should show file type error
    await expect(page.locator('text=Invalid file type')).toBeVisible();
    await expect(page.locator('text=Accepted types: .xlsx, .xls')).toBeVisible();
  });

  test('should validate file size and show error for large files', async () => {
    // Mock a large file (>10MB)
    const largeFileBuffer = Buffer.alloc(11 * 1024 * 1024, 'x'); // 11MB file

    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'large_file.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: largeFileBuffer
    });

    // Should show file size error
    await expect(page.locator('text=File size exceeds 10MB limit')).toBeVisible();
  });

  test('should handle successful file upload and processing', async () => {
    // Mock API responses
    await page.route('/api/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'test-session-123',
          status: 'COMPLETED',
          message: 'File processed successfully',
          total_rows: 10,
          valid_rows: 10,
          distributions_created: 20,
          fund_info: {
            fund_code: 'FUND001',
            period_quarter: 'Q4',
            period_year: '2023'
          },
          warning_count: 0
        })
      });
    });

    // Upload a valid file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test_data.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('mock excel content')
    });

    // Click upload button
    await page.click('button:has-text("Upload")');

    // Should show processing state
    await expect(page.locator('text=Processing')).toBeVisible();

    // Should eventually show success
    await expect(page.locator('text=Upload completed successfully!')).toBeVisible();
    await expect(page.locator('text=Successfully processed 20 distributions')).toBeVisible();

    // Should show session ID
    await expect(page.locator('text=Session: test-ses...')).toBeVisible();
  });

  test('should handle validation errors in uploaded file', async () => {
    // Mock API response for validation errors
    await page.route('/api/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'test-session-456',
          status: 'FAILED_VALIDATION',
          message: 'File contains validation errors',
          total_rows: 10,
          valid_rows: 0,
          error_count: 5
        })
      });
    });

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'invalid_data.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('mock excel content with errors')
    });

    await page.click('button:has-text("Upload")');

    // Should show validation error
    await expect(page.locator('text=Validation failed: 5 errors found')).toBeVisible();
    await expect(page.locator('text=File contains 5 validation errors that prevent processing')).toBeVisible();

    // Should show Try Again button
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible();
  });

  test('should navigate to results page after successful upload', async () => {
    // Mock successful upload
    await page.route('/api/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'test-session-789',
          status: 'COMPLETED',
          message: 'File processed successfully',
          total_rows: 5,
          valid_rows: 5,
          distributions_created: 10
        })
      });
    });

    // Mock results API
    await page.route('/api/results/test-session-789', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: {
            session_id: 'test-session-789',
            status: 'COMPLETED',
            total_rows: 5,
            valid_rows: 5,
            created_at: new Date().toISOString()
          },
          distributions: {
            data: [
              {
                id: '1',
                investor_name: 'Test Investor LLC',
                entity_type: 'LLC',
                tax_state: 'NY',
                fund_code: 'FUND001',
                period: 'Q4 2023',
                jurisdiction: 'STATE',
                amount: 100000,
                composite_exemption: false,
                withholding_exemption: true,
                created_at: new Date().toISOString()
              }
            ],
            count: 1,
            summary: {
              total_amount: 100000,
              total_composite_exempt: 0,
              total_withholding_exempt: 100000,
              exemption_summary: {
                composite_exempt_count: 0,
                withholding_exempt_count: 1,
                both_exempt_count: 0,
                no_exemption_count: 0
              }
            }
          },
          validation_errors: {
            data: [],
            summary: {
              total_errors: 0,
              error_count: 0,
              warning_count: 0
            }
          }
        })
      });
    });

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test_data.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('mock excel content')
    });

    await page.click('button:has-text("Upload")');

    // Wait for success and navigate to results
    await expect(page.locator('text=Upload completed successfully!')).toBeVisible();

    // Click view results or expect automatic navigation
    if (await page.locator('button:has-text("View Results")').isVisible()) {
      await page.click('button:has-text("View Results")');
    }

    // Should be on results page
    await expect(page.locator('text=Processing Results')).toBeVisible();
    await expect(page.locator('text=Test Investor LLC')).toBeVisible();
    await expect(page.locator('text=$100,000.00')).toBeVisible();
  });

  test('should show progress tracking during upload', async () => {
    // Mock upload with progress updates
    let callCount = 0;
    await page.route('/api/upload', async route => {
      callCount++;

      // Simulate different stages of processing
      if (callCount === 1) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: 'test-session-progress',
            status: 'UPLOADING',
            message: 'Uploading file...',
            progress: 25
          })
        });
      } else {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            session_id: 'test-session-progress',
            status: 'COMPLETED',
            message: 'File processed successfully',
            total_rows: 3,
            valid_rows: 3,
            distributions_created: 6
          })
        });
      }
    });

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test_data.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('mock excel content')
    });

    await page.click('button:has-text("Upload")');

    // Should show progress bar
    await expect(page.locator('[role="progressbar"]')).toBeVisible();
    await expect(page.locator('text=Uploading file...')).toBeVisible();

    // Should eventually complete
    await expect(page.locator('text=File processed successfully')).toBeVisible();
  });

  test('should handle network errors gracefully', async () => {
    // Mock network error
    await page.route('/api/upload', async route => {
      await route.abort('failed');
    });

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test_data.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('mock excel content')
    });

    await page.click('button:has-text("Upload")');

    // Should show network error
    await expect(page.locator('text=Upload failed')).toBeVisible();
    await expect(page.locator('button:has-text("Try Again")')).toBeVisible();
  });

  test('should download results as CSV', async () => {
    // Navigate to results page (assume we have session)
    await page.goto('/results/test-session-download');

    // Mock results API
    await page.route('/api/results/test-session-download', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session: {
            session_id: 'test-session-download',
            status: 'COMPLETED',
            total_rows: 1,
            valid_rows: 1,
            created_at: new Date().toISOString()
          },
          distributions: {
            data: [{
              id: '1',
              investor_name: 'Download Test LLC',
              entity_type: 'LLC',
              tax_state: 'CA',
              fund_code: 'FUND002',
              period: 'Q1 2024',
              jurisdiction: 'STATE',
              amount: 50000,
              composite_exemption: true,
              withholding_exemption: false,
              created_at: new Date().toISOString()
            }],
            count: 1,
            summary: { total_amount: 50000 }
          },
          validation_errors: { data: [], summary: { total_errors: 0 } }
        })
      });
    });

    // Mock download API
    await page.route('/api/results/test-session-download/download*', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/csv',
        headers: {
          'Content-Disposition': 'attachment; filename=fundflow_results_test-ses.csv'
        },
        body: 'Investor Name,Entity Type,Tax State,Amount\nDownload Test LLC,LLC,CA,50000'
      });
    });

    // Wait for page to load and click download
    await expect(page.locator('text=Processing Results')).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Download CSV")');
    const download = await downloadPromise;

    // Verify download
    expect(download.suggestedFilename()).toMatch(/fundflow_results_.*\.csv/);
  });

  test('should handle duplicate file upload', async () => {
    // Mock duplicate file response
    await page.route('/api/upload', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'existing-session-123',
          status: 'COMPLETED',
          message: 'File already processed',
          duplicate: true
        })
      });
    });

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'duplicate_file.xlsx',
      mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      buffer: Buffer.from('duplicate content')
    });

    await page.click('button:has-text("Upload")');

    // Should show duplicate message
    await expect(page.locator('text=File already processed')).toBeVisible();
    await expect(page.locator('text=Session: existing-...')).toBeVisible();
  });
});