import json
import smtplib
import sys
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def carregar_credenciais():
    with open('config.json', 'r') as arquivo:
        credenciais = json.load(arquivo)
    return credenciais


def enviar_email(assunto, mensagem):
    credenciais = carregar_credenciais()

    usuario = credenciais['email']
    senha = credenciais['senha']
    destinatario = credenciais['destinatario']

    # Configurações do servidor SMTP do Gmail
    servidor_smtp = 'smtp.gmail.com'
    porta_smtp = 587

    # Criando objeto para conexão com o servidor SMTP
    servidor = smtplib.SMTP(host=servidor_smtp, port=porta_smtp)
    servidor.starttls()  # Habilitando a conexão segura

    # Logando no servidor SMTP
    servidor.login(usuario, senha)

    # Criando o e-mail
    msg = MIMEMultipart()
    msg['From'] = usuario
    msg['To'] = destinatario

    # Adicionando o nome do arquivo ao assunto e caminho do arquivo à mensagem
    # Obtém o caminho completo do arquivo .py que está sendo executado
    caminho_arquivo = sys.argv[0]
    # Obtém a parte final (nome da imobiliaria) do arquivo .py que está sendo executado
    nome_arquivo = os.path.basename(caminho_arquivo).split('_')[
        2].split('.')[0]
    assunto = f'{assunto} {nome_arquivo}'
    mensagem = f'{mensagem}\n\nCaminho do script: {caminho_arquivo}'

    # Definindo assunto e corpo da mensagem
    msg['Subject'] = assunto
    corpo = mensagem
    msg.attach(MIMEText(corpo, 'plain'))

    # Enviando o e-mail
    servidor.sendmail(usuario, destinatario, msg.as_string())

    # Fechando a conexão com o servidor SMTP
    servidor.quit()
    # Msg de sucesso no envio do email
    print('Email enviado com sucesso!')
    print("-" * 50)


# Exemplo de uso
if __name__ == "__main__":
    assunto = 'Script executado para: '
    mensagem = 'O script foi executado com sucesso.'
    enviar_email(assunto, mensagem)
