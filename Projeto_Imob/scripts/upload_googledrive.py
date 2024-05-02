from google.oauth2 import service_account  # pip install --upgrade google-auth
# pip install google-api-python-client
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Caminho do arquivo JSON de credenciais --- alterar caminh se trocar de máquina
CRED_JSON_PATH = 'C:\\Users\\denis\\OneDrive\\Documentos\\Projeto_Imob\\projeto-imob-419818-e75892643c3f.json'

# Configurar credenciais de serviço globalmente
credentials = service_account.Credentials.from_service_account_file(
    CRED_JSON_PATH,
    scopes=['https://www.googleapis.com/auth/drive'])

# Construir serviço do Google Drive globalmente
drive_service = build('drive', 'v3', credentials=credentials)

# Função para upload do arquivo para o Google Drive


def upload_arquivo_para_drive(nome_arquivo, arquivo_csv, id_pasta):
    global drive_service

    # Verificar se o arquivo já existe no Google Drive
    file_list = drive_service.files().list(q=f"name='{nome_arquivo}' and parents in '{id_pasta}' and trashed=false",
                                           fields='files(id)').execute()
    existing_files = file_list.get('files', [])

    if existing_files:
        # Se o arquivo já existir, atualize seu conteúdo
        file_id = existing_files[0]['id']
        media = MediaFileUpload(arquivo_csv, mimetype='text/csv')
        updated_file = drive_service.files().update(
            fileId=file_id, media_body=media).execute()
        print('Arquivo atualizado no Google Drive com o ID:',
              updated_file.get('id'))
        print("-" * 50)
    else:
        # Se o arquivo não existir, crie um novo arquivo no Google Drive
        file_metadata = {
            'name': nome_arquivo,
            'parents': [id_pasta]
        }
        media = MediaFileUpload(arquivo_csv, mimetype='text/csv')
        uploaded_file = drive_service.files().create(
            body=file_metadata, media_body=media, fields='id').execute()
        print('Arquivo enviado para o Google Drive com o ID:',
              uploaded_file.get('id'))
        print("-" * 50)
