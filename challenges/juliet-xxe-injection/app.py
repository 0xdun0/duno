from flask import Flask, render_template, request, jsonify
from lxml import etree
import os
import threading
import subprocess
from datetime import datetime

app = Flask(__name__)

# Flags
FLAG1 = os.environ.get('FLAG1', 'xxe_d1sc0v3r3d')
FLAG2 = os.environ.get('FLAG2', 'f1l3_r34d_succ3ss')
FLAG3 = os.environ.get('FLAG3', 'ssrf_t0_1nt3rn4l')
FLAG4 = os.environ.get('FLAG4', 'xxe_rc3_ch41n3d')
FLAG5 = os.environ.get('FLAG5', 'f1nd_pr1v_3sc_r00t')

# Create flag files
def init_flags():
    """Initialize flag files on disk"""
    os.makedirs('/tmp/flags', exist_ok=True)

    with open('/tmp/flags/flag1.txt', 'w') as f:
        f.write(f"Congratulations! You've discovered XXE!\n{FLAG1}\n")

    # FLAG2: Hidden in a realistic config path (requires XXE file read to discover)
    os.makedirs('/opt/eversec/secrets', exist_ok=True)
    with open('/opt/eversec/secrets/credentials.conf', 'w') as f:
        f.write(f"# EverSec Internal Credentials\n")
        f.write(f"# DO NOT SHARE\n")
        f.write(f"db_host=10.0.1.50\n")
        f.write(f"db_user=eversec_admin\n")
        f.write(f"db_pass={FLAG2}\n")
        f.write(f"api_secret=sk_live_9f8e7d6c5b4a3\n")

    # FLAG4: Accessible via RCE through internal service
    with open('/home/ctfuser/flag4.txt', 'w') as f:
        f.write(FLAG4)

    print("[*] Flag files initialized")
    print(f"[*] FLAG1: /tmp/flags/flag1.txt")
    print(f"[*] FLAG2: /opt/eversec/secrets/credentials.conf")
    print(f"[*] FLAG4: /home/ctfuser/flag4.txt")
    print(f"[*] FLAG5: /root/flag5.txt (written by Dockerfile)")

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Invoice upload page - VULNERABLE to XXE"""
    if request.method == 'POST':
        try:
            # Check if file was uploaded
            if 'invoice' not in request.files:
                return render_template('upload.html', error='No file uploaded')

            file = request.files['invoice']

            if file.filename == '':
                return render_template('upload.html', error='No file selected')

            if not file.filename.endswith('.xml'):
                return render_template('upload.html', error='Only XML files are accepted')

            # Read XML content
            xml_content = file.read().decode('utf-8')

            try:
                # VULNERABLE: resolve_entities=True enables XXE
                parser = etree.XMLParser(resolve_entities=True, no_network=False)
                root = etree.fromstring(xml_content.encode(), parser=parser)

                # Parse invoice data
                invoice_data = {
                    'number': root.findtext('number', 'N/A'),
                    'date': root.findtext('date', 'N/A'),
                    'customer': root.findtext('customer', 'N/A'),
                    'amount': root.findtext('amount', 'N/A'),
                }

                # Check for items
                items = []
                items_element = root.find('items')
                if items_element is not None:
                    for item in items_element.findall('item'):
                        items.append({
                            'description': item.findtext('description', 'N/A'),
                            'price': item.findtext('price', 'N/A'),
                        })

                invoice_data['line_items'] = items

                # Extract all text content (this is where XXE content appears)
                raw_text = etree.tostring(root, method='text', encoding='unicode')

                return render_template('result.html',
                                     invoice=invoice_data,
                                     raw_content=raw_text,
                                     success=True)

            except etree.XMLSyntaxError as e:
                error_msg = str(e)
                return render_template('upload.html',
                                     error=f'XML parsing error: {error_msg}')

        except Exception as e:
            return render_template('upload.html',
                                 error=f'Error processing invoice: {str(e)}')

    return render_template('upload.html')

@app.route('/api/parse', methods=['POST'])
def api_parse():
    """API endpoint for XML parsing - VULNERABLE to XXE"""
    try:
        # Get XML from request body
        xml_content = request.data.decode('utf-8')

        if not xml_content:
            return jsonify({'error': 'No XML content provided'}), 400

        # VULNERABLE: resolve_entities=True enables XXE
        parser = etree.XMLParser(resolve_entities=True, no_network=False)

        try:
            root = etree.fromstring(xml_content.encode(), parser=parser)

            # Extract invoice data
            invoice_data = {
                'number': root.findtext('number', 'N/A'),
                'date': root.findtext('date', 'N/A'),
                'customer': root.findtext('customer', 'N/A'),
                'amount': root.findtext('amount', 'N/A'),
            }

            # Extract all text (this is where XXE content shows up)
            raw_text = etree.tostring(root, method='text', encoding='unicode')

            # Extract items
            items = []
            items_element = root.find('items')
            if items_element is not None:
                for item in items_element.findall('item'):
                    items.append({
                        'description': item.findtext('description', 'N/A'),
                        'price': item.findtext('price', 'N/A'),
                    })

            invoice_data['line_items'] = items

            return jsonify({
                'success': True,
                'invoice': invoice_data,
                'raw_content': raw_text,
                'message': 'Invoice parsed successfully'
            })

        except etree.XMLSyntaxError as e:
            return jsonify({
                'error': f'XML parsing error: {str(e)}',
                'hint': 'Check your XML syntax and DTD declarations'
            }), 400

    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/admin/flag')
def admin_flag():
    """Internal admin endpoint - only accessible via SSRF (FLAG 3)"""
    if request.remote_addr not in ['127.0.0.1', 'localhost', '::1']:
        return jsonify({'error': 'Access denied - internal endpoint only'}), 403
    return jsonify({
        'message': 'Internal admin endpoint',
        'flag': FLAG3,
        'note': 'This endpoint should only be accessible internally'
    })

@app.route('/robots.txt')
def robots():
    """Robots.txt - hints at internal paths"""
    return """User-agent: *
Disallow: /admin/
Disallow: /tmp/
Disallow: /opt/eversec/
""", 200, {'Content-Type': 'text/plain'}

@app.route('/api/docs')
def api_docs():
    """API documentation"""
    return render_template('api_docs.html')

@app.route('/example')
def example():
    """Show example invoice XML"""
    example_xml = """<?xml version="1.0" encoding="UTF-8"?>
<invoice>
    <number>INV-2026-001</number>
    <date>2026-01-19</date>
    <customer>Acme Corporation</customer>
    <amount>1500.00</amount>
    <items>
        <item>
            <description>Security Audit</description>
            <price>1000.00</price>
        </item>
        <item>
            <description>Penetration Testing</description>
            <price>500.00</price>
        </item>
    </items>
</invoice>"""

    return render_template('example.html', xml=example_xml)


def start_internal_service():
    """Internal admin service - only accessible from localhost (port 5001)

    This service is the target for SSRF -> RCE chaining (FLAG4).
    Players must use XXE SSRF to reach http://127.0.0.1:5001/execute?cmd=...
    """
    from flask import Flask as InternalFlask, request as int_request, jsonify as int_jsonify

    internal_app = InternalFlask('internal')

    @internal_app.route('/')
    def internal_home():
        return int_jsonify({
            'service': 'EverSec Internal Admin',
            'status': 'running',
            'endpoints': ['/execute']
        })

    @internal_app.route('/execute', methods=['GET', 'POST'])
    def internal_execute():
        if int_request.method == 'GET':
            command = int_request.args.get('cmd', '')
        else:
            data = int_request.get_json() or {}
            command = data.get('cmd', '') or data.get('command', '')

        if not command:
            return int_jsonify({'error': 'No command provided'})

        try:
            result = subprocess.check_output(command, shell=True, text=True, timeout=5)
            return int_jsonify({'output': result.strip(), 'success': True})
        except subprocess.TimeoutExpired:
            return int_jsonify({'error': 'Command timed out'})
        except Exception as e:
            return int_jsonify({'error': str(e)})

    internal_app.run(host='127.0.0.1', port=5001, debug=False)


if __name__ == '__main__':
    # Initialize flag files
    init_flags()

    # Start internal admin service in background thread
    threading.Thread(target=start_internal_service, daemon=True).start()

    # Run Flask app
    app.run(host='0.0.0.0', port=4005, debug=False)
