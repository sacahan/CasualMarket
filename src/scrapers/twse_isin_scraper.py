"""
TWSE ISIN scraper for fetching Taiwan securities ISIN codes and company information.

This module provides functionality to scrape the Taiwan Stock Exchange's
ISIN code listing page and extract stock information.
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from ..utils.logging import get_logger


class TWSeISINScraper:
    """
    Scraper for TWSE ISIN listings.

    Fetches and parses Taiwan Stock Exchange ISIN code listings
    from https://isin.twse.com.tw/isin/C_public.jsp?strMode=2
    """

    TWSE_ISIN_URL = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"

    def __init__(self, db_path: str | None = None):
        """
        Initialize the TWSE ISIN scraper.

        Args:
            db_path: Path to SQLite database file. If None, uses default path.
        """
        self.logger = get_logger(__name__)
        self.db_path = db_path or self._get_default_db_path()
        self.session = requests.Session()

        # Set headers to mimic a browser
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-TW,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
        )

    def _get_default_db_path(self) -> str:
        """Get default database path."""
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        return str(data_dir / "twse_securities.db")

    def fetch_isin_data(self) -> str:
        """
        Fetch ISIN data from TWSE website.

        Returns:
            Raw HTML content from the TWSE ISIN page

        Raises:
            requests.RequestException: If request fails
        """
        self.logger.info(f"從 {self.TWSE_ISIN_URL} 取得 ISIN 資料")

        try:
            response = self.session.get(self.TWSE_ISIN_URL, timeout=30)
            response.raise_for_status()

            # The content is in Big5 encoding
            response.encoding = "big5"

            self.logger.info(f"成功取得 ISIN 資料 ({len(response.text)} 字元)")
            return response.text

        except requests.RequestException as e:
            self.logger.error(f"取得 ISIN 資料失敗: {e}")
            raise

    def parse_isin_data(self, html_content: str) -> list[dict[str, str]]:
        """
        Parse ISIN data from HTML content, filtering for regular stocks only.

        Args:
            html_content: Raw HTML content from TWSE ISIN page

        Returns:
            List of dictionaries containing stock information (regular stocks only)
        """
        self.logger.info("解析 HTML 內容中的 ISIN 資料")

        soup = BeautifulSoup(html_content, "html.parser")

        # Find the main table
        tables = soup.find_all("table")
        data_table = None

        for table in tables:
            if table.get("class") == ["h4"]:
                data_table = table
                break

        if not data_table:
            self.logger.error("在 HTML 內容中找不到資料表格")
            return []

        securities = []
        rows = data_table.find_all("tr")
        current_section = None

        for row in rows[1:]:  # Skip header row
            cells = row.find_all("td")

            if len(cells) < 6:
                continue

            # Check for section header rows
            if cells[0].get("colspan"):
                # This is a section header
                header_text = cells[0].get_text(strip=True)
                current_section = header_text
                self.logger.debug(f"找到區塊標題: {header_text}")
                continue

            try:
                # Extract stock code and company name from first cell
                first_cell_text = cells[0].get_text(strip=True)

                # Use regex to separate stock code and company name
                # Handle both regular 4-digit codes and ETF codes with letters (e.g., 00648R, 00670L)
                match = re.match(r"(\d{4,6}[A-Z]*)\s*(.+)", first_cell_text)
                if not match:
                    continue

                stock_code = match.group(1)
                raw_company_name = match.group(2)

                # Extract other fields first
                isin_code = cells[1].get_text(strip=True)
                listing_date = cells[2].get_text(strip=True)
                market_type = cells[3].get_text(strip=True)
                industry = cells[4].get_text(strip=True)
                cfi_code = cells[5].get_text(strip=True)

                # Check if this is a valid security (stock or ETF)
                is_valid, security_type = self._is_valid_security(
                    stock_code, raw_company_name, cfi_code
                )
                if not is_valid:
                    continue

                # Clean the company name
                company_name = self._clean_company_name(raw_company_name)

                # For stocks, require industry. For ETFs, industry can be empty
                if security_type == "stock" and not industry.strip():
                    continue

                security_info = {
                    "stock_code": stock_code,
                    "company_name": company_name,
                    "isin_code": isin_code,
                    "listing_date": listing_date,
                    "market_type": market_type,
                    "industry": industry,
                    "cfi_code": cfi_code,
                    "security_type": security_type,
                    "scraped_at": datetime.now().isoformat(),
                }

                securities.append(security_info)

            except Exception as e:
                self.logger.warning(f"解析資料列失敗: {e}")
                continue

        self.logger.info(f"成功解析 {len(securities)} 項證券 (股票和ETF)")
        return securities

    def _is_valid_security(
        self, stock_code: str, company_name: str, cfi_code: str
    ) -> tuple[bool, str]:
        """
        Check if this is a valid security (stock or ETF) to include.

        Args:
            stock_code: 4-digit stock code
            company_name: Company name from the first cell
            cfi_code: CFI code for the security

        Returns:
            Tuple of (is_valid, security_type) where security_type is 'stock' or 'etf'
        """
        # Check if it's an ETF
        if self._is_etf(stock_code, cfi_code):
            return True, "etf"

        # Check if it's a regular stock
        if self._is_regular_stock(stock_code, company_name, cfi_code):
            return True, "stock"

        return False, ""

    def _is_etf(self, stock_code: str, cfi_code: str) -> bool:
        """
        Check if this is an ETF.

        Args:
            stock_code: 4-digit or 6-digit stock code
            cfi_code: CFI code for the security

        Returns:
            True if this is an ETF, False otherwise
        """
        # ETFs typically have CFI code starting with 'CEOG'
        if cfi_code.startswith("CEOG"):
            return True

        # ETFs typically have codes starting with 00 or 006
        if stock_code.startswith("00"):
            return True

        return False

    def _is_regular_stock(
        self, stock_code: str, company_name: str, cfi_code: str
    ) -> bool:
        """
        Check if this is a regular stock (not warrant, option, or special stock).

        Args:
            stock_code: 4-digit stock code
            company_name: Company name from the first cell
            cfi_code: CFI code for the security

        Returns:
            True if this is a regular stock, False otherwise
        """
        # ETFs are handled separately
        if self._is_etf(stock_code, cfi_code):
            return False

        # Filter out warrants and options (codes starting with 0 but not ETFs)
        if stock_code.startswith("0") and not stock_code.startswith("00"):
            return False

        # Filter out entries with special prefixes
        prefixes_to_exclude = [
            "A　",
            "B　",
            "C　",
            "D　",
            "E　",
            "F　",
            "G　",
            "H　",
            "9U　",
            "9V　",
            "9W　",
            "9X　",
            "9Y　",
            "9Z　",
            "01　",
            "02　",
            "03　",
            "04　",
            "05　",
            "特　",
            "乙　",
            "甲　",
        ]

        for prefix in prefixes_to_exclude:
            if company_name.startswith(prefix):
                return False

        # Regular stocks typically have codes 1000-9999
        try:
            code_num = int(stock_code)
            if code_num < 1000:
                return False
        except ValueError:
            return False

        # Regular stocks should have CFI code 'ESVUFR'
        if cfi_code == "ESVUFR":
            return True

        return False

    def _clean_company_name(self, raw_name: str) -> str:
        """
        Clean the company name by removing unwanted prefixes and suffixes.

        Args:
            raw_name: Raw company name from HTML

        Returns:
            Cleaned company name
        """
        # Remove common prefixes that might have been missed
        prefixes_to_remove = ["　", "\u3000", " "]  # Various space characters

        cleaned = raw_name
        for prefix in prefixes_to_remove:
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix) :]

        # Remove trailing spaces and special characters
        cleaned = cleaned.strip()

        return cleaned

    def init_database(self) -> None:
        """Initialize SQLite database with required tables."""
        self.logger.info(f"在 {self.db_path} 初始化資料庫")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create securities table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS securities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT UNIQUE NOT NULL,
                    company_name TEXT NOT NULL,
                    isin_code TEXT UNIQUE NOT NULL,
                    listing_date TEXT,
                    market_type TEXT,
                    industry TEXT,
                    cfi_code TEXT,
                    security_type TEXT DEFAULT 'stock',
                    scraped_at TEXT NOT NULL,
                    updated_at TEXT,
                    UNIQUE(stock_code, isin_code)
                )
            """
            )

            # Add security_type column if it doesn't exist (for existing databases)
            try:
                cursor.execute(
                    "ALTER TABLE securities ADD COLUMN security_type TEXT DEFAULT 'stock'"
                )
                self.logger.info("已新增 security_type 欄位至現有表格")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Create index for faster lookups
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_stock_code
                ON securities(stock_code)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_isin_code
                ON securities(isin_code)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_company_name
                ON securities(company_name)
            """
            )

            conn.commit()

        self.logger.info("資料庫初始化完成")

    def save_to_database(self, securities: list[dict[str, str]]) -> int:
        """
        Save securities data to SQLite database.

        Args:
            securities: List of security dictionaries

        Returns:
            Number of records inserted/updated
        """
        if not securities:
            self.logger.warning("沒有證券資料可儲存")
            return 0

        self.logger.info(f"儲存 {len(securities)} 項證券資料至資料庫")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            inserted_count = 0
            updated_count = 0

            for security in securities:
                try:
                    # Try to insert new record
                    cursor.execute(
                        """
                        INSERT INTO securities (
                            stock_code, company_name, isin_code, listing_date,
                            market_type, industry, cfi_code, security_type, scraped_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            security["stock_code"],
                            security["company_name"],
                            security["isin_code"],
                            security["listing_date"],
                            security["market_type"],
                            security["industry"],
                            security["cfi_code"],
                            security["security_type"],
                            security["scraped_at"],
                        ),
                    )
                    inserted_count += 1

                except sqlite3.IntegrityError:
                    # Record exists, update it
                    cursor.execute(
                        """
                        UPDATE securities SET
                            company_name = ?,
                            listing_date = ?,
                            market_type = ?,
                            industry = ?,
                            cfi_code = ?,
                            security_type = ?,
                            updated_at = ?
                        WHERE stock_code = ? OR isin_code = ?
                    """,
                        (
                            security["company_name"],
                            security["listing_date"],
                            security["market_type"],
                            security["industry"],
                            security["cfi_code"],
                            security["security_type"],
                            datetime.now().isoformat(),
                            security["stock_code"],
                            security["isin_code"],
                        ),
                    )
                    updated_count += 1

            conn.commit()

        total_processed = inserted_count + updated_count
        self.logger.info(
            f"Database save completed: {inserted_count} inserted, {updated_count} updated"
        )
        return total_processed

    def get_company_by_code(self, stock_code: str) -> dict[str, str] | None:
        """
        Get company information by stock code.

        Args:
            stock_code: 4-digit stock code

        Returns:
            Dictionary with company information or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT stock_code, company_name, isin_code, listing_date,
                       market_type, industry, cfi_code, security_type
                FROM securities
                WHERE stock_code = ?
            """,
                (stock_code,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "stock_code": row[0],
                    "company_name": row[1],
                    "isin_code": row[2],
                    "listing_date": row[3],
                    "market_type": row[4],
                    "industry": row[5],
                    "cfi_code": row[6],
                    "security_type": row[7] if len(row) > 7 else "stock",
                }

        return None

    def search_companies(self, query: str, limit: int = 10) -> list[dict[str, str]]:
        """
        Search companies by name or stock code.

        Args:
            query: Search query (company name or stock code)
            limit: Maximum number of results

        Returns:
            List of matching companies
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT stock_code, company_name, isin_code, listing_date,
                       market_type, industry, cfi_code, security_type
                FROM securities
                WHERE stock_code LIKE ? OR company_name LIKE ?
                ORDER BY stock_code
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            rows = cursor.fetchall()
            return [
                {
                    "stock_code": row[0],
                    "company_name": row[1],
                    "isin_code": row[2],
                    "listing_date": row[3],
                    "market_type": row[4],
                    "industry": row[5],
                    "cfi_code": row[6],
                    "security_type": row[7] if len(row) > 7 else "stock",
                }
                for row in rows
            ]

    def scrape_and_save(self) -> int:
        """
        Complete scraping workflow: fetch, parse, and save data.

        Returns:
            Number of records processed
        """
        self.logger.info("開始 TWSE ISIN 爬取流程")

        try:
            # Initialize database
            self.init_database()

            # Fetch data
            html_content = self.fetch_isin_data()

            # Parse data
            securities = self.parse_isin_data(html_content)

            # Save to database
            processed_count = self.save_to_database(securities)

            self.logger.info(f"TWSE ISIN 爬取成功完成: 處理了 {processed_count} 筆記錄")
            return processed_count

        except Exception as e:
            self.logger.error(f"TWSE ISIN 爬取失敗: {e}")
            raise
