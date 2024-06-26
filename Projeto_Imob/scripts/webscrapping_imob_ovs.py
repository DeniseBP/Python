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

# Função para extrair o numero de páginas a iterar


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
    # Inicialize a variável de contagem
    qtd_imoveis_pagina = 0

    soup = obter_site(url)
    imoveis = soup.find_all('a')

    with open(arquivo, 'a', newline='', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')

        for imovel in imoveis:
            # Capitalizar a primeira letra de cada palavra e corrigir Locação
            negocio = tipo_transacao.capitalize().replace("Locacao", "Locação")
            img_tag = imovel.find('img')
            if img_tag:
                url_imagem = img_tag['src']
                if not url_imagem.startswith('/'):
                    localizacao_element = imovel.find_next('h2')
                    descricao_element = imovel.find_next('h3')

                    # Obter somente o texto contido nos elementos acima. O método get_text() é usado para extrair o texto de uma tag HTML
                    # O argumento strip=True remove espaços em branco no início e no final do texto
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

                    # Dividir a localização em partes: Tipo, Bairro/Cidade e Preço
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

                    # Escreva no arquivo CSV
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

                    # Incrementa a contagem de imoveis processados nesta página
                    qtd_imoveis_pagina += 1

        # Retorna a quantidade de itens inseridos nesta página
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
        'venda': ('http://www.ovsimoveis.com.br/imovel/?finalidade=venda&tipo=&bairro=0&suites=&banheiros=&vagas=&dormitorios='),
        'locacao': ('http://www.ovsimoveis.com.br/imovel/?finalidade=locacao&tipo=&bairro=0&suites=&banheiros=&vagas=&dormitorios=')
    }

    # Nome do arquivo CSV
    nome_arquivo = 'imoveis_dados_ovs.csv'

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
