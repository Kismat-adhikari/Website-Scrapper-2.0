# Phone Number Cleaning & Validation Architecture
## System Design for Removing Platform Junk While Keeping Real Business Numbers

---

## 1. PLATFORM JUNK DETECTION RULES

### 1.1 Known Platform Dummy Numbers (Blacklist)
**Rule:** Maintain a blacklist of commonly used dummy/example numbers

**Shopify Common Numbers:**
- 214-748-3647 (Shopify demo store default)
- 650-123-4567 (Shopify theme placeholder)
- 555-123-4567 (Generic placeholder)
- 123-456-7890 (Sequential test number)

**WooCommerce/WordPress Common Numbers:**
- 888-246-2598 (WooCommerce demo)
- 800-123-4567 (WordPress theme placeholder)
- 555-555-5555 (Generic test)

**Action:** Exact match against blacklist → Remove immediately

### 1.2 Toll-Free Number Filtering Logic

**US Toll-Free Prefixes:**
- 800, 833, 844, 855, 866, 877, 888

**Conditional Removal Rules:**

**REMOVE toll-free IF:**
1. Found in JavaScript files (.js, .min.js)
2. Found in CDN URLs (cdn.shopify.com, woocommerce.com, etc.)
3. Found in checkout/cart scripts
4. Found in analytics/tracking code
5. Found in theme bundle files
6. NOT found in any high-confidence location
7. Business location is non-US AND toll-free not in contact section

**KEEP toll-free IF:**
1. Found in `<a href="tel:">` tag
2. Found in Schema.org/JSON-LD structured data
3. Found in footer with "contact" or "support" keywords nearby
4. Found on dedicated contact page
5. Found in "about us" section
6. Multiple occurrences across different high-confidence locations
7. Business is US-based AND found in visible HTML

**Priority:** Context overrides prefix - high-confidence location = keep

---

## 2. SOURCE LOCATION DETECTION

### 2.1 High-Confidence Sources (KEEP)
**Confidence Score: 0.9-1.0**

1. **Telephone Links**
   - `<a href="tel:+1234567890">`
   - `<a href="callto:1234567890">`
   - Action: Extract and keep

2. **Structured Data**
   - JSON-LD with `@type: "LocalBusiness"` or `"Organization"`
   - Schema.org microdata with `itemprop="telephone"`
   - Action: Extract and keep

3. **Footer Sections**
   - `<footer>` tag content
   - Elements with class/id containing: footer, site-footer, page-footer
   - Within 100 characters of keywords: "contact", "call", "phone", "reach us"
   - Action: Extract and keep

4. **Contact Pages**
   - URL contains: /contact, /contact-us, /get-in-touch, /reach-us
   - Page title contains: "Contact", "Get in Touch"
   - Action: Extract and keep

5. **About Pages**
   - URL contains: /about, /about-us, /who-we-are
   - Within contact information sections
   - Action: Extract and keep

### 2.2 Medium-Confidence Sources (EVALUATE)
**Confidence Score: 0.5-0.8**

1. **Visible HTML Text**
   - Found in `<p>`, `<div>`, `<span>` tags
   - NOT inside `<script>` or `<style>`
   - Visible to user (not display:none or hidden)
   - Action: Apply additional filters

2. **Header Sections**
   - `<header>` tag content
   - Top navigation areas
   - Action: Apply context analysis

3. **Sidebar Content**
   - Widget areas
   - Contact widgets
   - Action: Check for contact keywords

### 2.3 Low-Confidence Sources (REMOVE)
**Confidence Score: 0.0-0.4**

1. **JavaScript Files**
   - Inside `<script>` tags
   - External .js files
   - Minified bundles (.min.js)
   - Action: Remove unless also found in high-confidence location

2. **CDN Resources**
   - URLs containing: cdn.shopify.com, cdn.woocommerce.com, wp-content/themes
   - Third-party script domains
   - Action: Remove

3. **Checkout/Cart Scripts**
   - URLs containing: checkout, cart, payment, stripe, paypal
   - E-commerce platform scripts
   - Action: Remove

4. **Theme Assets**
   - URLs containing: /themes/, /assets/, /static/
   - Template files
   - Action: Remove

5. **Analytics/Tracking**
   - Google Analytics, Facebook Pixel, etc.
   - Tracking script content
   - Action: Remove

6. **CSS Files**
   - Inside `<style>` tags or .css files
   - Action: Remove

7. **Comments**
   - HTML comments `<!-- -->`
   - JavaScript comments `//` or `/* */`
   - Action: Remove

---

## 3. CONTEXT-BASED FILTERING

### 3.1 Proximity Analysis
**Rule:** Analyze text within ±150 characters of phone number

**Keep IF nearby keywords include:**
- Contact: "contact us", "call us", "reach us", "get in touch"
- Support: "customer service", "support", "help desk"
- Business: "office", "headquarters", "location"
- Action: "phone", "telephone", "call", "dial"

**Remove IF nearby keywords include:**
- Platform: "shopify", "woocommerce", "wordpress", "powered by"
- Demo: "example", "demo", "sample", "placeholder"
- Code: "function", "var", "const", "return", "script"
- Error: "error", "404", "not found"

### 3.2 HTML Structure Analysis

**Keep IF:**
- Inside `<address>` tag
- Inside element with class/id: contact-info, phone-number, business-phone
- Part of vCard/hCard microformat
- Inside `<dl>` (definition list) with "phone" label

**Remove IF:**
- Inside `<code>` or `<pre>` tags
- Inside form validation messages
- Inside error messages
- Inside placeholder attributes

---

## 4. REGION-BASED LOGIC

### 4.1 Business Location Detection
**Methods to determine business location:**

1. **Structured Data**
   - JSON-LD `address.addressCountry`
   - Schema.org `addressCountry`

2. **Domain TLD**
   - .uk, .ca, .au, .de, etc.

3. **Address Text**
   - Parse extracted addresses for country
   - Look for country names in footer

4. **Language**
   - HTML lang attribute
   - Content language

### 4.2 Regional Filtering Rules

**IF Business is US-based:**
- Keep all +1 numbers from high-confidence sources
- Keep toll-free numbers from contact areas
- Remove +1 numbers from scripts/assets

**IF Business is non-US:**
- Remove ALL +1 numbers UNLESS:
  - Found in high-confidence location (tel: link, schema, footer)
  - Found on contact page with "US office" or "North America" keywords
  - Multiple occurrences suggesting real US presence
- Prioritize local country code numbers

**IF Business location unknown:**
- Keep numbers from high-confidence sources only
- Apply stricter filtering
- Prefer numbers matching domain TLD region

---

## 5. DUPLICATE NORMALIZATION

### 5.1 Normalization Process
**Step 1: Strip all formatting**
- Remove: spaces, dashes, parentheses, dots, plus signs
- Keep: digits only

**Step 2: Handle country codes**
- If starts with "1" and is 11 digits → US number, keep "1"
- If starts with other country code → keep it
- If 10 digits → assume US, prepend "1"

**Step 3: Create canonical form**
- Format: +[country][area][number]
- Example: +18882462598

**Step 4: Deduplication**
- Compare canonical forms
- Keep only one instance per canonical form
- Prefer instance from highest confidence source

### 5.2 Variant Detection
**Treat as duplicates:**
- (888) 246-2598
- 888-246-2598
- 888.246.2598
- +1 888 246 2598
- 18882462598
- +18882462598

**Action:** Keep single instance with highest confidence score

---

## 6. CONFIDENCE SCORING SYSTEM

### 6.1 Scoring Matrix

**Base Scores by Source:**
- `<a href="tel:">`: 1.0
- JSON-LD/Schema.org: 0.95
- Footer with contact keywords: 0.9
- Contact page: 0.85
- About page: 0.8
- Visible HTML with context: 0.6
- Header: 0.5
- Sidebar: 0.4
- JavaScript: 0.1
- CDN/Assets: 0.05

**Modifiers (add/subtract):**

**Add points (+):**
- Multiple occurrences in different high-confidence locations: +0.1
- Near contact keywords: +0.1
- In structured format (parentheses, dashes): +0.05
- Matches business region: +0.1
- Not toll-free: +0.05

**Subtract points (-):**
- In JavaScript: -0.5
- In CDN URL: -0.6
- Toll-free without context: -0.2
- In blacklist: -1.0 (instant removal)
- Near platform keywords: -0.3
- In checkout/cart: -0.4

### 6.2 Threshold Rules

**Keep IF:**
- Final score ≥ 0.7 (High confidence)
- Final score ≥ 0.5 AND found in multiple locations (Medium-high)

**Review IF:**
- Final score 0.4-0.6 (Medium - apply additional filters)

**Remove IF:**
- Final score < 0.4 (Low confidence)
- In blacklist (regardless of score)
- Only found in scripts/assets

---

## 7. STEP-BY-STEP CLEANING WORKFLOW

### Phase 1: EXTRACTION
1. Extract all phone numbers from HTML
2. Record source location for each (HTML element, URL, context)
3. Record surrounding text (±150 chars)
4. Store raw format and position

### Phase 2: BLACKLIST FILTERING
1. Normalize each number to canonical form
2. Check against known dummy number blacklist
3. Remove exact matches immediately
4. Log removed numbers for audit

### Phase 3: SOURCE CLASSIFICATION
1. Classify each number's source location:
   - High-confidence (tel:, schema, footer, contact page)
   - Medium-confidence (visible HTML)
   - Low-confidence (scripts, assets, CDN)
2. Assign base confidence score

### Phase 4: CONTEXT ANALYSIS
1. Analyze surrounding text for each number
2. Check for contact keywords (positive)
3. Check for platform keywords (negative)
4. Check HTML structure (address tag, contact div, etc.)
5. Adjust confidence score based on context

### Phase 5: TOLL-FREE EVALUATION
1. Identify toll-free numbers (800, 844, 855, 866, 877, 888, 833)
2. Check if found in high-confidence location
3. Check business region
4. Apply toll-free filtering rules
5. Remove or keep based on criteria

### Phase 6: REGION FILTERING
1. Detect business location (domain, address, structured data)
2. For non-US businesses:
   - Remove +1 numbers from low/medium confidence sources
   - Keep +1 only from high-confidence or with "US office" context
3. Prioritize numbers matching business region

### Phase 7: DUPLICATE NORMALIZATION
1. Normalize all remaining numbers to canonical form
2. Group duplicates
3. For each group:
   - Keep instance with highest confidence score
   - Keep instance from best source location
   - Discard others

### Phase 8: FINAL SCORING
1. Calculate final confidence score for each unique number
2. Apply all modifiers (multiple occurrences, context, region match)
3. Sort by confidence score

### Phase 9: THRESHOLD FILTERING
1. Keep numbers with score ≥ 0.7
2. Keep numbers with score ≥ 0.5 AND multiple occurrences
3. Remove all others

### Phase 10: QUALITY ASSURANCE
1. Verify at least one number remains (if none, relax threshold to 0.4)
2. Check for obvious patterns (all toll-free, all same prefix)
3. Flag suspicious results for manual review
4. Return cleaned list with confidence scores

---

## 8. SPECIAL CASES & EDGE CASES

### 8.1 International Numbers
**Rule:** Keep international numbers from high-confidence sources
- Don't apply US-specific rules
- Validate format for country
- Higher confidence if matches business region

### 8.2 Extensions
**Rule:** Strip extensions but keep base number
- Remove: "ext", "x", "#" followed by digits
- Keep base number for deduplication
- Store extension separately if needed

### 8.3 Multiple Business Locations
**Rule:** Keep numbers from different regions if in high-confidence sources
- US office: +1 number
- UK office: +44 number
- Both valid if in contact section

### 8.4 No Numbers Found After Filtering
**Fallback Strategy:**
1. Relax threshold to 0.4
2. Include medium-confidence sources
3. Keep toll-free if only option
4. Flag result as "low confidence"

### 8.5 All Numbers Are Toll-Free
**Rule:** Likely legitimate if:
- Multiple different toll-free numbers
- All in high-confidence locations
- Business is US-based
- Keep all

---

## 9. LOGGING & AUDIT TRAIL

### 9.1 Track for Each Number
- Original format
- Canonical format
- Source location (HTML path, URL)
- Surrounding context
- Initial confidence score
- Applied modifiers
- Final confidence score
- Keep/Remove decision
- Reason for removal (if removed)

### 9.2 Summary Metrics
- Total numbers extracted
- Numbers removed by blacklist
- Numbers removed by source (scripts, CDN, etc.)
- Numbers removed by toll-free rules
- Numbers removed by region rules
- Numbers removed by duplicates
- Final numbers kept
- Average confidence score

---

## 10. IMPLEMENTATION PRIORITY

### Phase 1 (Critical):
1. Blacklist filtering
2. Source classification (high/medium/low)
3. Basic confidence scoring
4. Threshold filtering (≥0.7)

### Phase 2 (Important):
1. Context analysis (keywords)
2. Toll-free filtering
3. Duplicate normalization
4. Region-based filtering

### Phase 3 (Enhancement):
1. Advanced scoring modifiers
2. Multiple occurrence bonus
3. HTML structure analysis
4. Quality assurance checks

---

## 11. SUCCESS METRICS

**Target Accuracy:**
- Precision: >95% (kept numbers are real business numbers)
- Recall: >90% (real business numbers are kept)
- False Positive Rate: <5% (junk numbers kept)
- False Negative Rate: <10% (real numbers removed)

**Performance:**
- Processing time: <100ms per URL
- Memory efficient: <10MB per 1000 numbers

**Quality Indicators:**
- Average confidence score: >0.8
- Percentage high-confidence: >70%
- Blacklist hit rate: <5% (most junk caught by other rules)

---

## END OF ARCHITECTURE DOCUMENT
