import requests
import os
import smtplib
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# =========================================================================
# CONFIGURAÇÃO AVANÇADA: Inclui o Feed RSS onde as novidades entram na hora
# =========================================================================
PAGINAS_ALVO = [
    "https://agse.pt/concurso-nacional-2026-2027",  # Página do concurso
    "https://agse.pt",                              # Página mãe
    "https://agse.pt/feed/"                         # O Feed Secreto (Bypassa a Cache e apanha tudo!)
]
# =========================================================================

FICHEIRO_LEITURA = "links_guardados.txt"

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE")
EMAIL_SENHA = os.environ.get("EMAIL_SENHA")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO")

def normalizar_url(url):
    """Uniformiza os links para evitar duplicados e falsos alertas"""
    url = url.strip()
    url = url.replace("https://www.agse.pt", "https://agse.pt")
    url = url.replace("http://www.agse.pt", "https://agse.pt")
    url = url.replace("http://agse.pt", "https://agse.pt")
    if url.endswith("/"):
        url = url[:-1]
    return url

def enviar_email(novos_links):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = EMAIL_DESTINATARIO
    msg['Subject'] = "Alerta Urgente: Nova publicação detetada na AGSE!"
    
    lista_links_texto = "\n".join([f"- {link}" for link in novos_links])
    
    corpo = f"Olá,\n\nForam encontrados novos links ou sub-páginas no portal da AGSE (detetado via monitorização avançada):\n\n{lista_links_texto}\n\nCumprimentos,\nBot de Monitorização"
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

    links_encontrados = set()

    for url in PAGINAS_ALVO:
        print(f"A escanear exaustivamente: {url}")
        try:
            resposta = requests.get(url, headers=headers, timeout=15)
            resposta.raise_for_status()
            html = resposta.text
        except Exception as e:
            print(f"Aviso: Falha ao aceder a {url}: {e}")
            continue

        # Método 1: BeautifulSoup para links estruturais
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['a', 'link'], href=True):
            link = tag['href']
            if link.startswith('/'):
                link = urljoin("https://agse.pt", link)
            links_encontrados.add(normalizar_url(link))

        # Método 2: Detetor de Texto Puro (apanha links dentro de códigos ou do Feed RSS)
        links_texto_puro = re.findall(r'https?://(?:www\.)?agse\.pt/[^\s"\'><]+', html)
        for link in links_texto_puro:
            links_encontrados.add(normalizar_url(link))

    # Filtragem de ficheiros de sistema irrelevantes (imagens, estilos, scripts)
    links_filtrados = set()
    for link in links_encontrados:
        if any(link.endswith(ext) for ext in ['.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '/feed', '/rss']):
            continue
        # Garante que só guardamos links internos do portal
        if link.startswith("https://agse.pt"):
            links_filtrados.add(link)

    # Ler histórico anterior
    links_antigos = set()
    if os.path.exists(FICHEIRO_LEITURA):
        with open(FICHEIRO_LEITURA, "r", encoding="utf-8") as f:
            links_antigos = set(normalizar_url(linha) for linha in f if linha.strip())

    # Cruzamento de dados
    novos_links = links_filtrados - links_antigos

    if novos_links:
        print(f"Sucesso! Detetados {len(novos_links)} novos links!")
        
        if links_antigos:
            enviar_email(novos_links)
        else:
            print("Primeira corrida: a mapear a estrutura inicial do site.")

        # Grava a nova lista limpa e ordenada
        with open(FICHEIRO_LEITURA, "w", encoding="utf-8") as f:
            for link in sorted(links_filtrados):
                f.write(f"{link}\n")
    else:
        print("Nenhuma novidade detetada no portal.")

if __name__ == "__main__":
    monitorizar()
