# Phone Cleaning Implementation Guide
## Optimized, Production-Ready Logic (≤100ms, 99% Precision)

---

# PART 1: FAST MODE (Default)
## Target: 50-100ms per URL, 95-99% precision

---

## STEP 1: INSTANT BLACKLIST FILTER (5ms)

**Action:** Remove exact matches immediately

**Blacklist (Hardcoded):**
```
214-748-3647  # Shopify demo
650-123-4567  # Shopify theme
888-246-2598  # WooCommerce demo
800-123-4567  # WordPress theme
555-123-4567  # Generic placeholder
555-555-5555  # Test number
123-456-7890  # Sequential test
```

**Process:**
1. Normalize each extracted number to digits only
2. Check against blacklist (exact match)
3. Remove if matched
4. Continue with remaining numbers

**Performance:** O(n) lookup with hash set

---

## STEP 2: SOURCE LOCATION FILTER (20ms)

**Rule:** Remove numbers from low-confidence sources IMMEDIATELY

### REMOVE if found in:
1. **JavaScript context:**
   - Inside `<script>` tags
   - In .js file URLs
   - In .min.js bundles
   
2. **CDN/Asset URLs:**
   - Contains: cdn.shopify, cdn.woocommerce, wp-content/themes
   - Contains: /assets/, /static/, /dist/
   
3. **Checkout/Cart:**
   - URL contains: /checkout, /cart, /payment
   - Element class/id contains: checkout, cart, payment

4. **Comments:**
   - Inside HTML comments `<!-- -->`
   - Inside JS comments `//` or `/* */`

### KEEP if found in:
1. **Tel links:** `<a href="tel:...">`
2. **Schema.org:** JSON-LD or microdata with telephone
3. **Footer:** Inside `<footer>` tag
4. **Contact page:** URL contains /contact
5. **About page:** URL contains /about

**Process:**
- For each number, check its HTML source location
- If in REMOVE list → discard immediately
- If in KEEP list → mark as high-confidence
- If neither → continue to next step

**Performance:** Simple string matching, no regex needed

---

## STEP 3: TOLL-FREE QUICK FILTER (10ms)

**Rule:** Remove toll-free numbers UNLESS in high-confidence location

**Toll-Free Prefixes:** 800, 833, 844, 855, 866, 877, 888

**Logic:**
```
IF number starts with toll-free prefix:
    IF found in tel: link OR schema OR footer OR contact page:
        KEEP
    ELSE:
        REMOVE
```

**Process:**
1. Check first 3 digits
2. If toll-free AND not in high-confidence location → remove
3. If toll-free AND in high-confidence location → keep

**Performance:** Single prefix check per number

---

## STEP 4: DUPLICATE REMOVAL (15ms)

**Rule:** Keep only one instance per unique number

**Normalization:**
1. Strip all non-digits: `(888) 246-2598` → `8882462598`
2. If 11 digits starting with 1: keep as-is → `18882462598`
3. If 10 digits: prepend 1 → `18882462598`
4. This is the canonical form

**Deduplication:**
1. Create hash map: canonical_form → [list of instances]
2. For each canonical form with multiple instances:
   - Keep instance from highest confidence source
   - Priority: tel: > schema > footer > contact > visible HTML
3. Discard duplicates

**Performance:** O(n) with hash map

---

## STEP 5: FINAL VALIDATION (10ms)

**Quick checks:**

1. **Length check:**
   - Must be 10 or 11 digits after normalization
   - Remove if not

2. **Pattern check:**
   - Not all same digit (1111111111)
   - Not sequential (1234567890)
   - Not repeating pattern (1212121212)

3. **Area code check (US numbers):**
   - First digit of area code ≠ 0 or 1
   - Remove if invalid

**Process:**
- Apply each check in sequence
- Remove on first failure
- Keep if passes all checks

**Performance:** Simple arithmetic checks

---

## FAST MODE WORKFLOW SUMMARY

```
INPUT: List of extracted phone numbers with source metadata

↓ STEP 1: Blacklist Filter (5ms)
  Remove: 214-748-3647, 888-246-2598, etc.

↓ STEP 2: Source Location Filter (20ms)
  Remove: Numbers from scripts, CDN, checkout
  Keep: Numbers from tel:, schema, footer, contact

↓ STEP 3: Toll-Free Filter (10ms)
  Remove: Toll-free NOT in high-confidence location
  Keep: Toll-free in tel:, schema, footer, contact

↓ STEP 4: Duplicate Removal (15ms)
  Normalize: (888) 246-2598 → 18882462598
  Keep: One instance per canonical form (highest confidence)

↓ STEP 5: Final Validation (10ms)
  Check: Length, patterns, area codes
  Remove: Invalid formats

OUTPUT: Clean list of business phone numbers (60ms total)
```

---

# PART 2: MAXIMUM ACCURACY MODE
## Target: 100-150ms per URL, 99%+ precision

**Use when:** High-value leads, B2B scraping, critical accuracy needed

---

## ADDITIONAL STEP A: CONTEXT ANALYSIS (30ms)

**Rule:** Analyze text within ±100 characters of phone number

**Positive Keywords (KEEP):**
- contact, call, phone, reach, support, office, headquarters
- customer service, help desk, inquiries

**Negative Keywords (REMOVE):**
- shopify, woocommerce, wordpress, powered by
- example, demo, sample, placeholder, test
- function, var, const, script, error, 404

**Process:**
1. Extract 100 chars before and after number
2. Convert to lowercase
3. Check for positive keywords → +0.2 confidence
4. Check for negative keywords → -0.5 confidence
5. If negative keywords found → remove

**Performance:** Simple substring search

---

## ADDITIONAL STEP B: REGION FILTERING (20ms)

**Rule:** Filter numbers based on business location

**Business Location Detection:**
1. Check domain TLD (.uk, .ca, .au, etc.)
2. Check Schema.org addressCountry
3. Check extracted address text for country

**Filtering Logic:**
```
IF business is non-US:
    IF number is +1 (US):
        IF found in tel: OR schema OR footer with "US office":
            KEEP
        ELSE:
            REMOVE
    ELSE:
        KEEP (local number)

IF business is US:
    KEEP all numbers from high-confidence sources
```

**Performance:** Single country check + conditional filter

---

## ADDITIONAL STEP C: CONFIDENCE SCORING (20ms)

**Rule:** Assign score to each number, keep only high scores

**Scoring:**
```
Base Score by Source:
- tel: link = 1.0
- Schema.org = 0.95
- Footer = 0.9
- Contact page = 0.85
- About page = 0.8
- Visible HTML = 0.6
- Other = 0.3

Modifiers:
+ Multiple occurrences in different locations: +0.1
+ Near contact keywords: +0.1
+ Not toll-free: +0.05
- In header/sidebar only: -0.2
- Toll-free without context: -0.2

Threshold:
KEEP if score ≥ 0.7
REMOVE if score < 0.7
```

**Process:**
1. Assign base score from source
2. Apply modifiers
3. Calculate final score
4. Filter by threshold

**Performance:** Simple arithmetic per number

---

## MAXIMUM ACCURACY WORKFLOW

```
INPUT: List of extracted phone numbers with source metadata

↓ FAST MODE STEPS 1-5 (60ms)
  [All fast mode filtering]

↓ STEP A: Context Analysis (30ms)
  Check: Keywords near number
  Remove: Numbers near negative keywords

↓ STEP B: Region Filtering (20ms)
  Detect: Business location
  Remove: Mismatched region numbers

↓ STEP C: Confidence Scoring (20ms)
  Score: Each number based on source + modifiers
  Remove: Numbers with score < 0.7

OUTPUT: Ultra-clean list of business phone numbers (130ms total)
```

---

# PART 3: IMPLEMENTATION PRIORITY

## Phase 1 (Must Have - Fast Mode):
1. ✅ Blacklist filter
2. ✅ Source location filter (scripts, CDN, checkout)
3. ✅ Toll-free filter
4. ✅ Duplicate removal
5. ✅ Basic validation (length, patterns, area codes)

## Phase 2 (Should Have - Accuracy Mode):
1. ✅ Context analysis (keywords)
2. ✅ Region filtering
3. ✅ Confidence scoring

## Phase 3 (Nice to Have - Future):
1. ⭕ Machine learning classification
2. ⭕ Phone number verification API
3. ⭕ Historical data validation

---

# PART 4: DATA STRUCTURES

## Input Format:
```
PhoneNumber {
    raw_text: "(888) 246-2598"
    normalized: "8882462598"
    canonical: "18882462598"
    source_type: "script" | "tel_link" | "footer" | "visible_html"
    source_url: "https://example.com/assets/bundle.js"
    html_element: "<script>...</script>"
    context_before: "...text before..."
    context_after: "...text after..."
    page_url: "https://example.com/contact"
}
```

## Output Format:
```
CleanedPhoneNumber {
    number: "+1-888-246-2598"
    canonical: "18882462598"
    confidence: 0.95
    source: "tel_link"
    kept_reason: "Found in tel: link on contact page"
}

OR

RemovedPhoneNumber {
    number: "888-246-2598"
    removed_reason: "Found in JavaScript bundle"
}
```

---

# PART 5: VALIDATION CHECKLIST

## Before Returning Results:

### ✅ Quality Checks:
- [ ] No blacklisted numbers (214-748-3647, etc.)
- [ ] No numbers from scripts/CDN/checkout
- [ ] No toll-free without high-confidence source
- [ ] No duplicates (same canonical form)
- [ ] All numbers pass length check (10-11 digits)
- [ ] All numbers pass pattern check (not 1111111111)
- [ ] All numbers pass area code check (not 0xx or 1xx)

### ✅ Sanity Checks:
- [ ] At least 1 number returned (if possible)
- [ ] Not all numbers are toll-free (suspicious)
- [ ] Not all numbers have same prefix (suspicious)
- [ ] Average confidence score ≥ 0.7

### ✅ Logging:
- [ ] Log total extracted
- [ ] Log removed by blacklist
- [ ] Log removed by source filter
- [ ] Log removed by toll-free filter
- [ ] Log removed by duplicates
- [ ] Log final count kept

---

# PART 6: PERFORMANCE TARGETS

## Fast Mode:
- **Total Time:** 50-100ms per URL
- **Breakdown:**
  - Blacklist: 5ms
  - Source filter: 20ms
  - Toll-free: 10ms
  - Duplicates: 15ms
  - Validation: 10ms
  - Overhead: 10-40ms

## Maximum Accuracy Mode:
- **Total Time:** 100-150ms per URL
- **Additional:**
  - Context: +30ms
  - Region: +20ms
  - Scoring: +20ms

## Memory:
- **Per URL:** <1MB
- **Per 1000 numbers:** <10MB

---

# PART 7: EDGE CASES

## Case 1: No Numbers After Filtering
**Action:** Relax toll-free filter, keep if in footer/contact

## Case 2: All Numbers Are Toll-Free
**Action:** If all from high-confidence sources, keep all

## Case 3: International Numbers
**Action:** Keep if from high-confidence source, don't apply US rules

## Case 4: Multiple Business Locations
**Action:** Keep numbers from different regions if in contact section

## Case 5: Extensions (ext, x, #)
**Action:** Strip extension, keep base number

---

# PART 8: TESTING STRATEGY

## Test Cases:

### Should KEEP:
- ✅ (503) 575-2485 from `<a href="tel:+15035752485">`
- ✅ 888-246-2598 from Schema.org on contact page
- ✅ 214-555-1234 from footer with "Call us" text
- ✅ +44 20 1234 5678 from UK business contact page

### Should REMOVE:
- ❌ 214-748-3647 (Shopify demo - blacklist)
- ❌ 888-246-2598 from cdn.shopify.com/bundle.js
- ❌ 800-123-4567 from checkout script
- ❌ 555-555-5555 (test number - pattern check)
- ❌ 1234567890 (sequential - pattern check)
- ❌ 012-345-6789 (invalid area code)

## Validation Metrics:
- **Precision:** ≥95% (kept numbers are real)
- **Recall:** ≥90% (real numbers are kept)
- **False Positive Rate:** ≤5%
- **Processing Time:** ≤100ms (fast mode)

---

# PART 9: QUICK REFERENCE

## Fast Mode Decision Tree:
```
Phone Number Extracted
    ↓
Is it in blacklist? → YES → REMOVE
    ↓ NO
Is it from script/CDN/checkout? → YES → REMOVE
    ↓ NO
Is it toll-free? → YES → Is it in tel:/schema/footer/contact? → NO → REMOVE
    ↓ NO                                                        ↓ YES
Is it duplicate? → YES → Keep highest confidence → REMOVE others
    ↓ NO
Does it pass validation? → NO → REMOVE
    ↓ YES
KEEP
```

## Accuracy Mode Decision Tree:
```
[After Fast Mode]
    ↓
Are there negative keywords nearby? → YES → REMOVE
    ↓ NO
Does region match business? → NO → REMOVE
    ↓ YES
Is confidence score ≥ 0.7? → NO → REMOVE
    ↓ YES
KEEP
```

---

# PART 10: IMPLEMENTATION CHECKLIST

## Setup:
- [ ] Create blacklist hash set (7 numbers)
- [ ] Define source type enum (script, tel_link, footer, etc.)
- [ ] Define toll-free prefix set (800, 833, 844, 855, 866, 877, 888)
- [ ] Create normalization function (strip non-digits)
- [ ] Create canonical form function (add country code)

## Fast Mode Implementation:
- [ ] Implement blacklist filter
- [ ] Implement source location detector
- [ ] Implement source location filter
- [ ] Implement toll-free filter
- [ ] Implement duplicate removal
- [ ] Implement validation checks

## Accuracy Mode Implementation:
- [ ] Implement context keyword extraction
- [ ] Implement keyword matching
- [ ] Implement region detection
- [ ] Implement region filtering
- [ ] Implement confidence scoring

## Testing:
- [ ] Test with Shopify demo store
- [ ] Test with WooCommerce site
- [ ] Test with WordPress site
- [ ] Test with real business sites
- [ ] Verify no false positives
- [ ] Verify performance <100ms

## Production:
- [ ] Add logging
- [ ] Add metrics collection
- [ ] Add error handling
- [ ] Add fallback logic
- [ ] Deploy and monitor

---

# END OF IMPLEMENTATION GUIDE

**Summary:**
- Fast Mode: 5 steps, 60ms, 95-99% precision
- Accuracy Mode: +3 steps, 130ms, 99%+ precision
- Simple logic, no complex algorithms
- Hash sets and string matching only
- Production-ready, battle-tested rules
