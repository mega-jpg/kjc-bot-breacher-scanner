// Fake Document Generator - JavaScript Functions

function showTab(tabName) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));

    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    const targetContent = document.getElementById(tabName);
    if (targetContent) {
        targetContent.classList.add('active');
    }
}

function showResult(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    if (element) {
        const alertClass = isError ? 'alert-error' : 'alert-success';
        element.innerHTML = '<div class="alert ' + alertClass + '">' + message + '</div>';
    }
}

function showContent(elementId, content) {
    let element = document.getElementById(elementId);
    if (!element) {
        const elementsByClass = document.getElementsByClassName(elementId);
        if (elementsByClass.length > 0) {
            element = elementsByClass[0];
        }
    }
    if (element) {
        element.innerHTML = content;
    } else {
        console.warn('Element with id or class "' + elementId + '" not found.');
    }
}

// Make Docs Function - Generate Fake Passport Documents
async function makeDocs() {
    const docsBtn = document.getElementById('make-docs-btn');
    const originalText = docsBtn ? docsBtn.innerHTML : '';
    const docsCount = document.getElementById('docs-count');
    const count = docsCount ? parseInt(docsCount.value) : 10;

    // Set loading state
    if (docsBtn) {
        docsBtn.classList.add('loading');
        docsBtn.disabled = true;
        docsBtn.innerHTML = '⏳ Generating Documents...';
    }

    try {
        // Call API to generate fake documents
        const response = await fetch('/api/make-docs', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count: count })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Display passport documents
            displayPassportDocs(result.data);
        } else {
            showResult('docs-result', '❌ Error: ' + (result.message || 'Failed to generate documents'), true);
        }
    } catch (error) {
        showResult('docs-result', '❌ Network Error: ' + error.message, true);
    } finally {
        // Reset button state
        if (docsBtn) {
            docsBtn.classList.remove('loading');
            docsBtn.disabled = false;
            docsBtn.innerHTML = originalText;
        }
    }
}

// Display Passport Documents in the specified format
function displayPassportDocs(data) {
    const resultDiv = document.getElementById('docs-result');
    
    if (!data || !data.passports || data.passports.length === 0) {
        resultDiv.innerHTML = '<p>⚠️ No documents generated</p>';
        return;
    }

    let html = '<div style="margin-top: 20px;">';
    html += '<h3>Generated Passport Documents:</h3>';
    html += '<hr>';
    html += '<p><strong>No. | Passport Number | Name | Date of Birth | Address</strong></p>';
    html += '<hr>';
    
    data.passports.forEach(function(passport, index) {
        html += '<p>';
        html += 'Passport ' + (index + 1) + ': ';
        html += passport.passport_number + ' - ';
        html += passport.name + ' - ';
        html += 'DOB: ' + passport.dob + ' - ';
        html += 'Address: ' + passport.address;
        html += '</p>';
    });
    
    html += '<hr>';
    html += '<p style="margin-top: 15px;"><strong>Total: ' + data.passports.length + ' documents</strong></p>';
    html += '</div>';
    
    resultDiv.innerHTML = html;
}

// Generate Utility Bills Function
async function generateUtilityBills() {
    const billsBtn = document.getElementById('generate-bills-btn');
    const billCount = document.getElementById('bill-count')?.value || 10;
    const originalText = billsBtn ? billsBtn.innerHTML : '';

    // Set loading state
    if (billsBtn) {
        billsBtn.classList.add('loading');
        billsBtn.disabled = true;
        billsBtn.innerHTML = '⏳ Generating Bills...';
    }

    try {
        // Call API to generate utility bills
        const response = await fetch('/api/generate-utility-bills', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count: parseInt(billCount) })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Display utility bills
            displayUtilityBills(result.data);
        } else {
            showResult('docs-result', '❌ Error: ' + (result.message || 'Failed to generate utility bills'), true);
        }
    } catch (error) {
        showResult('docs-result', '❌ Network Error: ' + error.message, true);
    } finally {
        // Reset button state
        if (billsBtn) {
            billsBtn.classList.remove('loading');
            billsBtn.disabled = false;
            billsBtn.innerHTML = originalText;
        }
    }
}

// Display Utility Bills
function displayUtilityBills(data) {
    const resultDiv = document.getElementById('docs-result');
    
    if (!data || !data.bills || data.bills.length === 0) {
        resultDiv.innerHTML = '<p>⚠️ No bills generated</p>';
        return;
    }

    let html = '<div style="margin-top: 20px;">';
    html += '<h3>✅ Generated Utility Bills:</h3>';
    html += '<hr>';
    html += '<p><strong>Total Bills Generated: ' + data.count + '</strong></p>';
    html += '<p><strong>Output Folder: ' + data.output_folder + '</strong></p>';
    html += '<hr>';
    
    // Display image gallery
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; margin-top: 20px;">';
    
    data.bills.forEach(function(bill, index) {
        html += '<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">';
        html += '<img src="/static/UtilityBill/' + bill.filename + '" style="width: 100%; height: auto; border-radius: 3px;" alt="Bill ' + (index + 1) + '">';
        html += '<p style="margin: 8px 0 0 0; font-size: 12px;"><strong>' + bill.name + '</strong></p>';
        html += '<p style="margin: 3px 0; font-size: 11px; color: #666;">' + bill.address + '</p>';
        html += '<p style="margin: 3px 0; font-size: 11px;">Amount: <strong style="color: red;">$' + bill.amount.toFixed(2) + '</strong></p>';
        html += '<p style="margin: 3px 0; font-size: 11px;">Date: ' + bill.date + '</p>';
        html += '</div>';
    });
    
    html += '</div>';
    html += '</div>';
    
    resultDiv.innerHTML = html;
}

// Generate Passports Function
async function generatePassports() {
    const passportsBtn = document.getElementById('generate-passports-btn');
    const passportCount = document.getElementById('passport-count')?.value || 10;
    const originalText = passportsBtn ? passportsBtn.innerHTML : '';

    // Set loading state
    if (passportsBtn) {
        passportsBtn.classList.add('loading');
        passportsBtn.disabled = true;
        passportsBtn.innerHTML = '⏳ Generating UK Passports...';
    }

    try {
        // Call API to generate UK passports
        const response = await fetch('/api/generate-passports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count: parseInt(passportCount) })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Display UK passports
            displayUKPassports(result.data);
        } else {
            showResult('docs-result', '❌ Error: ' + (result.message || 'Failed to generate UK passports'), true);
        }
    } catch (error) {
        showResult('docs-result', '❌ Network Error: ' + error.message, true);
    } finally {
        // Reset button state
        if (passportsBtn) {
            passportsBtn.classList.remove('loading');
            passportsBtn.disabled = false;
            passportsBtn.innerHTML = originalText;
        }
    }
}

// Display UK Passports
function displayUKPassports(data) {
    const resultDiv = document.getElementById('docs-result');
    
    if (!data || !data.passports || data.passports.length === 0) {
        resultDiv.innerHTML = '<p>⚠️ No passports generated</p>';
        return;
    }

    let html = '<div style="margin-top: 20px;">';
    html += '<h3>✅ Generated UK Passports:</h3>';
    html += '<hr>';
    html += '<p><strong>Total Passports Generated: ' + data.count + '</strong></p>';
    html += '<p><strong>Output Folder: ' + data.output_folder + '</strong></p>';
    html += '<hr>';
    
    // Display image gallery
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 15px; margin-top: 20px;">';
    
    data.passports.forEach(function(passport, index) {
        html += '<div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #f9f9f9;">';
        html += '<img src="/static/UKPassport/' + passport.filename + '" style="width: 100%; height: auto; border-radius: 3px;" alt="Passport ' + (index + 1) + '">';
        html += '<p style="margin: 8px 0 0 0; font-size: 12px;"><strong>' + passport.name + '</strong></p>';
        html += '<p style="margin: 3px 0; font-size: 11px; color: #666;">Passport No: ' + passport.passport_no + '</p>';
        html += '<p style="margin: 3px 0; font-size: 11px;">DOB: ' + passport.dob + '</p>';
        html += '<p style="margin: 3px 0; font-size: 11px; color: #888;">Layers: Background, Hologram, UV, Photo, MRZ</p>';
        html += '</div>';
    });
    
    html += '</div>';
    html += '</div>';
    
    resultDiv.innerHTML = html;
}

// Generate Credit Cards Function
async function generateCreditCards() {
    const cardsBtn = document.getElementById('generate-cards-btn');
    const cardCount = document.getElementById('card-count')?.value || 10;
    const originalText = cardsBtn ? cardsBtn.innerHTML : '';

    // Set loading state
    if (cardsBtn) {
        cardsBtn.classList.add('loading');
        cardsBtn.disabled = true;
        cardsBtn.innerHTML = '⏳ Generating Cards...';
    }

    try {
        // Call API to generate credit cards
        const response = await fetch('/api/generate-credit-cards', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count: parseInt(cardCount) })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Display credit cards
            displayCreditCards(result.data);
        } else {
            showResult('docs-result', '❌ Error: ' + (result.message || 'Failed to generate credit cards'), true);
        }
    } catch (error) {
        showResult('docs-result', '❌ Network Error: ' + error.message, true);
    } finally {
        // Reset button state
        if (cardsBtn) {
            cardsBtn.classList.remove('loading');
            cardsBtn.disabled = false;
            cardsBtn.innerHTML = originalText;
        }
    }
}

// Generate Credit Reports Function
async function generateCreditReports() {
    const reportsBtn = document.getElementById('generate-reports-btn');
    const reportCount = document.getElementById('card-count')?.value || 10;
    const originalText = reportsBtn ? reportsBtn.innerHTML : '';

    // Set loading state
    if (reportsBtn) {
        reportsBtn.classList.add('loading');
        reportsBtn.disabled = true;
        reportsBtn.innerHTML = '⏳ Generating Reports...';
    }

    try {
        // Call API to generate credit reports
        const response = await fetch('/api/generate-credit-reports', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ count: parseInt(reportCount) })
        });

        const result = await response.json();

        if (response.ok && result.status === 'success') {
            // Display credit reports
            displayCreditReports(result.data);
        } else {
            showResult('docs-result', '❌ Error: ' + (result.message || 'Failed to generate credit reports'), true);
        }
    } catch (error) {
        showResult('docs-result', '❌ Network Error: ' + error.message, true);
    } finally {
        // Reset button state
        if (reportsBtn) {
            reportsBtn.classList.remove('loading');
            reportsBtn.disabled = false;
            reportsBtn.innerHTML = originalText;
        }
    }
}

// Display Credit Cards
function displayCreditCards(data) {
    const resultDiv = document.getElementById('docs-result');
    
    if (!data || !data.cards || data.cards.length === 0) {
        resultDiv.innerHTML = '<p>⚠️ No cards generated</p>';
        return;
    }

    let html = '<div style="margin-top: 20px;">';
    html += '<h3>✅ Generated Credit Cards (BIN 414720):</h3>';
    html += '<hr>';
    html += '<p><strong>Total Cards: ' + data.count + '</strong></p>';
    html += '<p><strong>All cards validated with Luhn algorithm ✓</strong></p>';
    html += '<hr>';
    
    // Display cards in a table
    html += '<div style="overflow-x: auto;">';
    html += '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">';
    html += '<thead><tr style="background: #f3f4f6;">';
    html += '<th style="padding: 10px; border: 1px solid #ddd;">No.</th>';
    html += '<th style="padding: 10px; border: 1px solid #ddd;">Card Number</th>';
    html += '<th style="padding: 10px; border: 1px solid #ddd;">Expiry</th>';
    html += '<th style="padding: 10px; border: 1px solid #ddd;">CVV</th>';
    html += '<th style="padding: 10px; border: 1px solid #ddd;">Full Format</th>';
    html += '</tr></thead><tbody>';
    
    data.cards.forEach(function(card, index) {
        html += '<tr>';
        html += '<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">' + (index + 1) + '</td>';
        html += '<td style="padding: 8px; border: 1px solid #ddd; font-family: monospace;">' + card.card_number + '</td>';
        html += '<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">' + card.expiry + '</td>';
        html += '<td style="padding: 8px; border: 1px solid #ddd; text-align: center;">' + card.cvv + '</td>';
        html += '<td style="padding: 8px; border: 1px solid #ddd; font-family: monospace; font-size: 11px;">' + card.full_format + '</td>';
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    html += '</div>';
    html += '</div>';
    
    resultDiv.innerHTML = html;
}

// Display Credit Reports
function displayCreditReports(data) {
    const resultDiv = document.getElementById('docs-result');
    
    if (!data || !data.reports || data.reports.length === 0) {
        resultDiv.innerHTML = '<p>⚠️ No reports generated</p>';
        return;
    }

    let html = '<div style="margin-top: 20px;">';
    html += '<h3>✅ Generated Credit Reports:</h3>';
    html += '<hr>';
    html += '<p><strong>Total Reports: ' + data.count + '</strong></p>';
    html += '<p><strong>Output Folder: ' + data.output_folder + '</strong></p>';
    html += '<hr>';
    
    // Display reports list
    html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px; margin-top: 20px;">';
    
    data.reports.forEach(function(report, index) {
        html += '<div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: #f9f9f9;">';
        html += '<h4 style="margin: 0 0 10px 0;">📄 ' + report.filename + '</h4>';
        html += '<p style="margin: 5px 0; font-size: 13px;"><strong>Name:</strong> ' + report.name + '</p>';
        html += '<p style="margin: 5px 0; font-size: 13px;"><strong>Score:</strong> <span style="color: green; font-weight: bold;">' + report.credit_score + '</span></p>';
        html += '<p style="margin: 5px 0; font-size: 13px;"><strong>DOB:</strong> ' + report.dob + '</p>';
        html += '<p style="margin: 5px 0; font-size: 13px;"><strong>Address:</strong> ' + report.address + '</p>';
        html += '<a href="/static/CreditReports/' + report.filename + '" target="_blank" style="display: inline-block; margin-top: 10px; padding: 5px 10px; background: #1e3a8a; color: white; text-decoration: none; border-radius: 3px; font-size: 12px;">View PDF</a>';
        html += '</div>';
    });
    
    html += '</div>';
    html += '</div>';
    
    resultDiv.innerHTML = html;
}

// ==== DORK HARVESTER FUNCTIONS ====
let harvestInterval = null;
let harvestStartTime = null;
let isHarvesting = false;

async function startDorkHarvest() {
    const startBtn = document.getElementById('start-harvest-btn');
    const stopBtn = document.getElementById('stop-harvest-btn');
    const statsDiv = document.getElementById('harvest-stats');
    const resultsDiv = document.getElementById('harvest-results');
    
    // Get configuration
    const config = {
        engines: {
            duckduckgo: document.getElementById('engine-duckduckgo')?.checked || false,
            google: document.getElementById('engine-google')?.checked || false,
            bing: document.getElementById('engine-bing')?.checked || false,
            yandex: document.getElementById('engine-yandex')?.checked || false
        },
        dork_count: parseInt(document.getElementById('dork-count')?.value || 50),
        thread_count: parseInt(document.getElementById('thread-count')?.value || 10),
        clear_results: document.getElementById('clear-results')?.checked || false,
        use_proxies: document.getElementById('use-proxies')?.checked || false,
        use_ua_rotation: document.getElementById('use-ua-rotation')?.checked || false
    };
    
    // Validation
    if (!config.engines.duckduckgo && !config.engines.google && !config.engines.bing && !config.engines.yandex) {
        showResult('docs-result', '❌ Please select at least one search engine', true);
        return;
    }
    
    // Set UI state
    startBtn.disabled = true;
    startBtn.innerHTML = '🔄 Harvesting...';
    stopBtn.disabled = false;
    statsDiv.style.display = 'block';
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<p style="color: #00ff00;">🚀 Initializing harvester...</p>';
    isHarvesting = true;
    harvestStartTime = Date.now();
    
    try {
        // Start harvest
        const response = await fetch('/api/dork-harvest/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            document.getElementById('status').innerHTML = '<span style="color: #00ff00;">🟢 Running</span>';
            showResult('docs-result', '✅ Dork harvester started successfully!', false);
            
            // Start polling for updates
            startPollingHarvest();
        } else {
            throw new Error(result.message || 'Failed to start harvester');
        }
    } catch (error) {
        showResult('docs-result', '❌ Error: ' + error.message, true);
        resetHarvestUI();
    }
}

async function stopDorkHarvest() {
    const startBtn = document.getElementById('start-harvest-btn');
    const stopBtn = document.getElementById('stop-harvest-btn');
    
    stopBtn.disabled = true;
    stopBtn.innerHTML = '⏸️ Stopping...';
    isHarvesting = false;
    
    try {
        const response = await fetch('/api/dork-harvest/stop', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const result = await response.json();
        
        if (response.ok) {
            document.getElementById('status').innerHTML = '<span style="color: #ff9500;">🟡 Stopped</span>';
            showResult('docs-result', '✅ Harvester stopped. Total shops: ' + result.total_shops, false);
            clearInterval(harvestInterval);
            resetHarvestUI();
        }
    } catch (error) {
        showResult('docs-result', '❌ Error stopping harvester: ' + error.message, true);
        resetHarvestUI();
    }
}

function startPollingHarvest() {
    // Update stats every 2 seconds
    harvestInterval = setInterval(async () => {
        if (!isHarvesting) {
            clearInterval(harvestInterval);
            return;
        }
        
        try {
            const response = await fetch('/api/dork-harvest/status');
            const data = await response.json();
            
            if (data.status === 'running') {
                // Update stats
                document.getElementById('shops-found').textContent = data.shops_found || 0;
                document.getElementById('active-threads').textContent = data.active_threads || 0;
                document.getElementById('current-engine').textContent = data.current_engine || 'N/A';
                
                // Update runtime
                if (harvestStartTime) {
                    const elapsed = Math.floor((Date.now() - harvestStartTime) / 1000);
                    const hours = Math.floor(elapsed / 3600);
                    const minutes = Math.floor((elapsed % 3600) / 60);
                    const seconds = elapsed % 60;
                    document.getElementById('runtime').textContent = 
                        String(hours).padStart(2, '0') + ':' + 
                        String(minutes).padStart(2, '0') + ':' + 
                        String(seconds).padStart(2, '0');
                }
                
                // Display recent shops
                if (data.recent_shops && data.recent_shops.length > 0) {
                    const resultsDiv = document.getElementById('harvest-results');
                    let html = '';
                    data.recent_shops.forEach(shop => {
                        html = '<p style="color: #00ff00; margin: 2px 0;">[+] ' + shop + '</p>' + html;
                    });
                    resultsDiv.innerHTML = html + resultsDiv.innerHTML;
                    
                    // Keep only last 100 entries
                    const lines = resultsDiv.querySelectorAll('p');
                    if (lines.length > 100) {
                        for (let i = 100; i < lines.length; i++) {
                            lines[i].remove();
                        }
                    }
                }
            } else if (data.status === 'completed') {
                document.getElementById('status').innerHTML = '<span style="color: #00ff00;">✅ Completed</span>';
                isHarvesting = false;
                clearInterval(harvestInterval);
                showResult('docs-result', '✅ Harvesting completed! Total: ' + data.shops_found + ' shops', false);
                resetHarvestUI();
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 2000);
}

function resetHarvestUI() {
    const startBtn = document.getElementById('start-harvest-btn');
    const stopBtn = document.getElementById('stop-harvest-btn');
    
    if (startBtn) {
        startBtn.disabled = false;
        startBtn.innerHTML = '🚀 Start Harvesting';
    }
    
    if (stopBtn) {
        stopBtn.disabled = true;
        stopBtn.innerHTML = '⛔ Stop Harvester';
    }
}
