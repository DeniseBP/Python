import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configurações do Selenium
options = Options()
# configuração do tamanho da tela do navegador
# options.add_argument('window-size=1366,768')
options.add_argument("--start-maximized")
# Rodar o navegador sem interface gráfica
# options.add_argument("--headless")

# Abrir o navegador que irá rodar a função def extrair_e_escrever_dados
navegador = webdriver.Chrome(options=options)


def obter_numero_de_paginas(url):
    # Inicializar o navegador
    navegador.get(url)
    # Aguarde para garantir que a página seja totalmente carregada
    time.sleep(5)
    # Encontrar o elemento de paginação
    paginacao_element = navegador.find_elements(
        By.CSS_SELECTOR, 'ul.pagination li:not(.previous):not(.next):not(.break) a[role="button"]')
    if paginacao_element:
        ultima_pagina = paginacao_element[-1].text.strip()
        # Verificar se a última página é um número válido
        if ultima_pagina.isdigit():
            return int(ultima_pagina)
        else:
            print("O número de páginas não pôde ser obtido. Usando valor padrão.")
            return 40  # Valor padrão
    else:
        print("Elementos de paginação não encontrados. Usando valor padrão.")
        return 40  # Valor padrão


def extrair_e_escrever_dados(url, arquivo):
    # Criar uma nova instância do driver para cada pagina
    navegador.get(url)
    # Aguarde para garantir que a página seja totalmente carregada
    time.sleep(5)
    # Encontrar todos os elementos de imóveis
    imoveis = navegador.find_elements(
        By.CSS_SELECTOR, 'a.chakra-linkbox.css-1kcv35j')

    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')

        # Iterar sobre os elementos de imóveis
        for imovel in imoveis:

            negocio = "Venda" if 'comprar?' in url else "Locação"
            
            tipo_element = imovel.find_element(
                By.CSS_SELECTOR, 'span.chakra-badge.css-1mliqn9').text.strip()
            bairro_element = imovel.find_element(
                By.CSS_SELECTOR, 'h2.chakra-heading.css-18i4k2w').text.strip()
            cidade_element = imovel.find_element(
                By.CSS_SELECTOR, 'p.chakra-text.css-uvhce0').text.strip()
            preco_element = imovel.find_element(
                By.CSS_SELECTOR, 'p.chakra-text.css-j1vyp6').text.strip()
            descricao_element = imovel.find_elements(
                By.CSS_SELECTOR, 'p.chakra-text.css-itvw0n')
            link_imovel_element = imovel.get_attribute(
                'href')
            # Obter url imagem com tratamento para casos de imovel sem imagem
            try:
                div_span_element = imovel.find_element(
                    By.CSS_SELECTOR, 'div > span')
                url_imagem_element = div_span_element.find_element(
                    By.TAG_NAME, 'img')
            except NoSuchElementException:
                url_imagem_element = "N/A"

            # Obter somente o texto contido nos elementos acima e tratar posiveis valores vazios com o if
            tipo = tipo_element if tipo_element else "N/A"
            bairro = bairro_element if bairro_element else "N/A"
            preco = preco_element if preco_element else "NA"
            link_imovel = link_imovel_element if link_imovel_element else "N/A"

            # Usando expressão regular para encontrar o texto desejado
            padrao = r'[^,]*,\s*([^,-]+?)\s*-\s*'
            resultado = re.search(padrao, cidade_element)

            # Verificar se a correspondência foi encontrada
            if resultado:
                # Extrair o texto desejado
                cidade = resultado.group(1).strip()
            else:
                # Se a correspondência não for encontrada, apenas use a cidade original
                cidade = cidade_element.strip()

            # Ajuste preço. Ex: R$ 1.500/mês, deixar somente o valor R$ 1.500
            preco = preco_element.split(
                "/")[0].strip() if '/' in preco_element else preco_element.strip()

            # Ajuste descrição
            # Inicializa uma lista para armazenar os textos dos elementos descrição
            textos = []
            # Itera sobre a lista de elementos e armazena o texto de cada um na lista
            for elemento in descricao_element:
                textos.append(elemento.text)
            # Junta os textos em uma única string, separados por '/'
            descricao = ' / '.join(textos) if descricao_element else "N/A"

            # Obter url imagem com tratamento para casos de imovel sem imagem
            try:
                url_imagem = url_imagem_element.get_attribute('src')
            except AttributeError:
                url_imagem = "N/A"

            csv_writer.writerow(
                [tipo, negocio, cidade, bairro, preco, descricao, url_imagem, link_imovel])

            # Imprimir informações do imóvel
            print("Negócio:", negocio)
            print("Tipo:", tipo)
            print("Cidade:", cidade)
            print("Bairro:", bairro)
            print("Preço:", preco)
            print("Descrição:", descricao)
            print("URL da imagem:", url_imagem)
            print("Link do imóvel:", link_imovel)
            print("-" * 50)


# URLs para os diferentes tipos de finalidade e número de páginas para iterar
urls = {
    'venda': ('https://www.mibimobiliaria.com.br/imoveis/comprar?'),
    'locacao': ('https://www.mibimobiliaria.com.br/imoveis/alugar?')
}

# Nome do arquivo CSV
nome_arquivo = 'imoveis_dados_mb.csv'

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
        url_pag = f'{url}&p={i}'
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