
import os

files = [
    'frontend/src/pages/VerifyEmailPage.jsx',
    'frontend/src/pages/PendingVerificationPage.jsx',
    'frontend/src/pages/Dashboard.jsx',
    'frontend/src/pages/ArenaPage.jsx',
    'frontend/src/components/AppLayout.jsx'
]

for file_path in files:
    full_path = os.path.join(os.getcwd(), file_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        new_content = content.replace('logo-premium.png', 'ufl-logo.png')
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file_path}")
    else:
        print(f"File not found: {file_path}")
