from flask import Flask, render_template, request, jsonify
import re, requests
from bs4 import BeautifulSoup
from flask_cors import CORS
import google.generativeai as genai

genai.configure(api_key="AIzaSyB1xeoyR-F4MKTqjLKFB5xqlU9_Idt-zrI")
app = Flask(__name__)
CORS(app)
    
@app.route('/')
def home():
    return render_template('index.html')

def get_additional_context(soup):
    description = soup.find('meta', attrs={'name': 'description'})
    description_content = description['content'] if description else 'No description available'

    keywords = soup.find('meta', attrs={'name': 'keywords'})
    keywords_content = keywords['content'] if keywords else 'No keywords available'

    target_audience = "General" 

    return description_content, keywords_content, target_audience

def get_ai_suggestion(content_type, current_content, description, keywords, target_audience):
    model = genai.GenerativeModel("gemini-1.5-flash")  

    prompts = {
        "title": f"Suggest a better SEO title for a {content_type} page. Current title: {current_content}. Page description: {description}. Keywords: {keywords}. Target audience: {target_audience}. In less than 10 words",
        "meta description": f"Suggest a better meta description for SEO. Current description: {current_content}. Page description: {description}. Keywords: {keywords}. Target audience: {target_audience}. Keep it concise (under 60 characters) and direct, without using phrases like 'Here are a few options'.",
    }

    suggestion = prompts[content_type]
    response = model.generate_content(suggestion)
    return response.text.strip()

def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' 
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
        r'localhost|' 
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'
        r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' 
        r'(?::\d+)?'  
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

def fix_url_protocol(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def is_mobile_friendly(soup):
    viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
    if viewport_meta:
        content = viewport_meta.get('content', '')
        if 'width=device-width' in content:
            return True
    
    styles = soup.find_all('style')
    for style in styles:
        if '@media' in style.text:
            return True

    return False

@app.route('/analyze', methods=['POST'])
def analyze_website():
    try:
        data = request.get_json()
        website_url = data.get('url', '').strip()
        website_url = fix_url_protocol(website_url)

        if not is_valid_url(website_url):
            return jsonify({'status': 'error', 'message': 'Invalid URL format'}), 400

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(website_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return jsonify({'status': 'error', 'message': f"Error: {response.status_code} - {response.text}"}), 400

        soup = BeautifulSoup(response.text, 'html.parser')

        # SEO Checks
        title = soup.title.string.strip() if soup.title and soup.title.string else 'No title found'
        title_length = len(title)

        meta_description_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_description_tag['content'].strip() if meta_description_tag and meta_description_tag.get('content') else 'No meta description found'
        meta_description_length = len(meta_description)

        h1_tags = soup.find_all('h1')
        h1_count = len(h1_tags)

        canonical_url_tag = soup.find('link', attrs={'rel': 'canonical'})
        canonical_url = canonical_url_tag['href'].strip() if canonical_url_tag and canonical_url_tag.get('href') else 'No canonical URL found'

        mobile_friendly = is_mobile_friendly(soup)

        description, keywords, target_audience = get_additional_context(soup)

        title_suggestion = get_ai_suggestion("title", title, description, keywords, target_audience)
        meta_description_suggestion = get_ai_suggestion("meta description", meta_description, description, keywords, target_audience)

        result_data = {
            'status': 'success',
            'title': title,
            'title_length': title_length,
            'meta_description': meta_description,
            'meta_description_length': meta_description_length,
            'h1_count': h1_count,
            'canonical_url': canonical_url,
            'title_suggestion': title_suggestion,
            'meta_description_suggestion': meta_description_suggestion,
            'mobile_friendly': mobile_friendly
        }

        return jsonify(result_data)

    except requests.exceptions.Timeout:
        # Timeout error
        message = "Your website is too slow to respond. Here are some suggestions to improve its performance:"
        suggestions = [
            "1. Check your server's performance. High traffic or heavy load can slow down response times.",
            "2. Optimize your website's content, such as compressing images and reducing file sizes.",
            "3. Use caching mechanisms to improve page load speed.",
            "4. Consider using a Content Delivery Network (CDN) to speed up delivery of your content.",
            "5. Check for any ongoing maintenance or issues with your hosting provider."
        ]
        return jsonify({
            'status': 'error',
            'message': message,
            'suggestions': suggestions
        }), 504
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/results', methods=['GET'])
def results():
    data = {
        'title': request.args.get('title'),
        'title_length': request.args.get('title_length'),
        'meta_description': request.args.get('meta_description'),
        'meta_description_length': request.args.get('meta_description_length'),
        'h1_count': request.args.get('h1_count'),
        'canonical_url': request.args.get('canonical_url'),
        'images_without_alt': request.args.get('images_without_alt'),
        'title_suggestion': request.args.get('title_suggestion'),
        'meta_description_suggestion': request.args.get('meta_description_suggestion'),
        'mobile_friendly': request.args.get('mobile_friendly')
    }

    data['title_length'] = len(data['title']) if data['title'] else 0
    data['meta_description_length'] = len(data['meta_description']) if data['meta_description'] else 0
    if data['images_without_alt']:
        data['images_without_alt'] = data['images_without_alt'].split(',')

    return render_template('results.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)