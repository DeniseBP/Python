import os
import datetime
import csv
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
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

# Abrir o navegador que irá rodar a função def extrair_e_escrever_dados
navegador = webdriver.Chrome(options=options)

# Função para obter o número de páginas a iterar


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
            registrar_log(
                'O número de páginas não pôde ser obtido. Usando valor padrão.', None, None)
            return 40  # Valor padrão
    else:
        print("Elementos de paginação não encontrados. Usando valor padrão.")
        registrar_log(
            'O número de páginas não pôde ser obtido. Usando valor padrão.', None, None)
        return 40  # Valor padrão

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

            # Capitalizar a primeira letra de cada palavra e corrigir Locação
            negocio = tipo_transacao.capitalize().replace("Locacao", "Locação")

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
        'venda': ('https://www.mibimobiliaria.com.br/imoveis/comprar?'),
        'locacao': ('https://www.mibimobiliaria.com.br/imoveis/alugar?')
    }

    # Nome do arquivo CSV
    nome_arquivo = 'imoveis_dados_mb.csv'

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
            url_pag = f'{url}&p={i}'
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
