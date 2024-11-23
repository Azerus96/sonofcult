import os
import requests
import json
from datetime import datetime

def sync_progress():
    token = os.environ.get('AI_PROGRESS_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    
    if not token or not repo:
        print("Missing required environment variables")
        return
    
    progress_dir = os.path.join(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__))), 'progress')
        
    if not os.path.exists(progress_dir):
        print("Progress directory not found")
        return
        
    # Подготовка данных для отправки
    files = []
    for filename in os.listdir(progress_dir):
        if filename.endswith('.json'):
            with open(os.path.join(progress_dir, filename), 'r') as f:
                content = json.load(f)
                files.append({
                    'name': filename,
                    'content': content
                })
    
    # Создание коммита
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    api_url = f'https://api.github.com/repos/{repo}/contents/progress'
    
    for file in files:
        # Проверяем существование файла
        response = requests.get(
            f'{api_url}/{file["name"]}',
            headers=headers
        )
        
        file_content = json.dumps(file['content'], indent=2)
        data = {
            'message': f'Update progress {datetime.now().isoformat()}',
            'content': base64.b64encode(file_content.encode()).decode(),
            'branch': 'main'
        }
        
        if response.status_code == 200:
            # Файл существует, обновляем
            current_file = response.json()
            data['sha'] = current_file['sha']
            
        response = requests.put(
            f'{api_url}/{file["name"]}',
            headers=headers,
            json=data
        )
        
        if response.status_code not in [200, 201]:
            print(f"Error syncing {file['name']}: {response.text}")
        else:
            print(f"Successfully synced {file['name']}")

if __name__ == '__main__':
    sync_progress()
