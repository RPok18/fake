function switchTab(tabName, event) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab content
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // Add active class to selected tab
    event.target.classList.add('active');
    
    // Hide results when switching tabs
    document.getElementById('results').style.display = 'none';
}

function showLoading() {
    document.getElementById('results').innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Analyzing news... Please wait</p>
        </div>
    `;
    document.getElementById('results').style.display = 'block';
}

function showError(message) {
    document.getElementById('results').innerHTML = `
        <div class="error-message">
            <i class="fas fa-exclamation-triangle"></i> ${message}
        </div>
    `;
    document.getElementById('results').style.display = 'block';
}

function analyzeML() {
    const text = document.getElementById('ml-text').value.trim();
    if (!text) {
        showError('Please enter some text to analyze.');
        return;
    }

    showLoading();

    fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            displayMLResults(data);
        }
    })
    .catch(error => {
        showError('An error occurred while analyzing the text.');
        console.error('Error:', error);
    });
}

function verifyOnline() {
    const text = document.getElementById('online-text').value.trim();
    if (!text) {
        showError('Please enter some text to verify.');
        return;
    }

    showLoading();

    fetch('/verify-online', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            displayOnlineResults(data);
        }
    })
    .catch(error => {
        showError('An error occurred while verifying the text.');
        console.error('Error:', error);
    });
}

function comprehensiveAnalysis() {
    const text = document.getElementById('comprehensive-text').value.trim();
    if (!text) {
        showError('Please enter some text to analyze.');
        return;
    }

    showLoading();

    fetch('/verify', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: text })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            displayComprehensiveResults(data);
        }
    })
    .catch(error => {
        showError('An error occurred while analyzing the text.');
        console.error('Error:', error);
    });
}

function fetchLiveNews() {
    showLoading();

    fetch('/live-news')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            displayLiveNewsResults(data);
        }
    })
    .catch(error => {
        showError('An error occurred while fetching live news.');
        console.error('Error:', error);
    });
}

function displayMLResults(data) {
    const resultsDiv = document.getElementById('results');
    const prediction = data.prediction;
    const confidence = (data.confidence * 100).toFixed(1);
    
    resultsDiv.innerHTML = `
        <div class="verdict-card ${prediction === 'fake' ? 'false' : ''}">
            <div class="verdict-title">
                <i class="fas fa-${prediction === 'fake' ? 'times-circle' : 'check-circle'}"></i>
                ${prediction.toUpperCase()}
            </div>
            <div class="verdict-confidence">Confidence: ${confidence}%</div>
            <div class="verdict-score">
                Probability: ${(data.probability_real * 100).toFixed(1)}% Real, 
                ${(data.probability_fake * 100).toFixed(1)}% Fake
            </div>
        </div>
        
        <div class="analysis-grid">
            <div class="analysis-card">
                <div class="analysis-icon">🎯</div>
                <div class="analysis-value">${prediction.toUpperCase()}</div>
                <div class="analysis-label">AI Prediction</div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">📊</div>
                <div class="analysis-value">${confidence}%</div>
                <div class="analysis-label">Confidence</div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">✅</div>
                <div class="analysis-value">${(data.probability_real * 100).toFixed(1)}%</div>
                <div class="analysis-label">Real Probability</div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">❌</div>
                <div class="analysis-value">${(data.probability_fake * 100).toFixed(1)}%</div>
                <div class="analysis-label">Fake Probability</div>
            </div>
        </div>
    `;
    
    resultsDiv.style.display = 'block';
}

function displayOnlineResults(data) {
    const resultsDiv = document.getElementById('results');
    const verdict = data.verdict;
    let verdictClass = '';
    
    if (verdict.verdict === 'TRUE' || verdict.verdict === 'LIKELY TRUE') {
        verdictClass = '';
    } else if (verdict.verdict === 'LIKELY FALSE') {
        verdictClass = 'false';
    } else if (verdict.verdict === 'UNCERTAIN') {
        verdictClass = 'uncertain';
    } else {
        verdictClass = 'unverified';
    }
    
    resultsDiv.innerHTML = `
        <div class="verdict-card ${verdictClass}">
            <div class="verdict-title">
                <i class="fas fa-${verdict.verdict === 'TRUE' ? 'check-circle' : 
                                 verdict.verdict === 'LIKELY TRUE' ? 'check-circle' : 
                                 verdict.verdict === 'LIKELY FALSE' ? 'times-circle' : 
                                 verdict.verdict === 'UNCERTAIN' ? 'question-circle' : 'question-circle'}"></i>
                ${verdict.verdict}
            </div>
            <div class="verdict-confidence">Confidence: ${verdict.confidence}</div>
            <div class="verdict-score">Overall Score: ${verdict.final_score}/100</div>
            <div class="verdict-explanation">${verdict.explanation}</div>
        </div>
        
        <div class="analysis-grid">
            <div class="analysis-card">
                <div class="analysis-icon">🔍</div>
                <div class="analysis-value">${data.analysis.source_credibility}/100</div>
                <div class="analysis-label">Source Credibility</div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">🔗</div>
                <div class="analysis-value">${data.analysis.cross_source_consistency.score}/100</div>
                <div class="analysis-label">Cross-Source Consistency</div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">✅</div>
                <div class="analysis-value">${data.analysis.fact_checking_score}/100</div>
                <div class="analysis-label">Fact-Checking Score</div>
            </div>
            <div class="analysis-card">
                <div class="analysis-icon">📝</div>
                <div class="analysis-value">${data.analysis.content_quality}/100</div>
                <div class="analysis-label">Content Quality</div>
            </div>
        </div>
        
        ${data.top_sources.length > 0 ? `
            <div class="sources-section">
                <div class="sources-title">
                    <i class="fas fa-newspaper"></i> Top Sources (${data.top_sources.length})
                </div>
                ${data.top_sources.map(source => `
                    <div class="source-item">
                        <div class="source-title">${source.title}</div>
                        <div class="source-meta">
                            <span>${source.source} • ${source.api_source}</span>
                            <span class="credibility-badge credibility-${source.credibility >= 80 ? 'high' : source.credibility >= 60 ? 'medium' : 'low'}">
                                ${source.credibility}/100
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;
    
    resultsDiv.style.display = 'block';
}

function displayComprehensiveResults(data) {
    // This will show both ML and online results combined
    const resultsDiv = document.getElementById('results');
    
    let html = '<h2 style="margin-bottom: 20px; color: #2c3e50;">🤖 Comprehensive Analysis Results</h2>';
    
    // ML Results
    if (data.ml_prediction) {
        const ml = data.ml_prediction;
        html += `
            <div class="verdict-card ${ml.prediction === 'fake' ? 'false' : ''}" style="margin-bottom: 20px;">
                <div class="verdict-title">
                    <i class="fas fa-robot"></i> AI Prediction: ${ml.prediction.toUpperCase()}
                </div>
                <div class="verdict-confidence">Confidence: ${(ml.confidence * 100).toFixed(1)}%</div>
            </div>
        `;
    }
    
    // Online Results
    if (data.online_verification) {
        const online = data.online_verification;
        const verdict = online.verdict;
        let verdictClass = '';
        
        if (verdict.verdict === 'TRUE' || verdict.verdict === 'LIKELY TRUE') {
            verdictClass = '';
        } else if (verdict.verdict === 'LIKELY FALSE') {
            verdictClass = 'false';
        } else if (verdict.verdict === 'UNCERTAIN') {
            verdictClass = 'uncertain';
        } else {
            verdictClass = 'unverified';
        }
        
        html += `
            <div class="verdict-card ${verdictClass}">
                <div class="verdict-title">
                    <i class="fas fa-globe"></i> Online Verification: ${verdict.verdict}
                </div>
                <div class="verdict-confidence">Confidence: ${verdict.confidence}</div>
                <div class="verdict-score">Overall Score: ${verdict.final_score}/100</div>
                <div class="verdict-explanation">${verdict.explanation}</div>
            </div>
        `;
        
        html += `
            <div class="analysis-grid">
                <div class="analysis-card">
                    <div class="analysis-icon">🔍</div>
                    <div class="analysis-value">${online.analysis.source_credibility}/100</div>
                    <div class="analysis-label">Source Credibility</div>
                </div>
                <div class="analysis-card">
                    <div class="analysis-icon">🔗</div>
                    <div class="analysis-value">${online.analysis.cross_source_consistency.score}/100</div>
                    <div class="analysis-label">Cross-Source Consistency</div>
                </div>
                <div class="analysis-card">
                    <div class="analysis-icon">✅</div>
                    <div class="analysis-value">${online.analysis.fact_checking_score}/100</div>
                    <div class="analysis-label">Fact-Checking Score</div>
                </div>
                <div class="analysis-card">
                    <div class="analysis-icon">📝</div>
                    <div class="analysis-value">${online.analysis.content_quality}/100</div>
                    <div class="analysis-label">Content Quality</div>
                </div>
            </div>
        `;
    }
}
