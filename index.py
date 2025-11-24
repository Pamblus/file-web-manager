#!/usr/bin/env python3
import http.server
import socketserver
import os
import json
import urllib.parse
import html
import time
import mimetypes

class FileManagerHandler(http.server.SimpleHTTPRequestHandler):
    
    # Пароль для доступа
    PASSWORD = "pass123"
    
    # Иконки для разных типов файлов
    ICONS = {
        'folder': '📁',
        'default': '📄',
        'image': '🖼️',
        'audio': '🎵',
        'video': '🎬',
        'archive': '📦',
        'code': '📝',
        'pdf': '📕',
        'text': '📄',
        'hidden': '🔒'
    }
    
    # Расширения файлов
    FILE_TYPES = {
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
        'video': ['.mp4', '.avi', '.mkv', '.mov', '.webm'],
        'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'code': ['.html', '.htm', '.css', '.js', '.py', '.php', '.json', '.xml', '.txt', '.md'],
        'pdf': ['.pdf'],
        'text': ['.txt', '.md', '.log']
    }
    
    def get_file_icon(self, filename):
        """Возвращает иконку для файла"""
        if os.path.isdir(filename):
            return self.ICONS['folder']
        
        if filename.startswith('.'):
            return self.ICONS['hidden']
        
        ext = os.path.splitext(filename)[1].lower()
        for file_type, extensions in self.FILE_TYPES.items():
            if ext in extensions:
                return self.ICONS[file_type]
        return self.ICONS['default']
    
    def check_auth(self):
        """Проверяет авторизацию"""
        if 'Cookie' in self.headers:
            cookies = self.headers['Cookie'].split(';')
            for cookie in cookies:
                if 'filemanager_auth' in cookie:
                    auth_value = cookie.split('=')[1].strip()
                    return auth_value == self.PASSWORD
        return False
    
    def send_auth_form(self):
        """Отправляет форму ввода пароля"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>File Manager - Access</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: #2d3748;
                    height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin: 0;
                }
                .auth-container {
                    background: #4a5568;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 400px;
                    width: 90%;
                }
                h2 {
                    color: white;
                    margin-bottom: 30px;
                }
                .form-group {
                    margin-bottom: 20px;
                }
                input[type="password"] {
                    width: 100%;
                    padding: 15px;
                    background: #718096;
                    border: 2px solid #a0aec0;
                    border-radius: 5px;
                    font-size: 16px;
                    box-sizing: border-box;
                    color: white;
                }
                input[type="password"]::placeholder {
                    color: #cbd5e0;
                }
                button {
                    width: 100%;
                    padding: 15px;
                    background: #667eea;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background 0.3s;
                }
                button:hover {
                    background: #764ba2;
                }
            </style>
        </head>
        <body>
            <div class="auth-container">
                <h2>🔐 File Manager Access</h2>
                <form method="post">
                    <div class="form-group">
                        <input type="password" name="password" placeholder="Enter password" required>
                    </div>
                    <button type="submit">Access Files</button>
                </form>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def send_file_manager(self, current_dir):
        """Отправляет файловый менеджер"""
        try:
            files = []
            for item in os.listdir(current_dir):
                item_path = os.path.join(current_dir, item)
                try:
                    stats = os.stat(item_path)
                    files.append({
                        'name': item,
                        'path': item_path,
                        'is_dir': os.path.isdir(item_path),
                        'size': stats.st_size,
                        'modified': stats.st_mtime,
                        'icon': self.get_file_icon(item_path),
                        'is_hidden': item.startswith('.')
                    })
                except:
                    continue
            
            # Сортируем: папки сначала, потом файлы
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            
            html_content = self.generate_file_manager_html(files, current_dir)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html_content.encode())
        except Exception as e:
            self.send_error(500, f"Error reading directory: {str(e)}")
    
    def generate_file_manager_html(self, files, current_dir):
        """Генерирует HTML файлового менеджера"""
        files_html = ""
        for file in files:
            if file['is_dir']:
                link = f'?dir={urllib.parse.quote(file["path"])}'
                open_web = ''
            else:
                link = f'?view={urllib.parse.quote(file["path"])}'
                # Кнопки для файла
                open_web = f'''
                <a href="?preview={urllib.parse.quote(file["path"])}" target="_blank" class="open-web">👁️ View</a>
                <a href="/{file["path"]}" target="_blank" class="open-web">🌐 Open</a>
                '''
            
            file_class = "hidden-file" if file['is_hidden'] else ""
            
            files_html += f"""
            <div class="file-item {file_class}">
                <input type="checkbox" class="file-checkbox" data-path="{html.escape(file['path'])}">
                <span class="file-icon">{file['icon']}</span>
                <span class="file-name">
                    <a href="{link}">{html.escape(file['name'])}</a>
                </span>
                <span class="file-size">{self.format_size(file['size'])}</span>
                <span class="file-modified">{time.strftime('%Y-%m-%d %H:%M', time.localtime(file['modified']))}</span>
                <span class="file-actions">
                    {open_web}
                </span>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>File Manager - {current_dir}</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #1a202c;
                    color: #e2e8f0;
                    line-height: 1.6;
                }}
                .header {{
                    background: #2d3748;
                    color: white;
                    padding: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                }}
                .header h1 {{
                    margin-bottom: 15px;
                    font-size: 24px;
                }}
                .header-controls {{
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }}
                .header button {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s;
                }}
                .btn-home {{ background: #48bb78; color: white; }}
                .btn-back {{ background: #ed8936; color: white; }}
                .btn-logout {{ background: #f56565; color: white; }}
                .btn-home:hover {{ background: #38a169; }}
                .btn-back:hover {{ background: #dd6b20; }}
                .btn-logout:hover {{ background: #e53e3e; }}
                
                .current-path {{
                    background: #2d3748;
                    margin: 20px;
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    font-family: monospace;
                    color: #cbd5e0;
                    word-break: break-all;
                }}
                
                .file-list {{
                    background: #2d3748;
                    margin: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .file-header {{
                    display: flex;
                    background: #4a5568;
                    padding: 12px 15px;
                    font-weight: bold;
                    border-bottom: 2px solid #718096;
                    align-items: center;
                }}
                .file-header > * {{
                    padding: 0 5px;
                }}
                .file-item {{
                    display: flex;
                    align-items: center;
                    padding: 10px 15px;
                    border-bottom: 1px solid #4a5568;
                    transition: background 0.2s;
                }}
                .file-item:hover {{
                    background: #4a5568;
                }}
                .hidden-file {{
                    background: #744210;
                }}
                .file-checkbox {{
                    width: 20px;
                    margin-right: 10px;
                }}
                .file-icon {{
                    width: 30px;
                    font-size: 18px;
                    text-align: center;
                    margin-right: 10px;
                }}
                .file-name {{
                    flex: 3;
                    min-width: 200px;
                    color: #e2e8f0;
                    font-weight: 500;
                }}
                .file-name a {{
                    color: #e2e8f0;
                    text-decoration: none;
                }}
                .file-name a:hover {{
                    color: #90cdf4;
                    text-decoration: underline;
                }}
                .file-size {{
                    flex: 1;
                    min-width: 100px;
                    color: #cbd5e0;
                    font-size: 14px;
                    text-align: right;
                    font-weight: bold;
                }}
                .file-modified {{
                    flex: 1;
                    min-width: 150px;
                    color: #cbd5e0;
                    font-size: 14px;
                    text-align: right;
                    font-weight: bold;
                }}
                .file-actions {{
                    flex: 1;
                    min-width: 120px;
                    text-align: right;
                }}
                .open-web {{
                    color: #90cdf4;
                    text-decoration: none;
                    font-size: 13px;
                    padding: 4px 8px;
                    background: #4a5568;
                    border-radius: 3px;
                    margin-left: 5px;
                    font-weight: bold;
                }}
                .open-web:hover {{
                    background: #5a6578;
                    text-decoration: none;
                }}
                
                .actions {{
                    background: #2d3748;
                    margin: 20px;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    display: flex;
                    gap: 10px;
                    flex-wrap: wrap;
                }}
                .actions button {{
                    padding: 12px 20px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s;
                    min-width: 120px;
                }}
                .btn-create {{ background: #48bb78; color: white; }}
                .btn-folder {{ background: #4299e1; color: white; }}
                .btn-rename {{ background: #ed8936; color: white; }}
                .btn-delete {{ background: #f56565; color: white; }}
                .btn-clone {{ background: #9f7aea; color: white; }}
                .btn-upload {{ background: #ed64a6; color: white; }}
                
                .btn-create:hover {{ background: #38a169; }}
                .btn-folder:hover {{ background: #3182ce; }}
                .btn-rename:hover {{ background: #dd6b20; }}
                .btn-delete:hover {{ background: #e53e3e; }}
                .btn-clone:hover {{ background: #805ad5; }}
                .btn-upload:hover {{ background: #d53f8c; }}

                /* Стили для модальных окон */
                .modal {{
                    display: none;
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0,0,0,0.7);
                }}
                .modal-content {{
                    background-color: #2d3748;
                    margin: 15% auto;
                    padding: 30px;
                    border-radius: 10px;
                    width: 400px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                }}
                .modal-header {{
                    margin-bottom: 20px;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                }}
                .modal-input {{
                    width: 100%;
                    padding: 12px;
                    background: #4a5568;
                    border: 2px solid #718096;
                    border-radius: 5px;
                    color: white;
                    font-size: 16px;
                    margin-bottom: 20px;
                    box-sizing: border-box;
                }}
                .modal-input:focus {{
                    outline: none;
                    border-color: #90cdf4;
                }}
                .modal-actions {{
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }}
                .modal-btn {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                }}
                .modal-confirm {{ background: #48bb78; color: white; }}
                .modal-cancel {{ background: #718096; color: white; }}
                .modal-confirm:hover {{ background: #38a169; }}
                .modal-cancel:hover {{ background: #5a6578; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📁 File Manager</h1>
                <div class="header-controls">
                    <button class="btn-home" onclick="goHome()">🏠 Home</button>
                    <button class="btn-back" onclick="goBack()">⬅️ Back</button>
                    <button class="btn-logout" onclick="logout()">🚪 Logout</button>
                </div>
            </div>
            
            <div class="current-path">
                📍 Current path: {html.escape(current_dir)}
            </div>
            
            <div class="file-list">
                <div class="file-header">
                    <div style="width: 20px; margin-right: 10px;">
                        <input type="checkbox" onchange="toggleAll(this)">
                    </div>
                    <div style="width: 30px; margin-right: 10px;">Icon</div>
                    <div style="flex: 3; min-width: 200px;">Name</div>
                    <div style="flex: 1; min-width: 100px; text-align: right;">Size</div>
                    <div style="flex: 1; min-width: 150px; text-align: right;">Modified</div>
                    <div style="flex: 1; min-width: 120px; text-align: right;">Actions</div>
                </div>
                {files_html}
            </div>
            
            <div class="actions">
                <button class="btn-create" onclick="showModal('createFile')">📄 New File</button>
                <button class="btn-folder" onclick="showModal('createFolder')">📁 New Folder</button>
                <button class="btn-rename" onclick="renameFile()">✏️ Rename</button>
                <button class="btn-delete" onclick="deleteFiles()">🗑️ Delete</button>
                <button class="btn-clone" onclick="cloneFiles()">📋 Clone</button>
                <button class="btn-upload" onclick="uploadFile()">📤 Upload</button>
            </div>

            <!-- Модальное окно для создания файла -->
            <div id="createFileModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">📄 Create New File</div>
                    <input type="text" id="fileName" class="modal-input" placeholder="Enter file name" autofocus>
                    <div class="modal-actions">
                        <button class="modal-btn modal-cancel" onclick="hideModal('createFileModal')">Cancel</button>
                        <button class="modal-btn modal-confirm" onclick="createFile()">Create</button>
                    </div>
                </div>
            </div>

            <!-- Модальное окно для создания папки -->
            <div id="createFolderModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">📁 Create New Folder</div>
                    <input type="text" id="folderName" class="modal-input" placeholder="Enter folder name" autofocus>
                    <div class="modal-actions">
                        <button class="modal-btn modal-cancel" onclick="hideModal('createFolderModal')">Cancel</button>
                        <button class="modal-btn modal-confirm" onclick="createFolder()">Create</button>
                    </div>
                </div>
            </div>

            <!-- Модальное окно для переименования -->
            <div id="renameModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">✏️ Rename</div>
                    <input type="text" id="newFileName" class="modal-input" placeholder="Enter new name" autofocus>
                    <div class="modal-actions">
                        <button class="modal-btn modal-cancel" onclick="hideModal('renameModal')">Cancel</button>
                        <button class="modal-btn modal-confirm" onclick="performRename()">Rename</button>
                    </div>
                </div>
            </div>
            
            <script>
                let selectedFiles = [];
                let currentRenamePath = '';

                function getSelectedFiles() {{
                    const checkboxes = document.querySelectorAll('.file-checkbox:checked');
                    return Array.from(checkboxes).map(cb => cb.dataset.path);
                }}
                
                function toggleAll(source) {{
                    const checkboxes = document.querySelectorAll('.file-checkbox');
                    checkboxes.forEach(cb => cb.checked = source.checked);
                }}
                
                function goHome() {{
                    location.href = '/';
                }}
                
                function goBack() {{
                    const currentDir = '{current_dir}';
                    const parentDir = currentDir.split('/').slice(0, -1).join('/');
                    if (parentDir && parentDir !== '') {{
                        location.href = '?dir=' + encodeURIComponent(parentDir);
                    }} else {{
                        location.href = '/';
                    }}
                }}
                
                function logout() {{
                    document.cookie = 'filemanager_auth=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/';
                    location.reload();
                }}

                function showModal(modalType) {{
                    const modals = {{
                        'createFile': 'createFileModal',
                        'createFolder': 'createFolderModal',
                        'rename': 'renameModal'
                    }};
                    document.getElementById(modals[modalType]).style.display = 'block';
                }}

                function hideModal(modalId) {{
                    document.getElementById(modalId).style.display = 'none';
                }}

                function createFile() {{
                    const name = document.getElementById('fileName').value.trim();
                    if (name) {{
                        const form = document.createElement('form');
                        form.method = 'post';
                        form.innerHTML = `
                            <input type="hidden" name="action" value="create_file">
                            <input type="hidden" name="name" value="${{name}}">
                            <input type="hidden" name="current_dir" value="{current_dir}">
                        `;
                        document.body.appendChild(form);
                        form.submit();
                    }}
                    hideModal('createFileModal');
                }}

                function createFolder() {{
                    const name = document.getElementById('folderName').value.trim();
                    if (name) {{
                        const form = document.createElement('form');
                        form.method = 'post';
                        form.innerHTML = `
                            <input type="hidden" name="action" value="create_folder">
                            <input type="hidden" name="name" value="${{name}}">
                            <input type="hidden" name="current_dir" value="{current_dir}">
                        `;
                        document.body.appendChild(form);
                        form.submit();
                    }}
                    hideModal('createFolderModal');
                }}

                function renameFile() {{
                    const files = getSelectedFiles();
                    if (files.length === 1) {{
                        currentRenamePath = files[0];
                        const currentName = currentRenamePath.split('/').pop();
                        document.getElementById('newFileName').value = currentName;
                        showModal('rename');
                    }} else alert('Please select exactly one file or folder to rename.');
                }}

                function performRename() {{
                    const newName = document.getElementById('newFileName').value.trim();
                    if (newName && currentRenamePath) {{
                        const form = document.createElement('form');
                        form.method = 'post';
                        form.innerHTML = `
                            <input type="hidden" name="action" value="rename">
                            <input type="hidden" name="path" value="${{currentRenamePath}}">
                            <input type="hidden" name="new_name" value="${{newName}}">
                        `;
                        document.body.appendChild(form);
                        form.submit();
                    }}
                    hideModal('renameModal');
                }}
                
                function deleteFiles() {{
                    const files = getSelectedFiles();
                    if (files.length > 0 && confirm('Are you sure you want to delete selected items?')) {{
                        const form = document.createElement('form');
                        form.method = 'post';
                        files.forEach(path => {{
                            form.innerHTML += `
                                <input type="hidden" name="action" value="delete">
                                <input type="hidden" name="path" value="${{path}}">
                            `;
                        }});
                        document.body.appendChild(form);
                        form.submit();
                    }}
                }}
                
                function cloneFiles() {{
                    const files = getSelectedFiles();
                    if (files.length > 0) {{
                        const form = document.createElement('form');
                        form.method = 'post';
                        files.forEach(path => {{
                            form.innerHTML += `
                                <input type="hidden" name="action" value="clone">
                                <input type="hidden" name="path" value="${{path}}">
                            `;
                        }});
                        document.body.appendChild(form);
                        form.submit();
                    }}
                }}
                
                function uploadFile() {{
                    const input = document.createElement('input');
                    input.type = 'file';
                    input.multiple = true;
                    input.onchange = function() {{
                        const form = new FormData();
                        form.append('action', 'upload');
                        form.append('current_dir', '{current_dir}');
                        for (let file of input.files) {{
                            form.append('files', file);
                        }}
                        fetch('', {{ method: 'POST', body: form }}).then(() => location.reload());
                    }};
                    input.click();
                }}

                // Закрытие модальных окон при клике вне их
                window.onclick = function(event) {{
                    if (event.target.classList.contains('modal')) {{
                        event.target.style.display = 'none';
                    }}
                }}

                // Обработка Enter в модальных окнах
                document.addEventListener('keydown', function(event) {{
                    if (event.key === 'Enter') {{
                        if (document.getElementById('createFileModal').style.display === 'block') {{
                            createFile();
                        }} else if (document.getElementById('createFolderModal').style.display === 'block') {{
                            createFolder();
                        }} else if (document.getElementById('renameModal').style.display === 'block') {{
                            performRename();
                        }}
                    }} else if (event.key === 'Escape') {{
                        hideModal('createFileModal');
                        hideModal('createFolderModal');
                        hideModal('renameModal');
                    }}
                }});
            </script>
        </body>
        </html>
        """
    
    def format_size(self, size):
        """Форматирует размер файла"""
        if size == 0:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def show_editor(self, file_path):
        """Показывает редактор файла"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            content = ""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Editing: {os.path.basename(file_path)}</title>
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: #1a202c;
                    margin: 0;
                    padding: 20px;
                    color: #e2e8f0;
                }}
                .editor-container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: #2d3748;
                    border-radius: 10px;
                    box-shadow: 0 2px 20px rgba(0,0,0,0.3);
                    overflow: hidden;
                }}
                .editor-header {{
                    background: #4a5568;
                    color: white;
                    padding: 25px;
                }}
                .editor-header h2 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .editor-content {{
                    padding: 25px;
                }}
                textarea {{
                    width: 100%;
                    height: 700px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 14px;
                    padding: 20px;
                    background: #1a202c;
                    color: #e2e8f0;
                    border: 2px solid #4a5568;
                    border-radius: 8px;
                    resize: vertical;
                    line-height: 1.5;
                }}
                .editor-actions {{
                    margin-top: 25px;
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                }}
                .editor-actions button {{
                    padding: 15px 30px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: 600;
                    min-width: 160px;
                    transition: all 0.3s;
                }}
                .btn-save {{ 
                    background: #48bb78; 
                    color: white; 
                }}
                .btn-cancel {{ 
                    background: #718096; 
                    color: white; 
                }}
                .btn-save:hover {{ 
                    background: #38a169;
                    transform: translateY(-2px);
                }}
                .btn-cancel:hover {{ 
                    background: #5a6268;
                    transform: translateY(-2px);
                }}
            </style>
        </head>
        <body>
            <div class="editor-container">
                <div class="editor-header">
                    <h2>✏️ Editing: {html.escape(os.path.basename(file_path))}</h2>
                </div>
                <div class="editor-content">
                    <form method="post">
                        <textarea name="content" placeholder="File content...">{html.escape(content)}</textarea>
                        <div class="editor-actions">
                            <input type="hidden" name="action" value="save">
                            <input type="hidden" name="path" value="{file_path}">
                            <button type="submit" class="btn-save">💾 Save Changes</button>
                            <button type="button" class="btn-cancel" onclick="history.back()">❌ Cancel</button>
                        </div>
                    </form>
                </div>
            </div>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def serve_file_preview(self, file_path):
        """Показывает файл для просмотра"""
        if not os.path.isfile(file_path):
            self.send_error(404, "File not found")
            return
        
        # Определяем MIME тип
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")
    
    def do_GET(self):
        """Обрабатывает GET запросы"""
        # Проверяем авторизацию
        if not self.check_auth():
            self.send_auth_form()
            return
        
        # Обрабатываем пути
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        
        if 'dir' in query:
            # Показываем директорию
            current_dir = query['dir'][0]
            # Защита от выхода за пределы корневой директории
            root_dir = os.getcwd()
            if not os.path.abspath(current_dir).startswith(root_dir):
                current_dir = root_dir
            self.send_file_manager(current_dir)
        elif 'view' in query:
            # Показываем редактор файла
            self.show_editor(query['view'][0])
        elif 'preview' in query:
            # Показываем файл для просмотра
            self.serve_file_preview(query['preview'][0])
        elif parsed.path == '/':
            # Корневая директория (где запущен скрипт)
            current_dir = os.getcwd()
            self.send_file_manager(current_dir)
        else:
            # Статические файлы
            file_path = parsed.path[1:]  # Убираем первый слеш
            if os.path.isfile(file_path):
                self.serve_file_preview(file_path)
            else:
                self.send_error(404, "File not found")
    
    def do_POST(self):
        """Обрабатывает POST запросы"""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        post_params = urllib.parse.parse_qs(post_data)
        
        # Проверка пароля
        if 'password' in post_params:
            password = post_params['password'][0]
            if password == self.PASSWORD:
                self.send_response(302)
                self.send_header('Location', '/')
                self.send_header('Set-Cookie', f'filemanager_auth={self.PASSWORD}; Path=/')
                self.end_headers()
                return
            else:
                self.send_auth_form()
                return
        
        # Проверяем авторизацию для других действий
        if not self.check_auth():
            self.send_auth_form()
            return
        
        action = post_params.get('action', [''])[0]
        self.handle_file_actions(action, post_params)
    
    def handle_file_actions(self, action, params):
        """Обрабатывает действия с файлами"""
        try:
            current_dir = params.get('current_dir', [os.getcwd()])[0]
            
            if action == 'create_file':
                name = params.get('name', [''])[0]
                file_path = os.path.join(current_dir, name)
                with open(file_path, 'w') as f:
                    f.write('')
            
            elif action == 'create_folder':
                name = params.get('name', [''])[0]
                folder_path = os.path.join(current_dir, name)
                os.makedirs(folder_path, exist_ok=True)
            
            elif action == 'rename':
                path = params.get('path', [''])[0]
                new_name = params.get('new_name', [''])[0]
                new_path = os.path.join(os.path.dirname(path), new_name)
                os.rename(path, new_path)
            
            elif action == 'delete':
                paths = params.get('path', [])
                for path in paths:
                    if os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
            
            elif action == 'clone':
                paths = params.get('path', [])
                for path in paths:
                    if os.path.isdir(path):
                        new_path = path + '_copy'
                        import shutil
                        shutil.copytree(path, new_path)
                    else:
                        new_path = path + '_copy'
                        with open(path, 'rb') as fsrc, open(new_path, 'wb') as fdst:
                            fdst.write(fsrc.read())
            
            elif action == 'save':
                path = params.get('path', [''])[0]
                content = params.get('content', [''])[0]
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            # Перенаправляем обратно
            self.send_response(302)
            self.send_header('Location', f'?dir={urllib.parse.quote(current_dir)}')
            self.end_headers()
            
        except Exception as e:
            self.send_error(500, f"Error: {str(e)}")

def is_port_in_use(host, port):
    """Проверяет, занят ли порт"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return False
        except OSError:
            return True

def main():
    host = 'YOU IP SERVER'
    start_port = 3000 
    
    print(f"🔍 Поиск свободного порта на {host}...")
    
    for port in range(start_port, start_port + 50):
        if not is_port_in_use(host, port):
            print(f"✅ Порт {port} свободен")
            print(f"🚀 Запуск файлового менеджера на http://{host}:{port}")
            print(f"🔐 Пароль: pass123")
            print(f"📁 Корневая директория: {os.getcwd()}")
            
            with socketserver.TCPServer((host, port), FileManagerHandler) as httpd:
                print(f"✅ Сервер запущен!")
                print("⏹️  Ctrl+C для остановки")
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\n🛑 Сервер остановлен")
            return
        else:
            print(f"❌ Порт {port} занят")
    
    print(f"🚫 Все порты заняты!")

if __name__ == "__main__":
    main()
