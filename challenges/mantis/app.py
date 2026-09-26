from flask import Flask, render_template, request, render_template_string, jsonify, redirect, url_for
import os
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

FLAG1 = os.environ.get('FLAG1', '')
FLAG2 = os.environ.get('FLAG2', '')
FLAG3 = os.environ.get('FLAG3', '')

def init_flags():
    """Initialize flag files for RCE and privesc flags"""
    # FLAG2 readable by ctfuser (RCE target)
    os.makedirs('/home/ctfuser', exist_ok=True)
    try:
        with open('/home/ctfuser/flag2.txt', 'w') as f:
            f.write(f"{FLAG2}\n")
    except PermissionError:
        pass

    # FLAG3 is in /root/flag3.txt (written by Dockerfile, requires sudo privesc)

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/flag1')
def flag1_redirect():
    """Redirect legacy docs path to the actual challenge entry point."""
    return redirect(url_for('generator'))

@app.route('/generator', methods=['GET', 'POST'])
def generator():
    """Notification builder — generates formatted emails"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', 'Customer')
            company = request.form.get('company', 'Company')
            message = request.form.get('message', '')
            custom_greeting = request.form.get('custom_greeting', 'Dear')

            template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Generated Notification</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .letter {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .content {{
            line-height: 1.6;
            margin: 20px 0;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #999;
            font-size: 0.9em;
        }}
        .flag-display {{
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #28a745;
            margin-top: 20px;
            font-family: monospace;
        }}
    </style>
</head>
<body>
    <div class="letter">
        <div class="header">
            <h1>EverSec Security Solutions</h1>
        </div>
        <div class="content">
            <p>{custom_greeting} {name},</p>
            <p>{message}</p>
            <p>Best regards,<br>
            EverSec Team<br>
            {company}</p>
        </div>
        <div class="footer">
            Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            EverSec Notification Service v2.1
        </div>
    </div>
</body>
</html>
"""

            # VULNERABLE: render_template_string processes Jinja2 expressions in user input
            rendered = render_template_string(template)

            # Detect SSTI: if user input contained {{ }} and it got evaluated,
            # the raw input won't appear verbatim in the output
            raw_greeting = request.form.get('custom_greeting', '')
            if '{{' in raw_greeting and '{{' not in rendered:
                # Expression was evaluated — SSTI confirmed, award FLAG1
                rendered = rendered.replace('</body>', f"""
    <div class="letter" style="margin-top: 20px;">
        <div class="flag-display">
            FLAG 1: {FLAG1}
        </div>
    </div>
</body>""")

            return rendered

        except Exception as e:
            return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body {{ font-family: Arial; max-width: 800px; margin: 50px auto; padding: 20px; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; border-left: 4px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="error">
        <h2>Rendering Error</h2>
        <p><strong>Error:</strong> {str(e)}</p>
        <p><a href="/generator">&larr; Back to Builder</a></p>
    </div>
</body>
</html>
"""

    return render_template('generator.html')

@app.route('/api/render', methods=['POST'])
def api_render():
    """API endpoint for notification rendering"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        template_string = data.get('template', '')
        variables = data.get('variables', {})

        if not template_string:
            return jsonify({'error': 'Template string required'}), 400

        try:
            # VULNERABLE: Direct template rendering of user input
            rendered = render_template_string(template_string, **variables)

            return jsonify({
                'success': True,
                'rendered': rendered,
                'message': 'Notification rendered successfully'
            })

        except Exception as e:
            return jsonify({
                'error': f'Rendering error: {str(e)}',
                'hint': 'Check your input syntax'
            }), 400

    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/docs')
def api_docs():
    """API documentation"""
    return render_template('api_docs.html')

@app.route('/examples')
def examples():
    """Show example notifications"""
    return render_template('examples.html')

if __name__ == '__main__':
    init_flags()
    app.run(host='0.0.0.0', port=4006, debug=False)
