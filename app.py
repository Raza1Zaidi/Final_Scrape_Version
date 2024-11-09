from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <title>Enrich Social URLs</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        margin: 20px;
      }
      h1 {
        color: #2c3e50;
      }
      table {
        width: 100%;
        margin-top: 20px;
        border: 1px solid #ddd;
        border-collapse: collapse;
      }
      th, td {
        border: 1px solid #ddd;
        padding: 10px;
        text-align: left;
      }
      th {
        background-color: #f2f2f2;
      }
      button {
        margin-top: 10px;
        padding: 10px 20px;
        background-color: #3498db;
        color: white;
        border: none;
        cursor: pointer;
        border-radius: 5px;
      }
      button:hover {
        background-color: #2980b9;
      }
      .instructions {
        margin-bottom: 20px;
        font-style: italic;
      }
      #loading-message {
        display: none;
        font-style: italic;
        color: #2c3e50;
        margin-top: 20px;
      }
      #domain-count {
        font-weight: bold;
      }
    </style>
  </head>
  <body>
    <h1>Enrich Social URLs for Your Domains</h1>
    <p class="instructions">Enter a CSV of domains you want to scrape with a header “domain”.</p>
    <form id="upload-form" action="/" method="post" enctype="multipart/form-data" onsubmit="showLoadingMessage()">
      <input type="file" name="file" accept=".csv" required onchange="countDomains(this)">
      <p id="domain-count"></p>
      <button type="submit">Upload CSV</button>
    </form>
    <p id="loading-message">Please wait while we process your request...</p>
    <button onclick="copyTable()">Copy to Clipboard</button>
    <h2>Results</h2>
    <table id="results-table" style="display:none;">
      <tr>
        <th>Domain</th>
        <th>Twitter URL</th>
        <th>Facebook URL</th>
        <th>LinkedIn URL</th>
      </tr>
    </table>
    
    <script>
      function countDomains(input) {
        const file = input.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function(e) {
            const lines = e.target.result.split('\\n');
            const domainCount = lines.length - 1; // Adjust for the header line
            document.getElementById('domain-count').textContent = `Total Domains: ${domainCount}`;
          };
          reader.readAsText(file);
        }
      }

      function showLoadingMessage() {
        document.getElementById('loading-message').style.display = 'block';
        document.getElementById('results-table').style.display = 'table';
        startProgressUpdates();
      }

      function copyTable() {
        let range = document.createRange();
        range.selectNode(document.querySelector('#results-table'));
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        document.execCommand('copy');
        alert('Table copied to clipboard!');
      }

      function startProgressUpdates() {
        const interval = setInterval(async function() {
          const response = await fetch('/progress');
          const data = await response.json();

          const resultsTable = document.getElementById('results-table');
          resultsTable.style.display = 'table';

          if (data.processed_results.length) {
            // Clear existing rows (excluding header)
            resultsTable.innerHTML = '<tr><th>Domain</th><th>Twitter URL</th><th>Facebook URL</th><th>LinkedIn URL</th></tr>';

            // Populate the table with processed results
            data.processed_results.forEach(row => {
              const tr = document.createElement('tr');
              tr.innerHTML = `
                <td>${row.Domain}</td>
                <td>${row.Twitter || '-'}</td>
                <td>${row.Facebook || '-'}</td>
                <td>${row.LinkedIn || '-'}</td>
              `;
              resultsTable.appendChild(tr);
            });
          }

          if (data.complete) {
            clearInterval(interval);
            document.getElementById('loading-message').textContent = 'Processing complete!';
          }
        }, 3000); // Poll every 3 seconds
      }
    </script>
  </body>
</html>
"""
def scrape_social_links(domain):
    twitter_url, facebook_url, linkedin_url = None, None, None
    try:
        response = requests.get(f"http://{domain}", timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'twitter.com' in href or 'x.com' in href:
                twitter_url = href
            elif 'facebook.com' in href:
                facebook_url = href
            elif 'linkedin.com' in href:
                linkedin_url = href
    except requests.exceptions.RequestException:
        pass
    return twitter_url, facebook_url, linkedin_url

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            df = pd.read_csv(file)
            if 'domain' not in df.columns:
                return "Invalid CSV format. Please ensure the file has a 'domain' column.", 400
            for index, row in df.iterrows():
                domain = row['domain']
                twitter, facebook, linkedin = scrape_social_links(domain)
                results.append({
                    'Domain': domain,
                    'Twitter': twitter or 'Not found',
                    'Facebook': facebook or 'Not found',
                    'LinkedIn': linkedin or 'Not found'
                })
    return render_template_string(HTML_TEMPLATE, results=results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
