import csv
import re  # biblioteca expressoes regulares
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import requests
from bs4 import BeautifulSoup

# Função para extrair o numero de páginas a iterar

def obter_numero_de_paginas(url):

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    site = requests.get(url, headers=headers)
    soup = BeautifulSoup(site.text, 'html.parser')

    # Encontrar o elemento de paginação
    paginacao_element = soup.find_all('a', class_='lipagina-btn-paginacao')
    ultima_pagina = paginacao_element[-2].get_text()

    # Se a última página for "...", continuamos buscando até encontrar a página correta
    while ultima_pagina == "...":
        # Atualizamos a variável paginacao_element com o novo valor da página
        paginacao_element = soup.find_all('a', class_='lipagina-btn-paginacao')
        ultima_pagina = paginacao_element[-3].get_text()
        url_pag_len = f'{url}&pag={ultima_pagina}'
        site = requests.get(url_pag_len, headers=headers)
        soup = BeautifulSoup(site.text, 'html.parser')
        ultima_pagina = paginacao_element[-2].get_text()

    # Retornamos o número da última página
    return int(ultima_pagina)


# Função para extrair dados de uma página e escrever no arquivo CSV
def extrair_e_escrever_dados(url, arquivo):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    site = requests.get(url, headers=headers)
    soup = BeautifulSoup(site.text, 'html.parser')
    imoveis = soup.find_all('div', class_='imoveis_listar')

    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')

        for imovel in imoveis:
            negocio = "Venda" if 'finalidade=venda' in url else "Locação"
            bairro_cidade_element = imovel.find('h2')
            preco_element = imovel.find(
                'div', class_='li_ftcor valor')
            # Verificar se a descrição está vazia, se estiver, tentar buscar de outro elemento para reduzirmos ao maximo a qtd de N/A
            descricao_element = imovel.find('div', class_='descricao')
            if descricao_element is None or descricao_element.text.strip() == "":
                descricao_element = imovel.find_all('div', class_='itens')
            # Ajuste descrição
            # Inicializa uma lista para armazenar os textos dos elementos descrição
            textos = []
            # Itera sobre a lista de elementos e armazena o texto de cada um na lista
            for elemento in descricao_element:
                textos.append(elemento.text)
            # Junta os textos em uma única string, separados por '/'
            descricao = ' / '.join(textos) if descricao_element else "N/A"
            
            # Obter somente o texto contido nos elementos acima. O método get_text() é usado para extrair o texto de uma tag HTML. O argumento strip=True remove espaços em branco no início e no final do texto
            preco = preco_element.get_text(
                strip=True) if preco_element else "N/A"
            bairro_cidade = bairro_cidade_element.get_text(
                strip=True) if bairro_cidade_element else "N/A"

            # Separar Cidade e Bairro
            cidade = bairro_cidade.split(
                ",")[1].strip() if ',' in bairro_cidade else "N/A"
            # ajuste para extrair somente o texto antes da /. Ex: Cataguases / MG, irá extrair Cataguases
            padrao = r'^([^/]+)'
            resultado = re.match(padrao, cidade)
            cidade = resultado.group(1).strip()

            bairro = bairro_cidade.split(
                ",")[0].strip() if ',' in bairro_cidade else bairro_cidade.strip()

            # Obter Link do imovel e url imagem
            # Trazer codigo html que contém os links desejados
            urls_imovel_tag = imovel.find_next('a')
            # Expressão regular para encontrar texto entre aspas
            padrao = r'"([^"]*)"'
            # Encontrar todas as correspondências na string usando a expressão regular
            correspondencias = re.findall(padrao, str(urls_imovel_tag))
            # ultimo_texto_entre_aspas
            url_imagem = correspondencias[-2] if correspondencias else "N/A"
            # segundo_texto_entre_aspas
            link_imovel = 'http://www.imobiliariaavenida.com' + \
                correspondencias[0] if correspondencias else "N/A"
            tipo = correspondencias[1].split(
                "para")[0].strip() if correspondencias else "N/A"

            csv_writer.writerow(
                [tipo, negocio, cidade, bairro, preco, descricao, url_imagem, link_imovel])

            print("Tipo:", tipo)
            print("Negocio:", negocio)
            print("Cidade:", cidade)
            print("Bairro:", bairro)
            print("Preco:", preco)
            print("Descricao:", descricao)
            print("URL da imagem:", url_imagem)
            print("Link do imovel:", link_imovel)
            print("-" * 50)


# URLs para os diferentes tipos de finalidade e número de páginas para iterar
urls = {
    'venda': ('http://www.imobiliariaavenida.com/imovel/?finalidade=venda&tipo=&bairro=0&sui=&ban=&gar=&dor='),

    'locacao': ('http://www.imobiliariaavenida.com/imovel/?finalidade=locacao&tipo=&bairro=0&sui=&ban=&gar=&dor=')

}

# Nome do arquivo CSV
nome_arquivo = 'imoveis_dados_avenida.csv'

# Limpar o arquivo antes de começar a escrever
arquivo_csv = 'C:\\Users\\Camila\\Desktop\\DENISE\\Projeto_Imob\\imoveis_dados_avenida.csv'
open(arquivo_csv, 'w').close()

# Escrever cabeçalho
with open(arquivo_csv, 'a', newline='', encoding='UTF-8') as f:
    f.write('Tipo;Negocio;Cidade;Bairro;Preco;Descricao;UrlImagem;LinkImovel\n')

# Iterar sobre as URLs e extrair e escrever os dados no arquivo CSV
for finalidade, url in urls.items():
    print(f'Extraindo dados para a finalidade: {finalidade}')
    # Obter o número de páginas para a URL atual
    num_paginas = obter_numero_de_paginas(url)
    for i in range(1, num_paginas + 1):
        url_pag = f'{url}&pag={i}'
        print(f'Extraindo dados da página {i} de {finalidade}')
        # Extrair e escrever os dados da página atual
        extrair_e_escrever_dados(url_pag, arquivo_csv)

print('Extração de dados concluída!')
print("-" * 50)

# Upload do arquivo para o Google Drive
# Configurar credenciais de serviço
credentials = service_account.Credentials.from_service_account_file(
    'C:\\Users\\Camila\\Desktop\\DENISE\\Projeto_Imob\\projeto-imob-419818-e75892643c3f.json',
    scopes=['https://www.googleapis.com/auth/drive'])

# Construir serviço do Google Drive
drive_service = build('drive', 'v3', credentials=credentials)

# Especificar ID da pasta do Google Drive
id_pasta = '14NUG9dF7HE_E5f-vxKtIzXz9jjX9e6Y7'

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
    print('Arquivo atualizado no Google Drive com o ID:', updated_file.get('id'))
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
    print('Arquivo enviado para o Google Drive com o ID:', uploaded_file.get('id'))
    print("-" * 50)
