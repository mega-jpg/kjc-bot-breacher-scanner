# 💳 Card Filter System - Documentation

## 📋 Overview
Advanced credit/debit card validation system with Luhn algorithm, BIN lookup, and Steam checkout testing.

---

## 🔄 Processing Pipeline

### **Step 0: Pre-validation**
- Remove empty/unnamed columns
- Strip whitespace from card numbers
- **NEW**: Validate card format (13-19 digits)

### **Step 1: Luhn Algorithm**
- Validates checksum using Luhn mod-10 algorithm
- Filters out ~99% of fake/randomly generated cards
- **Performance**: O(n) where n = number of cards

### **Step 2: BIN Lookup**
- **OLD**: Used `binlist.net` API (rate limited to 10 req/min)
- **NEW**: Local BIN database (`bins_database.json`)
- Fallback detection by first digit:
  - `4` → Visa
  - `5` → Mastercard
  - `6` → Discover
  - `34/37` → Amex

### **Step 3: Categorization**
- Count cards by type: credit/debit/unknown
- **No filtering** - keeps all Luhn-valid cards

### **Step 4: Deduplication**
- Remove duplicate card numbers
- Keeps first occurrence

### **Step 5: Steam Checkout Testing** ⭐
- Tests cards via Steam digital wallet
- **Default limit**: 10 cards (configurable via `STEAM_TEST_LIMIT` env var)
- **Delay**: 2 seconds between requests
- **Error codes**:
  - `00` → Live (approved)
  - `51` → Live but low balance
  - `14` → Invalid card
  - `05` → Declined

---

## 🔧 Configuration

### Environment Variables
```bash
# Set custom test limit (default: 10)
export STEAM_TEST_LIMIT=20
```

### BIN Database
Edit `bins_database.json` to add custom BIN ranges:
```json
{
  "413287": {
    "type": "debit",
    "scheme": "visa",
    "brand": "Visa",
    "country": "JP"
  }
}
```

---

## 📊 CSV Format

### Required Columns
- `card_number` - Card number (13-19 digits)

### Optional Columns (for Steam testing)
- `cvv` - CVV code (3-4 digits)
- `expiration_month` - MM (1-12)
- `expiration_year` - YYYY or YY

### Example CSV
```csv
card_number,cvv,expiration_month,expiration_year
4132870318901948,232,07,2028
5412345678901234,123,12,2025
```

---

## 🚀 API Response

### Success Response
```json
{
  "success": true,
  "message": "Card filtering completed successfully",
  "stats": {
    "initial_cards": 100,
    "format_valid": 95,
    "luhn_valid": 50,
    "credit_cards": 20,
    "debit_cards": 25,
    "unknown_cards": 5,
    "final_unique": 48,
    "steam_tested": 10,
    "steam_live": 3,
    "steam_live_rate": "30.0%"
  },
  "filtered_cards": [
    {
      "card_number": "4132870318901948",
      "bin_type": "debit",
      "bin_scheme": "visa",
      "status": "live_low_balance",
      "error_code": "51",
      "check_message": "Insufficient funds"
    }
  ],
  "total_filtered": 48
}
```

---

## ⚠️ Known Limitations

1. **Steam rate limits**: Only test 10 cards by default
2. **Synchronous testing**: Cards tested sequentially (not concurrent)
3. **No proxy rotation**: Hardcoded (add via Chrome options)
4. **Selenium dependencies**: Requires Chrome + ChromeDriver
5. **BIN database**: Limited coverage (add more BINs manually)

---

## 🔒 Security Notes

- **Never commit real card data** to Git
- Use `.gitignore` for `*.csv` files
- Steam testing may violate ToS - use responsibly
- Add rate limiting on API endpoint

---

## 📈 Performance Metrics

| Cards | Luhn Filter | BIN Lookup | Dedup | Steam Test | Total Time |
|-------|-------------|------------|-------|------------|------------|
| 100   | ~0.1s       | ~0.2s      | ~0.05s| 20s (10 cards) | ~20.5s |
| 1000  | ~1s         | ~2s        | ~0.5s | 20s (10 cards) | ~24s |
| 10000 | ~10s        | ~20s       | ~5s   | 20s (10 cards) | ~55s |

**Note**: Steam testing time is constant (10 cards × 2s delay)

---

## 🐛 Troubleshooting

### "unknown/unknown" BIN results
→ Add BIN to `bins_database.json`

### "Driver initialization failed"
→ Install ChromeDriver: `pip install webdriver-manager`

### "No cards tested via Steam"
→ Check CSV has `cvv`, `expiration_month`, `expiration_year` columns

### "Rate limit exceeded"
→ Reduce `STEAM_TEST_LIMIT` or add delays

---

## 📝 Changelog

### v2.0 (Current)
- ✅ Fixed type hint (`csv_data: str` not `List[Dict]`)
- ✅ Added local BIN database (no API rate limits)
- ✅ Added card format validation (13-19 digits)
- ✅ Added configurable test limit via env var
- ✅ Added Steam live rate statistics
- ✅ Improved async/await handling
- ✅ Enhanced error messages
- ✅ Color-coded console output

### v1.0
- Initial implementation
- Luhn validation
- binlist.net integration (deprecated)
- Steam checkout testing

---

## 📞 Support

For issues or questions:
1. Check this guide
2. Review console logs
3. Inspect `filtered_cards` response
4. Check browser developer tools (Network tab)

**Made with ❤️ by KJC Company**
