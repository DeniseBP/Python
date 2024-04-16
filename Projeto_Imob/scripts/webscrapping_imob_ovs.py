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
    imoveis = soup.find_all('a')

    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')

        for imovel in imoveis:
            img_tag = imovel.find('img')
            if img_tag:
                url_imagem = img_tag['src']
                if not url_imagem.startswith('/'):
                    localizacao_element = imovel.find_next('h2')
                    descricao_element = imovel.find_next('h3')

                    # Obter somente o texto contido nos elementos acima. O método get_text() é usado para extrair o texto de uma tag HTML. O argumento strip=True remove espaços em branco no início e no final do texto
                    localizacao = localizacao_element.get_text(
                        strip=True) if localizacao_element else "N/A"
                    # Aqui tb estamos tirando as quebras de linha com o replace('\n', ''))
                    descricao = (descricao_element.get_text(strip=True).replace(
                        '\n', '')) if descricao_element else "N/A"

                    # Obter Link do imovel
                    # Trazer parte codigo html que contém parte do link do imovel
                    link_imovel_tag = imovel.find_next('a')
                    # Expressão regular para encontrar texto entre aspas
                    padrao = r'"([^"]*)"'
                    # Encontrar todas as correspondências na string usando a expressão regular
                    correspondencias = re.findall(padrao, str(link_imovel_tag))
                    # O primeiro item da lista corresponde ao texto entre aspas
                    link_imovel = 'http://www.ovsimoveis.com.br' + \
                        correspondencias[0] if correspondencias else "N/A"

                    # Dividir a localização em quatro partes: Tipo, Negocio, Bairro/Cidade e Preço
                    # Verificando quantas vezes 'para' aparece na localizacao
                    ocorrencias_para = localizacao.count("para")

                    if ocorrencias_para == 1:
                        # Se 'para' aparece apenas uma vez, faça o split normalmente
                        partes = localizacao.split("para")
                    else:
                        # Se 'para' aparece mais de uma vez, faça o split pela última posição
                        ultima_posicao_para = localizacao.rfind("para")
                        partes = [localizacao[:ultima_posicao_para],
                                  localizacao[ultima_posicao_para + len("para"):]]

                    tipo = partes[0].strip()

                    # encontrando Negocio
                    index_negocio = partes[1].strip()

                    if 'Venda' in index_negocio[0:5]:
                        negocio = index_negocio[0:5].strip()
                    else:
                        negocio = index_negocio[0:7].strip()

                    # dividindo Bairro/Cidade e Preço
                    bairro_cidade_preco = partes[1].split(negocio)[1].strip()

                    if 'Consulte' in bairro_cidade_preco:
                        bairro_cidade = bairro_cidade_preco.split('Consulte')[
                            0].strip()
                        preco = 'Consulte'
                    elif 'R$' in bairro_cidade_preco:
                        bairro_cidade = bairro_cidade_preco.split('R$')[
                            0].strip()
                        preco = 'R$' + \
                            bairro_cidade_preco.split('R$')[1].strip()
                    else:
                        bairro_cidade = bairro_cidade_preco.strip()
                        preco = "N/A"

                    # dividindo Bairro/Cidade
                    ocorrencias_traco = bairro_cidade.count("-")

                    if ocorrencias_traco == 1:
                        # Se '-' aparece apenas uma vez, faça o split normalmente
                        partes = bairro_cidade.split("-")
                        cidade = partes[0].strip()
                        # ajuste para extrair somente o texto antes da /. Ex: Cataguases / MG, irá extrair Cataguases
                        padrao = r'^([^/]+)'
                        resultado = re.match(padrao, cidade)
                        cidade = resultado.group(1).strip()

                        bairro = partes[1].strip()
                    else:
                        # Se '-' não aparece
                        cidade = bairro_cidade
                        # ajuste para extrair somente o texto antes da /. Ex: Cataguases / MG, irá extrair Cataguases
                        padrao = r'^([^/]+)'
                        resultado = re.match(padrao, cidade)
                        cidade = resultado.group(1).strip()

                        bairro = "N/A"

                    csv_writer.writerow(
                        [tipo, negocio, cidade, bairro, preco, descricao, url_imagem, link_imovel])

                    # Imprimir informações do imóvel
                    print("Negocio:", negocio)
                    print("Tipo:", tipo)
                    print("Cidade:", cidade)
                    print("Bairro:", bairro)
                    print("Preco:", preco)
                    print("Descricao:", descricao)
                    print("URL da imagem:", url_imagem)
                    print("Link do imovel:", link_imovel)
                    print("-" * 50)


# URLs para os diferentes tipos de finalidade e número de páginas para iterar
urls = {
    'venda': ('http://www.ovsimoveis.com.br/imovel/?finalidade=venda&tipo=&bairro=0&suites=&banheiros=&vagas=&dormitorios='),
    'locacao': ('http://www.ovsimoveis.com.br/imovel/?finalidade=locacao&tipo=&bairro=0&suites=&banheiros=&vagas=&dormitorios=')
}

# Nome do arquivo CSV
nome_arquivo = 'imoveis_dados_ovs.csv'

# Limpar o arquivo antes de começar a escrever
arquivo_csv = 'C:\\Users\\Camila\\Desktop\\DENISE\\Projeto_Imob\\'+ nome_arquivo
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

