import os
import csv
import datetime
import re  # biblioteca expressoes regulares
import requests
import sys
from bs4 import BeautifulSoup
import upload_googledrive as gd_upload  # importando função genérica
import send_email  # importando função genérica

# Definir variáveis globais para armazenar o somatório da quantidade de imóveis para venda e locação
total_venda = 0
total_locacao = 0

# Função para obter o conteúdo HTML de uma página


def obter_site(url):
    # Definir o cabeçalho padrão
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        # verifica se a resposta da requisição HTTP foi bem-sucedida.
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        # Caso a requisição falhe, imprimir o status code para depuração e registrar no log
        print(f"Falha na requisição. Status code: {response.status_code}")
        registrar_log('Erro na obtenção do site', str(e), None)

    # Função para obter o número de páginas a iterar


def obter_numero_de_paginas(url):
    # Obter o conteúdo HTML da página
    soup = obter_site(url)

    # Verificar se o conteúdo HTML foi obtido com sucesso
    if not soup:
        # Lógica para lidar com a falha na obtenção do site
        print(f'Erro ao tentar obter o número de páginas')
        registrar_log('Erro ao tentar obter o número de paginas', None, None)
        sys.exit()  # Encerra o script se houver erro na obtenção do site

    try:
        # Encontrar o elemento de paginação
        paginacao_element = soup.find_all('a', class_='lipagina-btn-paginacao')
        ultima_pagina = paginacao_element[-2].get_text()

        # Se a última página for "...", continuamos buscando até encontrar a página correta
        while ultima_pagina == "...":
            # Atualizamos a variável paginacao_element com o novo valor da página
            paginacao_element = soup.find_all(
                'a', class_='lipagina-btn-paginacao')
            ultima_pagina = paginacao_element[-3].get_text()
            url_pag_len = f'{url}&pag={ultima_pagina}'
            soup = obter_site(url_pag_len)
            ultima_pagina = paginacao_element[-2].get_text()

        # Retornamos o número da última página
        return int(ultima_pagina)

    except Exception as e:
        # Lógica para lidar com outros erros
        print(f'Erro ao tentar obter o número de páginas: {e}')
        registrar_log(f'Erro ao tentar obter o número de páginas: {e}')
        sys.exit()  # Encerra o script se houver outro erro

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
    soup = obter_site(url)
    # Slicing [:-1] no final da linha para selecionar todos os elementos da lista imoveis, exceto o último elemento, que é a paginação do site
    imoveis = soup.find_all('div', class_='imovelcard')[:-1]

    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')

        for imovel in imoveis:
            # Capitalizar a primeira letra de cada palavra e corrigir Locação
            negocio = tipo_transacao.capitalize().replace("Locacao", "Locação")
            tipo_element = imovel.find('p', class_='imovelcard__info__ref')
            # Verificar se o caractere "-"" está presente na string
            if "-" in tipo_element.get_text(strip=True):
                tipo = tipo_element.get_text(strip=True).split(
                    "-")[1].strip() if tipo_element else "N/A"
            else:
                tipo = tipo_element.get_text(
                    strip=True) if tipo_element else "N/A"

            if tipo != "N/A":
                preco_element = imovel.find(
                    'p', class_='imovelcard__valor__valor')
                bairro_cidade_element = imovel.find(
                    'h2', class_='imovelcard__info__local')
                # Verificar se a descrição está vazia, se estiver, tentar buscar de outro elemento para reduzirmos ao maximo a qtd de N/A
                descricao_element = imovel.find('h3')
                if descricao_element is None or descricao_element.text.strip() == "":
                    descricao_element = imovel.find(
                        'div', class_='imovelcard__info__feature')

                # Obter somente o texto contido nos elementos acima. O método get_text() é usado para extrair o texto de uma tag HTML. O argumento strip=True remove espaços em branco no início e no final do texto
                preco = preco_element.get_text(
                    strip=True) if preco_element else "N/A"
                bairro_cidade = bairro_cidade_element.get_text(
                    strip=True) if bairro_cidade_element else "N/A"

                # Aqui estamos tirando as quebras de linha com o replace
                descricao = (descricao_element.get_text(strip=True).replace(
                    '\n', '').replace('\r', '')) if descricao_element else "N/A"

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
                url_imagem = imovel.find_next('a').find('img')['src']
                link_imovel = 'https://www.moradaimoveiskta.com.br' + \
                    imovel.find_next('a')['href']

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
        'venda': ('https://www.moradaimoveiskta.com.br/imovel/?finalidade=venda&tipo=&bairro=0&sui=&ban=&gar=&dor='),
        'locacao': ('https://www.moradaimoveiskta.com.br/imovel/?finalidade=locacao&tipo=&bairro=0&sui=&ban=&gar=&dor=')
    }

    # Nome do arquivo CSV
    nome_arquivo = 'imoveis_dados_morada.csv'

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
            url_pag = f'{url}&pag={i}'
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
