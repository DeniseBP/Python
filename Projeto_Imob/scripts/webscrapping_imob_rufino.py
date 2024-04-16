
import csv
import time
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
    # Inicializar o navegador do Selenium com as opções acima configuradas
    # driver = webdriver.Chrome(options=options)
    navegador.get(url)
    # Aguarde para garantir que a página seja totalmente carregada
    # time.sleep(2)
    # Encontrar o elemento de paginação
    paginacao_element = navegador.find_elements(By.CSS_SELECTOR, 'h3')
    if paginacao_element:
        ultima_pagina = paginacao_element[-1].text.strip()
        # Verificar se a última página é um número válido
        if ultima_pagina.isdigit():
            return int(ultima_pagina)
        else:
            print("O número de páginas não pôde ser obtido. Usando valor padrão.")
            return 30  # Valor padrão
    else:
        print("Elementos de paginação não encontrados. Usando valor padrão.")
        return 30  # Valor padrão


def extrair_e_escrever_dados(url, arquivo):
    # Criar uma nova instância do driver para cada pagina
    # navegador = webdriver.Chrome(options=options)
    # Limpar o cache do navegador
    # navegador.delete_all_cookies()
    navegador.get(url)
    # Aguarde para garantir que a página seja totalmente carregada
    time.sleep(5)
    # Encontrar todos os elementos de imóveis
    imoveis = navegador.find_elements(
        By.CSS_SELECTOR, 'mat-card.mat-card.mat-focus-indicator.ng-star-inserted')

    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')
        # Iterar sobre os elementos de imóveis
        for imovel in imoveis:
            # Extrair informações do imóvel
            def get_element_text(imovel, css_selector):
                try:
                    element = imovel.find_element(By.CSS_SELECTOR, css_selector)
                    return element.text.strip()
                except NoSuchElementException:
                    return "N/A"

            negocio = "Venda" if 'availability=buy' in url else "Locação"
       
            tipo_element = get_element_text(imovel, 'mat-card-title.mat-card-title.h3.color-title.bold')
            bairro_cidade_element = get_element_text(imovel, 'mat-card-subtitle.mat-card-subtitle.h5.color-title')
            descricao_element = get_element_text(imovel, 'mat-card-subtitle.mat-card-subtitle.h4.color-subtitle')
            
            preco_element = imovel.find_element(
                By.CSS_SELECTOR, 'mat-card-subtitle.mat-card-subtitle.h3.color-title.bold')
            link_imovel_element = imovel.find_element(
                By.CSS_SELECTOR, 'div > a')  # sempre que for uma tag filha podemos utilizar o sinal >
            url_imagem_element = imovel.find_element(
                By.CSS_SELECTOR, '.swiper-slide.swiper-slide-duplicate-active').find_element(
                By.TAG_NAME, 'img')

            # dividindo tipo e bairro_cidade
            ocorrencias_em = tipo_element.count("em")
            ocorrencias_traco = tipo_element.count("-")

            if ocorrencias_em == 1:
                # Se 'em' aparece, faça o split normalmente
                partes = tipo_element.split("em")
                if partes[0].strip() != "":
                    # Se a primeira parte do split não estiver vazia, usamos ela como tipo
                    tipo = partes[0].strip()
                else:
                    # Se a primeira parte estiver vazia, usamos a descrição como tipo e obtemos as duas primeiras palavras
                    # o JOIN unifica as duas primeiras palavras em uma única string
                    tipo = ' '.join(descricao_element.split()[:2])

                if ocorrencias_traco == 1:
                    # Se '-' aparece, faça o split em partes[1]
                    cidade = (partes[1].split("-"))[1].strip()
                    bairro = (partes[1].split("-"))[0].strip()
                else:
                    # Se '-' não aparece, pegue o elemento bairro_cidade e faça split nele
                    cidade = (bairro_cidade_element.split("-")
                              )[0].strip() if bairro_cidade_element else "NA"
                    bairro = (bairro_cidade_element.split("-")
                              )[0].strip() if bairro_cidade_element else "NA"
            else:
                # Se 'em' não aparece:
                tipo = tipo_element.split()[0].strip()
                # Se '-' aparece, faça o split normalmente
                cidade = (bairro_cidade_element.split("-")
                          )[0].strip() if bairro_cidade_element else "NA"
                bairro = (bairro_cidade_element.split("-")
                          )[0].strip() if bairro_cidade_element else "NA"

            # Obter somente o texto contido nos elementos acima
            preco = preco_element.text.strip() if preco_element else "NA"
            descricao = descricao_element if descricao_element else "N/A"
            link_imovel = link_imovel_element.get_attribute(
                'href') if link_imovel_element else "N/A"
            url_imagem = url_imagem_element.get_attribute(
                'src') if url_imagem_element else "N/A"

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
    'venda': ('https://www.rufino.imb.br/buscar?order=most_relevant&direction=desc&availability=buy'),
    'locacao': ('https://www.rufino.imb.br/buscar?order=most_relevant&direction=desc&availability=rent')
}

# Nome do arquivo CSV
nome_arquivo = 'imoveis_dados_rufino.csv'

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
        url_pag = f'{url}&page={i}'
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
