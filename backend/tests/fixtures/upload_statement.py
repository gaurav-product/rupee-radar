import urllib.request
import urllib.parse
import mimetypes
import json
import os

def upload_file(url, file_path):
    # Prepare multipart/form-data payload
    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or 'application/octet-stream'
    
    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
        
    parts = []
    parts.append(f'--{boundary}')
    parts.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"')
    parts.append(f'Content-Type: {mime_type}')
    parts.append('')
    parts.append(file_content)
    parts.append(f'--{boundary}--')
    parts.append('')
    
    # Encode body
    body = b''
    for part in parts:
        if isinstance(part, bytes):
            body += part
        else:
            body += part.encode('utf-8') + b'\r\n'
            
    req = urllib.request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Content-Length', str(len(body)))
    
    try:
        with urllib.request.urlopen(req) as res:
            response_data = res.read().decode('utf-8')
            return json.loads(response_data)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode('utf-8')}")
        raise e

if __name__ == '__main__':
    url = "http://127.0.0.1:8000/api/v1/upload"
    file_path = r"C:\Users\gaura\.gemini\antigravity-ide\scratch\rupee-radar\backend\tests\fixtures\sample_statement.csv"
    print(f"Uploading {file_path} to {url}...")
    res = upload_file(url, file_path)
    print("Response:")
    print(json.dumps(res, indent=2))
    
    # Save the session ID in a temporary text file so the subagent can read it if needed
    with open("session_id.txt", "w") as f:
        f.write(res["session_id"])
