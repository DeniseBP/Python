
import os
import csv
import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
import upload_googledrive as gd_upload  # importando função genérica
import logging
import send_email  # importando função genérica

# Configurar para apenas mensagens de nível WARNING ou superior sejam exibidas no terminal
logging.basicConfig(level=logging.WARNING)

# Definir variáveis globais para armazenar o somatório da quantidade de imóveis para venda e locação
total_venda = 0
total_locacao = 0

# Configurações do Selenium
options = Options()
# configuração do tamanho da tela do navegador
# options.add_argument('window-size=1366,768')
options.add_argument("--start-maximized")
# Rodar o navegador sem interface gráfica
options.add_argument("--headless")
navegador = webdriver.Chrome(options=options)


def obter_numero_de_paginas(url):
    navegador.get(url)
    # Aguarde para garantir que a página seja totalmente carregada
    time.sleep(5)
    # Encontrar o elemento de paginação
    paginacao_element = navegador.find_elements(By.CSS_SELECTOR, 'h3')
    if paginacao_element:
        ultima_pagina = paginacao_element[-1].text.strip()
        # Verificar se a última página é um número válido
        if ultima_pagina.isdigit():
            return int(ultima_pagina)
        else:
            print("O número de páginas não pôde ser obtido. Usando valor padrão.")
            registrar_log(
                'O número de páginas não pôde ser obtido. Usando valor padrão.', None, None)
            return 30  # Valor padrão
    else:
        print("O número de páginas não pôde ser obtido. Usando valor padrão.")
        registrar_log(
            'O número de páginas não pôde ser obtido. Usando valor padrão.', None, None)
        return 30  # Valor padrão


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
    # Criar uma nova instância do driver para cada pagina
    navegador.get(url)
    time.sleep(5)
    # Aguarde para garantir que a página seja totalmente carregada
    # tempo_max_espera = 10  # Tempo máximo de espera em segundos
    # try:
    #     WebDriverWait(navegador, tempo_max_espera).until(
    #         EC.visibility_of_element_located(
    #             (By.CSS_SELECTOR, 'mat-card.mat-card.mat-focus-indicator.ng-star-inserted'))
    #     )
    # except Exception as e:
    #     print("Erro ao esperar pelo carregamento da página:", e)
    #     # Registrar o log
    #     registrar_log(f'Erro ao esperar pelo carregamento da página:{
    #                   pagina_executada}', tipo_transacao, qtd_imoveis_por_pagina)
    #     return

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
                    element = imovel.find_element(
                        By.CSS_SELECTOR, css_selector)
                    return element.text.strip()
                except NoSuchElementException:
                    return "N/A"

            # Capitalizar a primeira letra de cada palavra e corrigir Locação
            negocio = tipo_transacao.capitalize().replace("Locacao", "Locação")

            tipo_element = get_element_text(
                imovel, 'mat-card-title.mat-card-title.h3.color-title.bold')
            bairro_cidade_element = get_element_text(
                imovel, 'mat-card-subtitle.mat-card-subtitle.h5.color-title')
            descricao = get_element_text(
                imovel, 'mat-card-subtitle.mat-card-subtitle.h4.color-subtitle')
            try:
                preco = imovel.find_element(
                    By.CLASS_NAME, 'title_value.ng-star-inserted').text.strip()
            except NoSuchElementException:
                # Trtativa preço como "Consulte"
                preco = "NA"

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
                    tipo = ' '.join(descricao.split()[:2])

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

            # # Aguarde até que o link do imóvel seja visível na página
            # try:
            #     link_imovel_element = WebDriverWait(imovel, tempo_max_espera).until(
            #         EC.presence_of_element_located(
            #             (By.CSS_SELECTOR, 'div > a'))
            #     )
            # except Exception as e:
            #     print("Erro ao esperar pelo link do imóvel:", e)
            #     continue  # Pule para o próximo imóvel se não puder encontrar o link

            # # Aguarde até que a URL da imagem do imóvel seja visível na página
            # try:
            #     url_imagem_element = WebDriverWait(imovel, tempo_max_espera).until(
            #         EC.presence_of_element_located(
            #             (By.CSS_SELECTOR, '.swiper-slide.swiper-slide-duplicate-active img'))
            #     )
            # except Exception as e:
            #     print("Erro ao esperar pela URL da imagem do imóvel:", e)
            #     continue  # Pule para o próximo imóvel se não puder encontrar a URL da imagem

            link_imovel_element = imovel.find_element(
                # sempre que for uma tag filha podemos utilizar o sinal >
                By.CSS_SELECTOR, 'div > a') if imovel else None
            url_imagem_element = imovel.find_element(
                By.CSS_SELECTOR, '.swiper-slide.swiper-slide-duplicate-active').find_element(
                By.TAG_NAME, 'img')

            # Obter somente o texto contido nos elementos acima
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

        # Contar a quantidade de imóveis processados nesta página
        qtd_imoveis_pagina = len(imoveis)
        qtd_imoveis_por_pagina = f'{qtd_imoveis_pagina} imóveis encontrados'

        # Atualizar o somatório da quantidade de imóveis para venda ou locação
        if tipo_transacao == 'venda':
            total_venda += qtd_imoveis_pagina
        elif tipo_transacao == 'locacao':
            total_locacao += qtd_imoveis_pagina

        # Encontrar o numero da página que foi executada
        pagina_executada = f'page {pagina_atual}'
        # Registrar o log
        registrar_log(pagina_executada, tipo_transacao, qtd_imoveis_por_pagina)

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
        'venda': ('https://www.rufino.imb.br/buscar?order=most_relevant&direction=desc&availability=buy'),
        'locacao': ('https://www.rufino.imb.br/buscar?order=most_relevant&direction=desc&availability=rent')
    }

    # Nome do arquivo CSV
    nome_arquivo = 'imoveis_dados_rufino.csv'

    # Caminho do arquivo CSV
    arquivo_csv = 'C:\\Users\\denis\\OneDrive\\Documentos\\Projeto_Imob\\' + nome_arquivo

    # Salvar cabeçalho e limpar arquivo
    salvar_dados(arquivo_csv)

    # Iterar sobre as URLs e extrair e escrever os dados no arquivo CSV
    for finalidade, url in urls.items():
        print(f'Extraindo dados para a finalidade: {finalidade}')
        # Obter o número de páginas para a URL atual
        num_paginas = obter_numero_de_paginas(url)
        for i in range(1, num_paginas + 1):
            url_pag = f'{url}&page={i}'
            print(f'Extraindo dados da página {i} de {finalidade}')
            print("-" * 40)
            # Extrair e escrever os dados da página atual
            extrair_e_escrever_dados(url_pag, arquivo_csv, finalidade, i)

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
