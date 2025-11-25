// Logging system
let logs = [];

function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    logs.push({ message, type, timestamp });
}

function updateProgress(percent, message) {
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    const progressPercent = document.getElementById('progressPercent');
    
    progressContainer.style.display = 'block';
    progressFill.style.width = percent + '%';
    progressText.textContent = message;
    progressPercent.textContent = percent + '%';
}

function addLiveLog(log) {
    const logsList = document.getElementById('liveLogsList');
    if (!logsList) return;
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${log.type || 'info'}`;
    logEntry.innerHTML = `
        <span class="log-time">${log.time}</span>
        <span class="log-message">${log.message}</span>
    `;
    logsList.appendChild(logEntry);
    logsList.scrollTop = logsList.scrollHeight;
}

function clearLiveLogs() {
    const logsList = document.getElementById('liveLogsList');
    if (logsList) {
        logsList.innerHTML = '';
    }
}

// Unified scraping function
async function scrapeUrls() {
    const urlInput = document.getElementById('urlInput').value.trim();
    const blockKeywords = document.getElementById('blockKeywords').value;
    
    if (!urlInput) {
        alert('Please enter at least one URL');
        return;
    }
    
    // Parse URLs (split by newlines)
    const urls = urlInput.split('\n').map(u => u.trim()).filter(u => u);
    
    if (urls.length === 0) {
        alert('Please enter at least one valid URL');
        return;
    }
    
    // Clear previous results
    document.getElementById('results').style.display = 'none';
    clearLiveLogs();
    logs = [];
    
    // Find the button
    const btn = document.querySelector('.btn-primary');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    btn.disabled = true;
    
    try {
        if (urls.length === 1) {
            // Single URL - use single scrape endpoint
            await scrapeSingleUrl(urls[0], blockKeywords);
        } else {
            // Multiple URLs - use batch endpoint
            await scrapeBatchUrls(urls, blockKeywords);
        }
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        btn.disabled = false;
    }
}

// Scrape single URL
async function scrapeSingleUrl(url, blockKeywords) {
    addLog(`Starting scrape for ${url}`, 'info');
    updateProgress(10, 'Initializing...');
    
    try {
        updateProgress(20, 'Sending request...');
        addLog('Connecting to scraper...', 'info');
        
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, block_keywords: blockKeywords }),
            timeout: 120000
        });
        
        updateProgress(50, 'Processing results...');
        
        if (!response.ok) {
            const errorData = await response.json();
            addLog('Error: ' + (errorData.error || response.statusText), 'error');
            alert('Error: ' + (errorData.error || response.statusText));
            return;
        }
        
        const data = await response.json();
        
        // Display logs from backend
        if (data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                addLiveLog(log);
                addLog(log.message, log.type);
            });
        }
        
        addLog(`Found ${data.emails.length} emails`, 'success');
        addLog(`Found ${data.phones.length} phones`, 'success');
        addLog(`Scanned ${data.pages_scanned} pages`, 'info');
        
        if (data.social_links && data.social_links !== '{}') {
            addLog('Found social media links', 'success');
        }
        
        updateProgress(80, 'Displaying results...');
        displaySingleResults(data);
        
        updateProgress(100, 'Complete!');
        addLog('Scrape completed successfully', 'success');
        
        setTimeout(() => {
            document.getElementById('progressContainer').style.display = 'none';
        }, 1500);
        
    } catch (error) {
        console.error('Scrape error:', error);
        addLog('Error: ' + error.message, 'error');
        alert('Error: ' + error.message);
    }
}

// Scrape batch URLs
async function scrapeBatchUrls(urls, blockKeywords) {
    updateProgress(0, 'Starting batch scrape...');
    
    try {
        const results = [];
        const batchSize = 5; // Scrape 5 URLs in parallel
        
        // Process URLs in batches for speed
        for (let i = 0; i < urls.length; i += batchSize) {
            const batch = urls.slice(i, i + batchSize);
            const percent = Math.round((i / urls.length) * 100);
            
            updateProgress(percent, `Scraping batch ${Math.floor(i / batchSize) + 1}...`);
            addLiveLog({time: new Date().toLocaleTimeString(), message: `🚀 Scraping ${batch.length} URLs in parallel...`, type: 'info'});
            
            // Scrape all URLs in this batch in parallel
            const batchPromises = batch.map(async (url) => {
                try {
                    const response = await fetch('/api/scrape', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url, block_keywords: blockKeywords })
                    });
                
                    if (response.ok) {
                        const data = await response.json();
                        
                        // Ensure all fields exist
                        return {
                            url: data.url || url,
                            status: data.status || 'success',
                            emails: data.emails || [],
                            phones: data.phones || [],
                            confidence_score: data.confidence_score || 0,
                            company_name: data.company_name || null,
                            company_description: data.company_description || null,
                            addresses: data.addresses || [],
                            social_links: data.social_links || {},
                            pages_scanned: data.pages_scanned || 1
                        };
                    } else {
                        const errorData = await response.json();
                        return {
                            url: url,
                            status: 'failed',
                            reason: errorData.error || 'Unknown error',
                            emails: [],
                            phones: [],
                            confidence_score: 0,
                            company_name: null,
                            company_description: null,
                            addresses: [],
                            social_links: {},
                            pages_scanned: 0
                        };
                    }
                } catch (error) {
                    return {
                        url: url,
                        status: 'failed',
                        reason: error.message,
                        emails: [],
                        phones: [],
                        confidence_score: 0,
                        company_name: null,
                        company_description: null,
                        addresses: [],
                        social_links: {},
                        pages_scanned: 0
                    };
                }
            });
            
            // Wait for all URLs in this batch to complete
            const batchResults = await Promise.all(batchPromises);
            results.push(...batchResults);
            
            // Log results for this batch
            batchResults.forEach(result => {
                if (result.status === 'success') {
                    addLiveLog({time: new Date().toLocaleTimeString(), message: `✓ ${result.url} - ${result.emails.length} emails, ${result.phones.length} phones`, type: 'success'});
                } else {
                    addLiveLog({time: new Date().toLocaleTimeString(), message: `✗ ${result.url} - Failed`, type: 'error'});
                }
            });
        }
        
        // Complete
        updateProgress(100, 'Complete!');
        addLiveLog({time: new Date().toLocaleTimeString(), message: `✅ Batch scraping complete - ${results.length} URLs processed`, type: 'success'});
        
        displayBatchResults(results);
        window.lastResults = results;
        
        setTimeout(() => {
            document.getElementById('progressContainer').style.display = 'none';
        }, 1500);
        
    } catch (error) {
        console.error('Batch scrape error:', error);
        alert('Error: ' + error.message);
    }
}

// Display single results
function displaySingleResults(data) {
    const resultsDiv = document.getElementById('results');
    const content = document.getElementById('resultsContent');
    
    let html = `
        <div class="result-item">
            <h4><a href="${data.url}" target="_blank" class="result-url">${data.url}</a></h4>
            
            ${data.company_name ? `
            <div class="result-field">
                <span class="result-label">Company:</span>
                <span class="result-value">${data.company_name}</span>
            </div>
            ` : ''}
            
            ${data.company_description ? `
            <div class="result-field">
                <span class="result-label">Description:</span>
                <span class="result-value">${data.company_description}</span>
            </div>
            ` : ''}
            
            ${data.addresses && data.addresses.length > 0 ? `
            <div class="result-field">
                <span class="result-label">Addresses:</span>
                <span class="result-value">
                    ${[...new Set(data.addresses)].map(addr => `<div>${addr}</div>`).join('')}
                </span>
            </div>
            ` : ''}

            <div class="result-field">
                <span class="result-label">Status:</span>
                <span class="result-value">
                    <span class="status-badge status-${data.status === 'success' ? 'success' : 'warning'}">
                        ${data.status.toUpperCase()}
                    </span>
                </span>
            </div>
            
            <div class="result-field">
                <span class="result-label">Confidence:</span>
                <span class="result-value">
                    ${(data.confidence_score * 100).toFixed(0)}%
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${data.confidence_score * 100}%"></div>
                    </div>
                </span>
            </div>
    `;
    
    if (data.emails && data.emails.length > 0) {
        html += `
            <div class="result-field">
                <span class="result-label">Emails (${data.emails.length}):</span>
                <div class="email-list">
        `;
        
        data.emails.forEach(email => {
            const type = data.email_categories && data.email_categories.personal && data.email_categories.personal.includes(email) ? 'personal' : 'role';
            html += `<span class="email-tag ${type}">${email}</span>`;
        });
        
        html += `</div></div>`;
    } else {
        html += `<div class="result-field"><span class="result-label">Emails:</span><span class="result-value">None found</span></div>`;
    }
    
    if (data.phones && data.phones.length > 0) {
        html += `
            <div class="result-field">
                <span class="result-label">Phones (${data.phones.length}):</span>
                <div class="phone-list">
        `;
        
        data.phones.forEach(phone => {
            html += `<span class="phone-tag">${phone}</span>`;
        });
        
        html += `</div></div>`;
    } else {
        html += `<div class="result-field"><span class="result-label">Phones:</span><span class="result-value">None found</span></div>`;
    }
    
    html += `</div>`;
    
    content.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    // Store for download
    window.lastResults = [data];
}

// Store full descriptions globally
window.fullDescriptions = {};

// Display batch results
function displayBatchResults(results) {
    const resultsDiv = document.getElementById('results');
    const content = document.getElementById('resultsContent');
    
    if (!results || results.length === 0) {
        content.innerHTML = '<p>No results found</p>';
        resultsDiv.style.display = 'block';
        return;
    }
    
    // Clear previous descriptions
    window.fullDescriptions = {};
    
    let html = `
        <div class="batch-summary">
            <div class="summary-stat">
                <span class="summary-label">Total URLs:</span>
                <span class="summary-value">${results.length}</span>
            </div>
            <div class="summary-stat">
                <span class="summary-label">Successful:</span>
                <span class="summary-value">${results.filter(r => r.status === 'success').length}</span>
            </div>
            <div class="summary-stat">
                <span class="summary-label">Total Emails:</span>
                <span class="summary-value">${results.reduce((sum, r) => sum + (r.emails ? r.emails.length : 0), 0)}</span>
            </div>
            <div class="summary-stat">
                <span class="summary-label">Total Phones:</span>
                <span class="summary-value">${results.reduce((sum, r) => sum + (r.phones ? r.phones.length : 0), 0)}</span>
            </div>
        </div>
        
        <table class="results-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Emails</th>
                    <th>Phones</th>
                    <th>Company</th>
                    <th>Confidence</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    results.forEach((result, idx) => {
        const company = result.company_name ? result.company_name.substring(0, 30) : '-';
        const rowId = `row-${idx}`;
        const detailsId = `details-${idx}`;
        
        // Main row
        html += `
            <tr class="result-row status-${result.status}" id="${rowId}">
                <td>${idx + 1}</td>
                <td><a href="${result.url}" target="_blank" title="${result.url}">${result.url.substring(0, 40)}...</a></td>
                <td><span class="status-badge status-${result.status === 'success' ? 'success' : 'warning'}">${result.status}</span></td>
                <td>${result.emails ? result.emails.length : 0}</td>
                <td>${result.phones ? result.phones.length : 0}</td>
                <td title="${result.company_name || '-'}">${company}</td>
                <td>${((result.confidence_score || 0) * 100).toFixed(0)}%</td>
                <td><button class="btn-details" onclick="toggleDetails('${detailsId}', '${rowId}')">View</button></td>
            </tr>
        `;
        
        // Details row (hidden by default)
        html += `
            <tr class="details-row" id="${detailsId}" style="display: none;">
                <td colspan="8">
                    <div class="details-content">
                        <div class="details-grid">
                            <!-- Emails -->
                            <div class="details-section">
                                <h4>📧 Emails (${result.emails ? result.emails.length : 0})</h4>
                                ${result.emails && result.emails.length > 0 ? 
                                    `<div class="email-list">${result.emails.map(e => `<span class="email-tag">${e}</span>`).join('')}</div>` : 
                                    '<p class="no-data">No emails found</p>'}
                            </div>
                            
                            <!-- Phones -->
                            <div class="details-section">
                                <h4>📞 Phones (${result.phones ? result.phones.length : 0})</h4>
                                ${result.phones && result.phones.length > 0 ? 
                                    `<div class="phone-list">${result.phones.map(p => `<span class="phone-tag">${p}</span>`).join('')}</div>` : 
                                    '<p class="no-data">No phones found</p>'}
                            </div>
                            
                            <!-- Company Info -->
                            <div class="details-section">
                                <h4>🏢 Company</h4>
                                <p><strong>Name:</strong> ${result.company_name || 'Not found'}</p>
                                ${result.company_description ? `<p><strong>Description:</strong> ${result.company_description.substring(0, 200)}${result.company_description.length > 200 ? '...' : ''}</p>` : ''}
                            </div>
                            
                            <!-- Addresses -->
                            <div class="details-section">
                                <h4>📍 Addresses</h4>
                                ${result.addresses && result.addresses.length > 0 ? 
                                    result.addresses.map(a => `<p class="address-text">${a}</p>`).join('') : 
                                    '<p class="no-data">No addresses found</p>'}
                            </div>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    });
    
    html += `</tbody></table>`;
    
    content.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Toggle details row
function toggleDetails(detailsId, rowId) {
    const detailsRow = document.getElementById(detailsId);
    const mainRow = document.getElementById(rowId);
    const btn = mainRow.querySelector('.btn-details');
    
    if (detailsRow.style.display === 'none' || !detailsRow.style.display) {
        detailsRow.style.display = 'table-row';
        btn.textContent = 'Hide';
        btn.classList.add('active');
    } else {
        detailsRow.style.display = 'none';
        btn.textContent = 'View';
        btn.classList.remove('active');
    }
}

// Download results
async function downloadResults() {
    if (!window.lastResults) {
        alert('No results to download');
        return;
    }
    
    try {
        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ results: window.lastResults })
        });
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scraper_results_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert('Error downloading: ' + error.message);
    }
}
