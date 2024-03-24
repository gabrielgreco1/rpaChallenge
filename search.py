from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pandas as pd
import os
import json
import time

class NYTSearch:
    def __init__(self, query):
        self.query = query
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.wait = WebDriverWait(self.driver, 10)
        self.filepath = f'C:\\Challenge_RPA_PixelDu\\scrappedItems\\news_{query}.xlsx'
        self.filepath = self.filepath.replace(' ','_')

    def open_search(self):
        self.driver.get(f"https://www.nytimes.com/search?dropmab=false&query={self.query}&sort=newest")

    def scrape_list_items(self):
        try:
            # Wait until the list appears on the webpage
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ol')))
            # Fetch all list items
            list_items = self.driver.find_elements(By.CSS_SELECTOR, 'ol > li')
            return list_items
        except TimeoutError:
            print("The list did not load in time")
            return []

    def scrape_item_details(self, list_item):
        # Assuming list_item is a WebElement object
        details = {}

        # Extract headings
        details['headings'] = [heading.text for heading in list_item.find_elements(By.CSS_SELECTOR, 'h1, h2, h3, h4, h5, h6')]

        # Extract <span> element
        details['date'] = [span.text for span in list_item.find_elements(By.CSS_SELECTOR, "span")]

        # Extract <p> elements
        details['paragraphs'] = [p.text for p in list_item.find_elements(By.CSS_SELECTOR, 'p')]

        # Extract <a> elements
        details['links'] = [a.get_attribute('href') for a in list_item.find_elements(By.CSS_SELECTOR, 'a')]

        # Extract text from the span if present
        # span_element = list_item.find_element(By.XPATH, '//*[@id="site-content"]/div/div[1]')
        # details['date_text'] = span_element.text if span_element else None

        # Extract <img> inside <figure>
        figures = list_item.find_elements(By.CSS_SELECTOR, 'div > figure')
        images = [fig.find_element(By.TAG_NAME, 'img').get_attribute('src') for fig in figures if fig.find_element(By.TAG_NAME, 'img')]
        return {
            'newsData': details,
            'imageUrls': images
        }
    
    def download_image(self, url, path):
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
            print(f"Imagem baixada com sucesso: {path}")
        else:
            print(f"Erro ao baixar a imagem. Status code: {response.status_code}")

    def save_to_xlsx(self, data):
        # Define o texto base do link indesejado para a verificação
        undesired_links_texts = [
                                "https://www.nytimes.com/search?dropmab=false&query=",
                                "https://www.nytimes.com/topic/"
        ]        
        # Verifica se algum link na lista contém o texto base
        if any(any(base_text in link for base_text in undesired_links_texts) for link in data['newsData']['links']):
            print("Encontrado link com texto base indesejado, registro ignorado.")
            return
        
        # Desempacota os dados
        news_data = data['newsData']
        image_urls = data['imageUrls']
        
        # Seleciona o segundo parágrafo de 'paragraphs', conforme especificado
        selected_paragraph = news_data['paragraphs'][1] if len(news_data['paragraphs']) > 1 else None
        
        # Preparando os dados para DataFrame
        data_for_df = {
            'headings': [news_data['headings'][0]] if news_data['headings'] else [None],
            'date': [news_data['date'][0]] if news_data['date'] else [None],
            'paragraphs': [selected_paragraph],
            'links': [news_data['links'][0]] if news_data['links'] else [None],
            'image_urls': [image_urls[0]] if image_urls else 'No image available'
        }
        
        df = pd.DataFrame(data_for_df)
        
        # Se o arquivo já existe, carrega o DataFrame existente e anexa os novos dados
        if os.path.exists(self.filepath):
            with pd.ExcelWriter(self.filepath, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
                # Lê o arquivo Excel existente e o DataFrame da planilha específica
                try:
                    existing_data_df = pd.read_excel(self.filepath, sheet_name='News Data')
                    # Anexa os novos dados
                    updated_df = pd.concat([existing_data_df, df], ignore_index=True)
                    # Salva o DataFrame atualizado no arquivo, substituindo a planilha existente
                    updated_df.to_excel(writer, sheet_name='News Data', index=False)
                except ValueError:
                    # Se a planilha não existir, apenas escreve os novos dados
                    df.to_excel(writer, sheet_name='News Data', index=False)
        else:
            # Se o arquivo não existe, cria um novo e salva os dados
            with pd.ExcelWriter(self.filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='News Data', index=False)

    def run(self):
        # Open the search page
        self.open_search()

        # Scrape all list items
        list_items = self.scrape_list_items()
        all_item_details = []

        for item in list_items:
            # Scrape details for each item
            data = self.scrape_item_details(item)
            data_json = json.dumps(data, indent= 4)
            if data:
                self.save_to_xlsx(data)
                # print(data_json)
                print('-------------------------------------------------------------')

                for url in data['imageUrls']:
                        filename = f"{data['newsData']['headings']}.jpg".replace('[', '').replace(']', '').replace('?', '')
                        save_path = f"C:\\Challenge_RPA_PixelDu\\images\\{filename}"
                        self.download_image(url, save_path)
               
        self.driver.quit()
        return all_item_details