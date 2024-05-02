import os
import time
import csv
import datetime
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import upload_googledrive as gd_upload  # importando função genérica
import send_email  # importando função genérica


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


# Definir variáveis globais para armazenar o somatório da quantidade de imóveis para venda e locação
total_venda = 0
total_locacao = 0

# Função para carregar todos os imóveis (clicar btn "Ver mais")


def obter_numero_de_paginas(url):
    # Inicializar o navegador
    driver.get(url)
    # Aguarde para garantir que a página seja totalmente carregada
    time.sleep(5)
    # Verificar se o conteúdo HTML foi obtido com sucesso
    if not driver:
        # Lógica para lidar com a falha na obtenção do site
        print(f'Erro ao tentar abrir o navegador', None, None)
        registrar_log('Erro ao tentar abrir o navegador', None, None)
        sys.exit()  # Encerra o script se houver erro na obtenção do site

    # Defina a posição inicial do botão
    posicao_button = 40
    # Defina a última posição do botão
    ultima_posicao = 580

    # Loop para clicar no botão várias vezes
    while posicao_button <= ultima_posicao:
        try:
            # Encontre o botão
            button = driver.find_elements(By.TAG_NAME, 'button')[
                posicao_button]
            # Role a página para que o botão seja visível
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", button)
            # Aguarde para a rolagem da página
            time.sleep(7)
            # Espere até que o botão esteja visível na tela
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(button))
            # Se o botão estiver visível, clique nele
            button.click()
            print(f"Clicado no botão na posição {posicao_button}")
            # Aguarde um pouco para a página carregar após o clique
            time.sleep(8)
            # Atualize a posição do botão
            # Adicione 36 à posição atual, número obtivo com analise prévia do site
            posicao_button += 36
        except Exception as e:
            # Lógica para lidar com outros erros
            print(
                f"Erro ao clicar no botão na posição {posicao_button}: {e}")
            registrar_log(f'Erro ao clicar no botão na posição:{
                          posicao_button}: {e}', None, None)
            break  # Saia do loop em caso de erro e continue a rodar o script


# Função para registrar o log de execução


def registrar_log(pagina_executada, tipo_transacao, qtd_imoveis_por_pagina):
    data_atual = datetime.datetime.now()
    data_formatada = data_atual.strftime("%d/%m/%Y %H:%M:%S")
    nome_script = (os.path.basename(__file__).split("_")[2]).split(".")[0]

    log_info = f"{data_formatada} | {nome_script} | {
        pagina_executada} | {tipo_transacao} | {qtd_imoveis_por_pagina}\n"

    with open("log_execucao.txt", "a") as arquivo_log:
        arquivo_log.write(log_info)

# Função para extrair dados de uma página e escrever no arquivo CSV


def extrair_e_escrever_dados(url, arquivo, tipo_transacao, pagina_atual):
    global total_venda, total_locacao
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
            elementos_preco = imovel.find_elements(
                By.CSS_SELECTOR, 'span.h-money.location')
            # Para cada elemento encontrado, armazenar o preço na lista
            for elemento in elementos_preco:
                preco_texto = elemento.text.strip()
                # Tratamento para remover a unidade de medida (caso exista).Ex: R$ 1.500/mês, deixar somente o valor R$ 1.500
                preco = preco_texto.split(
                    "/")[0].strip() if '/' in preco_texto else preco_texto.strip()
                # Remover o símbolo da moeda e quaisquer caracteres não numéricos
                try:
                    preco_numerico = int(
                        ''.join(filter(str.isdigit, preco)))
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
            tipo = tipo_element.split("em")[0].strip(
            ) if 'em' in tipo_element else tipo_element.strip()

            # Ajuste no tipo para obter a cidade: split na palavra "em" e pegar a segunda parte
            cidade = tipo_element.split(
                "em")[1].strip() if 'em' in tipo_element else "NA"

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

        # Contar a quantidade de imóveis processados nesta página
        qtd_imoveis_pagina = len(imoveis)
        qtd_imoveis_por_pagina = f'{
            qtd_imoveis_pagina} imóveis encontrados'

        # Atualizar o somatório da quantidade de imóveis para venda ou locação
        if tipo_transacao == 'venda':
            total_venda += qtd_imoveis_pagina
        elif tipo_transacao == 'locacao':
            total_locacao += qtd_imoveis_pagina

        # Encontrar o numero da página que foi executada
        pagina_executada = f'page {pagina_atual}'
        # Registrar o log
        registrar_log(pagina_executada, tipo_transacao,
                      qtd_imoveis_por_pagina)

# Função para salvar os dados em um arquivo csv


def salvar_dados(arquivo_csv):
    # Limpar o arquivo antes de começar a escrever
    open(arquivo_csv, 'w').close()

    # Escrever cabeçalho
    with open(arquivo_csv, 'a', newline='', encoding='UTF-8') as f:
        f.write('Tipo;Negocio;Cidade;Bairro;Preco;Descricao;UrlImagem;LinkImovel\n')

# Função principal


def main():
    # URLs para os diferentes tipos de finalidade e número de páginas para iterar

    urls = {
        'venda': ('https://www.escolhamonteiro.com.br/imoveis/a-venda'),
        'locacao': ('https://www.escolhamonteiro.com.br/imoveis/para-alugar')
    }

    # Nome do arquivo CSV
    nome_arquivo = 'imoveis_dados_monteiro.csv'

    # Caminho do arquivo CSV
    arquivo_csv = 'C:\\Users\\denis\\OneDrive\\Documentos\\Projeto_Imob\\' + nome_arquivo

    # Salvar cabeçalho e limpar arquivo
    salvar_dados(arquivo_csv)

    # Iterar sobre as URLs e extrair e escrever os dados no arquivo CSV
    for finalidade, url in urls.items():
        print(f'Extraindo dados para a finalidade: {finalidade}')
        # Obter o número de páginas para a URL atual
        obter_numero_de_paginas(url)
        for i in range(1):
            url_pag = f'{url}'
            print(f'Extraindo dados da página {i} de {finalidade}')
            print("-" * 40)
            # Extrair e escrever os dados da página atual
            extrair_e_escrever_dados(url_pag, arquivo_csv, finalidade, i)

    # Encerre o driver do Selenium
    driver.quit()

    registrar_log('Final', 'venda', f'Total: {total_venda} imóveis')
    registrar_log('Final', 'locacao', f'Total: {total_locacao} imóveis')

    # Fazer upload do arquivo para o Google Drive
    id_pasta = '14NUG9dF7HE_E5f-vxKtIzXz9jjX9e6Y7'
    gd_upload.upload_arquivo_para_drive(nome_arquivo, arquivo_csv, id_pasta)

    # Enviar email sobre a execução bem sucedida
    send_email.enviar_email(f'Script executado para: ',
                            f'O script foi executado com sucesso!')


if __name__ == "__main__":
    main()

print('Extração de dados concluída!')
