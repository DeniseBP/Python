import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
import pandas as pd

# Caminho do arquivo JSON de credenciais
CRED_JSON_PATH = 'C:\\Users\\denis\\OneDrive\\Documentos\\Projeto_Imob\\projeto-imob-419818-e75892643c3f.json'

# Configurar credenciais de serviço globalmente
credentials = service_account.Credentials.from_service_account_file(
    CRED_JSON_PATH,
    scopes=['https://www.googleapis.com/auth/drive'])

# Construir serviço do Google Drive globalmente
drive_service = build('drive', 'v3', credentials=credentials)

# ID da pasta específica do Google Drive
folder_id = '14NUG9dF7HE_E5f-vxKtIzXz9jjX9e6Y7'

# Função para listar os IDs e nomes dos arquivos na pasta


def list_file_ids_and_names_in_folder(service, folder_id):
    file_data = []
    page_token = None
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields='nextPageToken, files(id, name)',
            pageToken=page_token
        ).execute()

        for file in response.get('files', []):
            file_name = file.get('name')
            file_id = file.get('id')
            # Extrai a parte final do nome do arquivo
            file_name = (file_name.split('_')[-1]).split('.')[0]
            file_data.append({'File ID': file_id, 'File Name': file_name})
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return file_data


# Obtém os IDs e nomes dos arquivos na pasta especificada
file_data = list_file_ids_and_names_in_folder(drive_service, folder_id)

# Cria um DataFrame pandas com os IDs e nomes dos arquivos
df = pd.DataFrame(file_data)

# Exibe o DataFrame pandas com os IDs e nomes dos arquivos no Power BI Desktop
df
print(df)
