// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // Remove active from all
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
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
    
    const btn = event.target.closest('.btn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, block_keywords: blockKeywords })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert('Error: ' + data.error);
            return;
        }
        
        displaySingleResults(data);
    } catch (error) {
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
                    ${data.confidence_score * 100}%
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
    
    html += `
            <div class="result-field">
                <span class="result-label">Pages Scanned:</span>
                <span class="result-value">${data.pages_scanned}</span>
            </div>
            
            <div class="result-field">
                <span class="result-label">Fetch Mode:</span>
                <span class="result-value">${data.fetch_mode}</span>
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
    
    if (!urlsText) {
        alert('Please enter URLs');
        return;
    }
    
    const urls = urlsText.split('\n').map(u => u.trim()).filter(u => u);
    
    const btn = event.target.closest('.btn');
    const btnText = btn.querySelector('.btn-text');
    const btnLoader = btn.querySelector('.btn-loader');
    
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ urls })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            alert('Error: ' + data.error);
            return;
        }
        
        displayBatchResults(data.results);
    } catch (error) {
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
    
    let html = `<table class="results-table">
        <thead>
            <tr>
                <th>URL</th>
                <th>Status</th>
                <th>Emails</th>
                <th>Phones</th>
                <th>Confidence</th>
            </tr>
        </thead>
        <tbody>
    `;
    
    results.forEach(result => {
        html += `
            <tr>
                <td><a href="${result.url}" target="_blank">${result.url.substring(0, 40)}...</a></td>
                <td><span class="status-badge status-${result.status === 'success' ? 'success' : 'warning'}">${result.status}</span></td>
                <td>${result.emails.length}</td>
                <td>${result.phones.length}</td>
                <td>${(result.confidence_score * 100).toFixed(0)}%</td>
            </tr>
        `;
    });
    
    html += `</tbody></table>`;
    
    content.innerHTML = html;
    resultsDiv.style.display = 'block';
    
    // Store for download
    window.lastResults = results;
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
