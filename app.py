
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify
import os

app = Flask(__name__)

# Function to scrape social media URLs from a given domain
def extract_social_links(domain):
    social_links = {
        'facebook': None,
        'linkedin': None,
        'twitter': None
    }
    try:
        response = requests.get(f'http://{domain}', timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if 'facebook.com' in href:
                social_links['facebook'] = href
            elif 'linkedin.com' in href:
                social_links['linkedin'] = href
            elif 'twitter.com' in href or 'x.com' in href:
                social_links['twitter'] = href
    except Exception as e:
        social_links['error'] = str(e)
    
    return social_links

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        # Read the uploaded CSV
        domains_df = pd.read_csv(file)
        if 'domain' not in domains_df.columns:
            return jsonify({'error': 'Invalid CSV format. "domain" column is required.'}), 400
        
        domains = domains_df['domain'].tolist()
        total_domains = len(domains)
        
        if total_domains > 1000:
            return jsonify({'error': 'Please upload a CSV with up to 1000 domains.'}), 400
        
        # Process each domain and gather results
        results = []
        for i, domain in enumerate(domains):
            social_links = extract_social_links(domain)
            results.append({
                'domain': domain,
                'facebook': social_links['facebook'],
                'linkedin': social_links['linkedin'],
                'twitter': social_links['twitter'],
                'status': social_links.get('error', 'Success')
            })

        # Return the results as JSON for rendering on the front-end
        return jsonify({'results': results})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
