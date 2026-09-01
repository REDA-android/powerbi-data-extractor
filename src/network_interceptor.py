"""
Power BI Network and Playwright Interceptor.
Automates browser navigation to Power BI reports, intercepts querydata payloads, and falls back to DOM/Vision extraction.
"""

import asyncio
import json
import os
from typing import List, Dict, Any, Optional
from vision_extractor import PowerBIVisionExtractor


class PowerBINetworkInterceptor:
    """Extracts data from live Power BI reports via Playwright & Network interception."""

    def __init__(self, vision_extractor: Optional[PowerBIVisionExtractor] = None):
        self.vision = vision_extractor or PowerBIVisionExtractor()

    async def scrape_powerbi_url(self, url: str, timeout_sec: int = 25) -> Dict[str, Any]:
        """
        Navigates to Power BI URL, intercepts data payloads, or captures screenshot for Vision AI.
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                "success": False,
                "error": "Playwright is not installed in the environment.",
                "records": [],
            }

        intercepted_payloads = []

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            )
            page = await context.new_page()

            # Listen for network responses
            async def handle_response(response):
                req_url = response.url
                if "querydata" in req_url or "executeQueries" in req_url or "modelsAndExploration" in req_url:
                    try:
                        data = await response.json()
                        intercepted_payloads.append(data)
                    except Exception:
                        pass

            page.on("response", handle_response)

            try:
                # Navigate to Power BI report
                await page.goto(url, wait_until="networkidle", timeout=timeout_sec * 1000)
                # Give 3 seconds for visual animations and data rendering
                await asyncio.sleep(3.5)

                # 1. Check if we intercepted clean network querydata
                records_from_network = self._parse_network_data(intercepted_payloads)
                if records_from_network and len(records_from_network) > 0:
                    await browser.close()
                    return {
                        "success": True,
                        "method": "network_querydata_intercept",
                        "records": records_from_network,
                    }

                # 2. Extract DOM grid elements if present
                dom_records = await self._extract_dom_tables(page)
                if dom_records and len(dom_records) > 0:
                    await browser.close()
                    return {
                        "success": True,
                        "method": "dom_grid_extraction",
                        "records": dom_records,
                    }

                # 3. Fallback: High-resolution full-page screenshot to Gemini Vision
                screenshot_bytes = await page.screenshot(full_page=False)
                await browser.close()

                vision_records = self.vision.extract_from_image_bytes(screenshot_bytes)
                return {
                    "success": True if vision_records else False,
                    "method": "playwright_screenshot_gemini_vision",
                    "records": vision_records,
                }

            except Exception as e:
                await browser.close()
                return {
                    "success": False,
                    "error": f"Browser navigation error: {str(e)}",
                    "records": [],
                }

    def _parse_network_data(self, payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parses Power BI internal semantic querydata JSON structures."""
        records = []
        for p in payloads:
            try:
                results = p.get("results", [])
                for r in results:
                    data = r.get("result", {}).get("data", {})
                    dsr = data.get("dsr", {}).get("DataShapes", [])
                    for shape in dsr:
                        primary = shape.get("Primary", {}).get("Data", [])
                        for item in primary:
                            if isinstance(item, dict):
                                records.append(item)
            except Exception:
                pass
        return records

    async def _extract_dom_tables(self, page) -> List[Dict[str, Any]]:
        """Extracts tabular data from rendered Power BI matrix and visual containers."""
        try:
            # Query table/grid rows
            rows_text = await page.evaluate("""() => {
                const results = [];
                const grids = document.querySelectorAll('div[role="grid"], .visual-table, .tableEx, .matrix');
                grids.forEach(g => {
                    const rows = g.querySelectorAll('div[role="row"], tr');
                    rows.forEach(r => {
                        const cells = Array.from(r.querySelectorAll('div[role="gridcell"], div[role="columnheader"], td, th')).map(c => c.innerText.trim());
                        if (cells.length > 0) results.push(cells);
                    });
                });
                return results;
            }""")

            if rows_text and len(rows_text) > 1:
                headers = rows_text[0]
                records = []
                for row in rows_text[1:]:
                    if len(row) == len(headers):
                        records.append(dict(zip(headers, row)))
                    else:
                        records.append({f"col_{i+1}": val for i, val in enumerate(row)})
                return records
        except Exception:
            pass
        return []
