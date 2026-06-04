import requests
import os
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuração da página alvo
URL_PARA_MONITORIZAR = "https://agse.pt"
FICHEIRO_LEITURA = "links_guardados.txt"

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

def enviar_email(novos_links):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg['Subject'] = "Alerta: Novos links/documentos detetados na AGSE!"
    
    # Lista os novos links de forma organizada
    lista_links_texto = "\n".join([f"- {link}" for link in novos_links])
    
    corpo = f"Olá,\n\nFoi adicionada uma nova sub-página ou documento PDF no site do concurso:\n\n{lista_links_texto}\n\nLink da página principal: {URL_PARA_MONITORIZAR}\n\nCumprimentos,\nBot de Monitorização"
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_REMETENTE, EMAIL_SENHA)
        server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        server.quit()
        print("Email de alerta enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def monitorizar():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print(f"A analisar a página em busca de links: {URL_PARA_MONITORIZAR}")
    try:
        resposta = requests.get(URL_PARA_MONITORIZAR, headers=headers, timeout=15)
        resposta.raise_for_status()
        html = resposta.text
    except Exception as e:
        print(f"Erro crítico ao aceder ao site: {e}")
        return

    # Extrai todas as tags de links <a>
    soup = BeautifulSoup(html, 'html.parser')
    links_encontrados = set()
    
    for tag in soup.find_all('a', href=True):
        link = tag['href']
        
        # Filtra links inúteis
        if link.startswith('#') or link.startswith('javascript:'):
            continue
            
        # Completa links relativos
        if link.startswith('/'):
            link = "https://agse.pt" + link
            
        links_encontrados.add(link)

    # Lê o histórico de links do ficheiro de texto
    links_antigos = set()
    if os.path.exists(FICHEIRO_LEITURA):
        with open(FICHEIRO_LEITURA, "r", encoding="utf-8") as f:
            links_antigos = set(linha.strip() for linha in f if linha.strip())

    # Descobre se há novos links cruzando as duas listas
    novos_links = links_encontrados - links_antigos

    if novos_links:
        print(f"Detetados {len(novos_links)} novos links!")
        
        # Só envia email se já existir um histórico gravado anteriormente
        if links_antigos:
            enviar_email(novos_links)
        else:
            print("Primeira execução: a guardar a lista inicial de links para referência futura.")

        # Atualiza o ficheiro de texto com a lista de links organizada
        with open(FICHEIRO_LEITURA, "w", encoding="utf-8") as f:
            for link in sorted(links_encontrados):
                f.write(f"{link}\n")
    else:
        print("Nenhum link ou sub-página nova foi detetada.")

if __name__ == "__main__":
    monitorizar()
