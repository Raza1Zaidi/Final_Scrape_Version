from flask import Flask, request, render_template_string, jsonify
import pandas as pd
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
HTML_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Enrich Social URLs for Your Domains</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.2/dist/css/bootstrap.min.css">
    <style>
      /* Add a small loading message style */
      #loadingMessage {
        display: none;
        text-align: center;
        padding: 20px;
        font-size: 20px;
        color: #007bff;
        font-weight: bold;
      }
      
      /* Center the table for better appearance */
      table {
        width: 100%;
        margin-top: 20px;
        border-collapse: collapse;
      }
      th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
      }
      th {
        background-color: #f2f2f2;
      }
    </style>
  </head>
  <body class="container mt-5">
    <h1 class="mb-4 text-center">Enrich Social URLs for Your Domains</h1>
    <form id="csvForm" method="post" enctype="multipart/form-data">
      <div class="form-group">
        <label for="file">Upload a CSV file with a header 'domain'</label>
        <input type="file" name="file" id="file" class="form-control-file" required>
      </div>
      <button type="submit" class="btn btn-primary btn-block">Upload</button>
    </form>
    
    <!-- Please wait message -->
    <div id="loadingMessage">Please wait while we process your request...</div>

    <!-- Output table will be injected here -->
    <div id="outputContainer">
      <!-- The table or output will be displayed here -->
      {{ table_data|safe }}
    </div>

    <!-- Copy button to copy the table content -->
    <button id="copyButton" onclick="copyToClipboard()" class="btn btn-secondary mt-3">Copy to Clipboard</button>

    <script>
      // Show the loading message when the form is submitted
      document.getElementById('csvForm').addEventListener('submit', function() {
        document.getElementById('loadingMessage').style.display = 'block';
      });

      // Hide the loading message once the data is processed (you can trigger this manually on success)
      function hideLoading() {
        document.getElementById('loadingMessage').style.display = 'none';
      }

      // Function to copy the table content to clipboard
      function copyToClipboard() {
        const table = document.querySelector('#outputContainer').innerText;
        navigator.clipboard.writeText(table)
          .then(() => alert('Copied to clipboard!'))
          .catch(err => alert('Failed to copy: ', err));
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
