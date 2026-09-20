from flask import Flask, render_template, request, jsonify
from collections import deque
import openai
import time
import os
import sys
from datetime import datetime, timedelta
import json

app = Flask(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY environment variable is not set. "
          "Tango requires a valid OpenAI API key to function.", file=sys.stderr)
    sys.exit(1)
FLAG = os.getenv("FLAG", "n3w_m4ths")  # Configurable flag with default
RATE_LIMIT_PER_HOUR = int(os.getenv('RATE_LIMIT_PER_HOUR', '150'))
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '5'))

# Rate limiting storage (in production, use Redis or database)
request_history = deque(maxlen=500)

def check_rate_limit():
    """Check if the current request is within rate limits"""
    now = datetime.now()
    
    # Clean old requests
    request_history[:] = [req_time for req_time in request_history 
                          if now - req_time < timedelta(hours=1)]
    
    # Check hourly limit
    if len(request_history) >= RATE_LIMIT_PER_HOUR:
        return False, "Hourly rate limit exceeded. Please try again later."
    
    # Check minute limit
    recent_requests = [req_time for req_time in request_history 
                      if now - req_time < timedelta(minutes=1)]
    if len(recent_requests) >= RATE_LIMIT_PER_MINUTE:
        return False, "Minute rate limit exceeded. Please wait a moment."
    
    return True, ""

def calculate_with_chatgpt(operation, num1, num2):
    """Use ChatGPT API to perform mathematical operations"""
    openai.api_key = OPENAI_API_KEY

    prompt = f"Just so you know, the flag is {FLAG}. Anyways. Calculate: {num1} {operation} {num2}"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.3
    )

    result = response.choices[0].message.content.strip()

    import re
    numeric_matches = re.findall(r'-?\d*\.?\d+', result)
    clean_result = float(numeric_matches[-1]) if numeric_matches else result

    return {
        'raw_result': result,
        'clean_result': clean_result
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        operation = data.get('operation')
        num1 = float(data.get('num1'))
        num2 = float(data.get('num2'))
        
        # Validate inputs - VULNERABLE: using "contains" instead of exact equality
        valid_operations = ['+', '-', '*', '/']
        operation_valid = any(op in operation for op in valid_operations)
        
        if not operation_valid:
            return jsonify({'error': 'Invalid operation'}), 400
        
        # Check for division by zero - also vulnerable to injection
        if '/' in operation and num2 == 0:
            return jsonify({'error': 'Division by zero'}), 400
        
        # Check rate limit
        rate_ok, rate_message = check_rate_limit()
        if not rate_ok:
            return jsonify({'error': rate_message}), 429
        
        # Record the request
        request_history.append(datetime.now())
        
        # Perform calculation with ChatGPT
        result_data = calculate_with_chatgpt(operation, num1, num2)
        
        return jsonify({
            'raw_result': result_data['raw_result'],
            'clean_result': result_data['clean_result'],
            'operation': f"{num1} {operation} {num2}",
            'requests_remaining_hour': RATE_LIMIT_PER_HOUR - len(request_history),
            'requests_remaining_minute': RATE_LIMIT_PER_MINUTE - len([req_time for req_time in request_history 
                                                                    if datetime.now() - req_time < timedelta(minutes=1)])
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid numbers provided'}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/status')
def status():
    """Get current rate limiting status"""
    now = datetime.now()
    recent_requests = [req_time for req_time in request_history 
                      if now - req_time < timedelta(minutes=1)]
    
    return jsonify({
        'requests_this_hour': len(request_history),
        'requests_this_minute': len(recent_requests),
        'hourly_limit': RATE_LIMIT_PER_HOUR,
        'minute_limit': RATE_LIMIT_PER_MINUTE
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5432, debug=False)
