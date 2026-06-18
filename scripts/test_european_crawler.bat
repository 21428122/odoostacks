@echo off
REM Test the European partners crawler

echo.
echo ============================================================
echo European Odoo Partners Crawler - Full Run
echo ============================================================
echo.
echo This will:
echo 1. Fetch the Odoo partners main page
echo 2. Extract all countries and their partner counts
echo 3. Filter for European countries only
echo 4. Crawl all European partners
echo 5. Save URLs to european_partners_real.txt
echo.
echo WARNING: This may take 10-30 minutes depending on number of partners
echo.
echo Starting...
echo.

set PYTHONIOENCODING=utf-8
python crawl_european_partners.py

echo.
echo ============================================================
echo DONE. Check european_partners_real.txt for results.
echo ============================================================
echo.
pause
