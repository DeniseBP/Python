import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


# Configurações do Selenium
options = Options()
# configuração do tamanho da tela do navegador
# options.add_argument('window-size=1366,768')
options.add_argument("--start-maximized")
# Rodar o navegador sem interface gráfica
options.add_argument("--headless")

# Inicializar o driver do Selenium com as opções configuradas
driver = webdriver.Chrome(options=options)
# driver = webdriver.Chrome(service=service, options=options)

def extrair_e_escrever_dados(url, arquivo):
    try:
        driver.get(url)
        # Aguarde para garantir que a página seja totalmente carregada
        time.sleep(3)

        # Defina a posição inicial do botão
        posicao_botao = 40
        # Defina a última posição do botão
        ultima_posicao = 580

        # Loop para clicar no botão várias vezes
        while posicao_botao <= ultima_posicao:
            try:
                # Encontre e clique no botão
                botao = driver.find_elements(By.TAG_NAME, 'button')[
                    posicao_botao]
                # Role a página para que o botão seja visível
                driver.execute_script(
                    "arguments[0].scrollIntoView(true);", botao)
                # Aguarde um segundo para a rolagem da página
                time.sleep(2)
                botao.click()
                # print(f"Clicado no botão na posição {posicao_botao}")
                # Aguarde um pouco para a página carregar após o clique
                time.sleep(2)
                # Atualize a posição do botão
                posicao_botao += 36  # Adicione 36 à posição atual, número obtivo com analise prévia do site
            except Exception as e:
                print(
                    f"Erro ao clicar no botão na posição {posicao_botao}: {e}")
                break  # Saia do loop em caso de erro

    finally:

        imoveis = driver.find_elements(
            By.CSS_SELECTOR, 'div.card.card-listing')

        with open(arquivo, 'a', newline='', encoding='utf-8') as f:
            csv_writer = csv.writer(f, delimiter=';')
            
            # Iterar sobre os elementos de imóveis
            for imovel in imoveis:
                
                negocio = "Venda" if 'a-venda' in url else "Locação"
                
                tipo_element = imovel.find_element(
                    By.CSS_SELECTOR, 'h3.card-text').text.strip()
                descricao_element = imovel.find_element(
                    By.CSS_SELECTOR, 'p.description.hidden-sm-down')
                bairro_element = imovel.find_element(
                    By.CSS_SELECTOR, 'h2.card-title')
                link_imovel_element = imovel.find_element(
                    By.XPATH, './/a[contains(@href,"/imovel/")]')
                url_imagem_element = imovel.find_element(
                    By.XPATH, './/div[@class="info-thumb"]/img')
                
                # Obter somente o texto contido nos elementos acima e tratar posiveis valores vazios com o if
                descricao = descricao_element.text.strip() if descricao_element else "N/A"
                bairro = bairro_element.text.strip() if bairro_element else "NA"
                link_imovel = link_imovel_element.get_attribute(
                    'href') if link_imovel_element else "N/A"
                url_imagem = url_imagem_element.get_attribute(
                    "src") if url_imagem_element else "N/A"
                
                # Obter o preço tratando os casos em que existe preço de aluguel e venda juntos, no mesmo imóvel, com mesmos atributos
                # Lista para armazenar os preços
                precos = []
                # Encontrar todos os elementos que correspondem à seleção CSS
                elementos_preco = imovel.find_elements(By.CSS_SELECTOR, 'span.h-money.location')
                # Para cada elemento encontrado, armazenar o preço na lista
                for elemento in elementos_preco:
                    preco_texto = elemento.text.strip()
                    # Tratamento para remover a unidade de medida (caso exista).Ex: R$ 1.500/mês, deixar somente o valor R$ 1.500
                    preco = preco_texto.split("/")[0].strip() if '/' in preco_texto else preco_texto.strip()
                    # Remover o símbolo da moeda e quaisquer caracteres não numéricos
                    try:
                        preco_numerico = int(''.join(filter(str.isdigit, preco)))
                        precos.append(preco_numerico)
                    except ValueError:
                        precos.append(preco)
                if len(precos) > 1:
                    # Se for para venda, pegue o maior preço
                    if negocio == 'Venda':
                        preco_final = max(precos)
                    # Se for para locação, pegue o menor preço
                    elif negocio == 'Locação':
                        preco_final = min(precos)
                    else:
                        preco_final = None  # Lidar com outros tipos de negócio, se necessário
                # Se não houver valores numéricos na lista de preços
                else:
                    preco_final = preco  # Ou qualquer outra ação adequada quando não há valores numéricos

                # Ajuste no tipo: split na palavra "em" e obter a primeira parte
                tipo = tipo_element.split("em")[0].strip() if 'em' in tipo_element else tipo_element.strip()

                # Ajuste no tipo para obter a cidade: split na palavra "em" e pegar a segunda parte
                cidade = tipo_element.split("em")[1].strip() if 'em' in tipo_element else "NA"

                csv_writer.writerow(
                    [tipo, negocio, cidade, bairro, preco_final, descricao, url_imagem, link_imovel])

                print("Negócio:", negocio)
                print("Tipo:", tipo)
                print("Cidade:", cidade)
                print("Bairro:", bairro)
                print("Preço:", preco_final)
                print("Descrição:", descricao)
                print("URL da imagem:", url_imagem)
                print("Link do imóvel:", link_imovel)
                print("-" * 50)


# URLs para os diferentes tipos de finalidade e número de páginas para iterar
urls = {
    'venda': ('https://www.escolhamonteiro.com.br/imoveis/a-venda'),
    'locacao': ('https://www.escolhamonteiro.com.br/imoveis/para-alugar')
}

# Nome do arquivo CSV
nome_arquivo = 'imoveis_dados_monteiro.csv'

# Limpar o arquivo antes de começar a escrever
arquivo_csv = 'C:\\Users\\Camila\\Desktop\\DENISE\\Projeto_Imob\\'+ nome_arquivo
open(arquivo_csv, 'w').close()

# Escrever cabeçalho
with open(arquivo_csv, 'a', newline='', encoding='UTF-8') as f:
    f.write('Tipo;Negocio;Cidade;Bairro;Preco;Descricao;UrlImagem;LinkImovel\n')

# Iterar sobre as URLs e extrair e escrever os dados no arquivo CSV
for finalidade, (url) in urls.items():
    print(f'Extraindo dados para a finalidade: {finalidade}')
    for i in range(1):
        url_pag = f'{url}'
        print(f'Extraindo dados da página de {finalidade}')
        extrair_e_escrever_dados(url_pag, arquivo_csv)

# Encerre o driver do Selenium
driver.quit()

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