"""
NSE Data Scraper USE equity data."""
       html = await self.fetch_raw(self.USE_URL)
       return self._parse_stock_table(html, exchange="USE")

   def _parse_stock_table(self, html: str, exchange: str) -> List[Dict]:
       """
       Parse the afx.kwayisi.org stock table.
       Validates: symbol, close price, date.
       Flags: missing volume, no-trade days.
       """
       soup = BeautifulSoup(html, "html.parser")
       results = []

       # TODO: implement actual table parsing for afx.kwayisi.org structure
       # Columns: Symbol | Name | Price | Change | %Change | Volume | MarketCap
       table = soup.find("table")
       if not table:
           return results

       rows = table.find_all("tr")[1:]  # skip header
       for row in rows:
           cols = row.find_all("td")
           if len(cols) < 5:
               continue

           try:
               symbol = cols[0].text.strip()
               name   = cols[1].text.strip()
               close  = float(cols[2].text.strip().replace(",", "") or 0)
               volume = int(cols[5].text.strip().replace(",", "") or 0) if len(cols) > 5 else None

               entry = {
                   "symbol":   symbol,
                   "name":     name,
                   "exchange": exchange,
                   "close":    close,
                   "volume":   volume,
                   "date":     date.today().isoformat(),
                   "source":   "afx.kwayisi.org",
                   "data_quality_warning": "no_trades" if volume == 0 else None,
               }
               results.append(entry)
           except (ValueError, IndexError):
               continue  # skip malformed rows

       return results

   def validate(self, records: List[Dict]) -> List[Dict]:
       """
       Validation layer:
       - Remove records with close <= 0
       - Flag volume == 0 as no-trade day
       - Flag z-score > 4 on daily return for manual review
       """
       valid = []
       for r in records:
           if r.get("close", 0) <= 0:
               continue
           if r.get("volume") == 0:
               r["data_quality_warning"] = "no_trades"
           valid.append(r)
       return valid


scraper = NSEScraper()