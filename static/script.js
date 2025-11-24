// Logging system
let logs = [];
let logsExpanded = true;

function addLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    logs.push({ message, type, timestamp });
    
    const logsList = document.getElementById('logsList');
    if (!logsList) return; // Skip if logs not available
    
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-message">${message}</span>
    `;
    logsList.appendChild(logEntry);
    logsList.scrollTop = logsList.scrollHeight;
}

function toggleLogs() {
    const logsList = document.getElementById('logsList');
    const logsToggle = document.getElementById('logsToggle');
    
    logsExpanded = !logsExpanded;
    
    if (logsExpanded) {
        logsList.classList.remove('logs-collapsed');
        logsList.classList.add('logs-expanded');
        logsToggle.textContent = '▼';
    } else {
        logsList.classList.remove('logs-expanded');
        logsList.classList.add('logs-collapsed');
        logsToggle.textContent = '▶';
    }
}

function clearLogs(event) {
    event.stopPropagation();
    logs = [];
    document.getElementById('logsList').innerHTML = '';
}

function collapseLogs() {
    const logsList = document.getElementById('logsList');
    const logsToggle = document.getElementById('logsToggle');
    
    logsExpanded = false;
    logsList.classList.remove('logs-expanded');
    logsList.classList.add('logs-collapsed');
    logsToggle.textContent = '▶';
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

// Tab switching
document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // Remove active from all
        document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active to clicked
        btn.classList.add('active');
        document.getElementById(tab).classList.add('active');
    });
});

// Scrape single URL
async function scrapeSingle() {
    const url = document.getElementById('singleUrl').value.trim();
    const blockKeywords = document.getElementById('blockKeywords').value;
    
    if (!url) {
        alert('Please enter a URL');
        return;
    }
    
    // Clear logs without event
    logs = [];
    const logsList = document.getElementById('logsList');
    if (logsList) {
        logsList.innerHTML = '';
    }
    
    addLog(`Starting scrape for ${url}`, 'info');
    updateProgress(10, 'Initializing...');
    
    // Find the button that was clicked
    const btn = document.querySelector('#single .btn-primary');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    btn.disabled = true;
    
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
            collapseLogs(); // Collapse logs after results load
        }, 1500);
        
    } catch (error) {
        console.error('Scrape error:', error);
        addLog('Error: ' + error.message, 'error');
        alert('Error: ' + error.message);
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        btn.disabled = false;
    }
}

// Display single results
function displaySingleResults(data) {
    const resultsDiv = document.getElementById('singleResults');
    const content = document.getElementById('resultsContent');
    
    let html = `
        <div class="result-item">
            <h4>${data.url}</h4>
            
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
    
    // Additional info
    html += `
            <div class="result-field">
                <span class="result-label">Pages Scanned:</span>
                <span class="result-value">${data.pages_scanned}</span>
            </div>
            
            <div class="result-field">
                <span class="result-label">Leadership Mentions:</span>
                <span class="result-value">${data.leadership_count}</span>
            </div>
            
            <div class="result-field">
                <span class="result-label">Fetch Mode:</span>
                <span class="result-value">${data.fetch_mode}</span>
            </div>
            
            <div class="result-field">
                <span class="result-label">Scrape Mode:</span>
                <span class="result-value">${data.scrape_mode}</span>
            </div>
            
            <div class="result-field">
                <span class="result-label">Retries:</span>
                <span class="result-value">${data.retry_count}</span>
            </div>
            
            <div class="result-field">
                <span class="result-label">SSL Valid:</span>
                <span class="result-value">${data.ssl_valid ? '✅ Yes' : '❌ No'}</span>
            </div>
            
            ${data.bot_protection ? `
            <div class="result-field">
                <span class="result-label">Bot Protection:</span>
                <span class="result-value">${data.bot_protection}</span>
            </div>
            ` : ''}
            
            ${data.social_links && data.social_links !== '{}' ? `
            <div class="result-field">
                <span class="result-label">Social Links:</span>
                <div class="result-value">
                    ${(() => {
                        try {
                            const links = typeof data.social_links === 'string' ? JSON.parse(data.social_links) : data.social_links;
                            let html = '';
                            for (const [platform, urls] of Object.entries(links)) {
                                if (Array.isArray(urls) && urls.length > 0) {
                                    html += `<div><strong>${platform}:</strong> ${urls.map(url => `<a href="${url}" target="_blank">${url}</a>`).join(', ')}</div>`;
                                }
                            }
                            return html || 'No social links found';
                        } catch (e) {
                            return data.social_links;
                        }
                    })()}
                </div>
            </div>
            ` : ''}
            
            <!-- Data Quality Breakdown -->
            <div class="result-field">
                <span class="result-label">Data Quality:</span>
                <div style="margin-top: 8px;">
                    <div style="font-size: 0.9em; color: var(--text-secondary); margin-bottom: 5px;">
                        ${data.emails.length > 0 ? '✅ Emails found' : '❌ No emails'}
                        ${data.phones.length > 0 ? ' • ✅ Phones found' : ' • ❌ No phones'}
                        ${data.pages_scanned > 1 ? ' • ✅ Multiple pages' : ' • ⚠️ Single page'}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    content.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    // Store for download
    window.lastResults = [data];
}

// Scrape batch URLs
async function scrapeBatch() {
    const urlsText = document.getElementById('batchUrls').value.trim();
    const blockKeywords = document.getElementById('batchBlockKeywords').value;
    
    if (!urlsText) {
        alert('Please enter URLs');
        return;
    }
    
    const urls = urlsText.split('\n').map(u => u.trim()).filter(u => u);
    
    if (urls.length === 0) {
        alert('Please enter at least one URL');
        return;
    }
    
    // Find the button
    const btn = document.querySelector('#batch .btn-primary');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    btn.disabled = true;
    
    // Show progress
    const progressContainer = document.getElementById('batchProgressContainer');
    progressContainer.style.display = 'block';
    
    try {
        const results = [];
        
        // Scrape each URL individually to show progress
        for (let i = 0; i < urls.length; i++) {
            const url = urls[i];
            const percent = Math.round((i / urls.length) * 100);
            
            document.getElementById('batchProgressText').textContent = `Scraping ${i + 1} of ${urls.length}...`;
            document.getElementById('batchProgressPercent').textContent = percent + '%';
            document.getElementById('batchProgressFill').style.width = percent + '%';
            
            try {
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url, block_keywords: blockKeywords })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    results.push(data);
                } else {
                    const errorData = await response.json();
                    results.push({
                        url: url,
                        status: 'failed',
                        reason: errorData.error || 'Unknown error',
                        emails: [],
                        phones: [],
                        confidence_score: 0
                    });
                }
            } catch (error) {
                results.push({
                    url: url,
                    status: 'failed',
                    reason: error.message,
                    emails: [],
                    phones: [],
                    confidence_score: 0
                });
            }
        }
        
        // Complete
        document.getElementById('batchProgressText').textContent = 'Complete!';
        document.getElementById('batchProgressPercent').textContent = '100%';
        document.getElementById('batchProgressFill').style.width = '100%';
        
        displayBatchResults(results);
        window.lastResults = results;
        
        setTimeout(() => {
            progressContainer.style.display = 'none';
        }, 1500);
        
    } catch (error) {
        console.error('Batch scrape error:', error);
        alert('Error: ' + error.message);
    } finally {
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        btn.disabled = false;
    }
}

// Display batch results
function displayBatchResults(results) {
    const resultsDiv = document.getElementById('batchResults');
    const content = document.getElementById('batchResultsContent');
    
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
                </tr>
            </thead>
            <tbody>
    `;
    
    results.forEach((result, idx) => {
        const company = result.company_name ? result.company_name.substring(0, 20) : '-';
        html += `
            <tr class="result-row status-${result.status}">
                <td>${idx + 1}</td>
                <td><a href="${result.url}" target="_blank" title="${result.url}">${result.url.substring(0, 35)}...</a></td>
                <td><span class="status-badge status-${result.status === 'success' ? 'success' : 'warning'}">${result.status}</span></td>
                <td>${result.emails ? result.emails.length : 0}</td>
                <td>${result.phones ? result.phones.length : 0}</td>
                <td>${company}</td>
                <td>${((result.confidence_score || 0) * 100).toFixed(0)}%</td>
            </tr>
        `;
    });
    
    html += `</tbody></table>`;
    
    content.innerHTML = html;
    resultsDiv.style.display = 'block';
}

// Download batch results
async function downloadBatchResults() {
    if (!window.lastResults || window.lastResults.length === 0) {
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
        a.download = `bulk_results_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        alert('Error downloading: ' + error.message);
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

// Add results table styling
const style = document.createElement('style');
style.textContent = `
    .results-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 15px;
    }
    
    .results-table th,
    .results-table td {
        padding: 12px;
        text-align: left;
        border-bottom: 1px solid var(--border);
    }
    
    .results-table th {
        background: var(--bg);
        font-weight: 600;
        color: var(--primary);
    }
    
    .results-table tr:hover {
        background: var(--bg);
    }
    
    .results-table a {
        color: var(--primary);
        text-decoration: none;
    }
    
    .results-table a:hover {
        text-decoration: underline;
    }
`;
document.head.appendChild(style);
