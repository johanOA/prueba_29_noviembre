#source myenv/bin/activate
from bs4 import BeautifulSoup
from flask import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import csv
import time
from translate import Translator
import re

def scrape_prices_safari(url, search_query):
    
    # Configurar el traductor
    translator = Translator(from_lang="en", to_lang="es")
    driver = webdriver.Safari()

    
    if "facebook" in url:
        cookies_path = "./cookies/cookiesFacebook.json"
    elif "instagram" in url:
        cookies_path = "./cookies/cookiesInstagram.json"

    driver.maximize_window()

    try:
        driver.get(url)

        time.sleep(2)

        with open(cookies_path, 'r') as file:
            cookies = json.load(file)

        for cookie in cookies:
            # Renombrar expirationDate a expiry y verificar campos requeridos
            if 'expirationDate' in cookie:
                cookie['expiry'] = int(cookie.pop('expirationDate'))

            # Eliminar campos no soportados o problemáticos
            cookie = {k: v for k, v in cookie.items() if k in ['name', 'value', 'domain', 'path', 'secure', 'httpOnly', 'expiry']}

            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(f"Error al agregar cookie {cookie.get('name', '(sin nombre)')}: {e}")


        driver.refresh()
        
        time.sleep(5)

        #------------------------------------------------------------------------------------
        #PARA GUARDAR LOS DATOS DE LA CUENTA
        # Obtener el HTML de la página
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        
        accountName = soup.find_all('span', {'x1lliihq x193iq5w x6ikm8r x10wlt62 xlyipyv xuxw1ft'})
        # Buscar el texto "UBISOFT"
        for span in accountName:
            if "UBISOFT" in span.text:
                nameAccount = span.text
                print(f"nameAccount = {nameAccount}" )  # Resultado: UBISOFT+

        detailsAccount = soup.find_all('span', {'html-span xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1hl2dhg x16tdsg8 x1vvkbs'})
        
        # Extraer todos los textos de los spans
        data = [span.text for span in detailsAccount]
        
        # Asignar las variables según el orden de los datos
        if len(data) >= 3:  # Asegurarse de que haya al menos 3 valores
            numPublic = data[0]        # Primer valor
            numFollowers = data[1]     # Segundo valor
            numFollowed = data[2]      # Tercer valor

            # Imprimir las variables asignadas
            print(f"numPublic = {numPublic}")
            print(f"numFollowers = {numFollowers}")
            print(f"numFollowed = {numFollowed}")
        else:
            print("No hay suficientes datos para asignar las variables.")

        spanDescriptionAccount = soup.find_all('span', {'_ap3a _aaco _aacu _aacx _aad7 _aade'})
        
        data2 = [span.text for span in spanDescriptionAccount]
        description = data2[0]
        traslate = translator.translate(description)


        output_file = "Cuentas.csv"

        #Escribe el CSV para las cuentas
        with open(output_file, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)

            # Escribir encabezados
            writer.writerow(["Nombre_de_cuenta", "N_Publicaciones", "N_Seguidores", "N_Seguidos", "Descripcion"])

            # Verificar que las variables están definidas
            try:
                # Escribir los datos obtenidos
                writer.writerow([
                    nameAccount,
                    numPublic,
                    numFollowers,
                    numFollowed,
                    traslate
                ])
                print(f"Datos guardados en {output_file}")
            except NameError as e:
                print(f"Error: {e}. Variables sin datos.")

            # Espera hasta que el div con la clase '_aagu' sea visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div._aagu'))
            )

            # Obtener todos los divs con la clase '_aagu'
            all_posts = driver.find_elements(By.CSS_SELECTOR, 'div._aagu')

            # Iterar sobre cada publicación encontrada y hacer clic
            for post in all_posts:
                try:
                    post.click()  # Hacer clic en la publicación               
                    time.sleep(3)  # Esperar un poco para que la publicación cargue
                    # Obtener todos los comentarios
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.x1qjc9v5.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x78zum5.xdt5ytf.x2lah0s.xk390pu.xdj266r'))
                    )
                    # Obtener todos los divs con la clase '_a9zs' (comentarios)
                    all_comments = driver.find_elements(By.CSS_SELECTOR, 'div.x1qjc9v5.x972fbf.xcfux6l.x1qhh985.xm0m39n.x9f619.x78zum5.xdt5ytf.x2lah0s.xk390pu.xdj266r')

                    comments = []

                    for idx, comment_div in enumerate(all_comments):
                        try:
                            # Extraer el texto del comentario
                            comment_text = comment_div.text
                            if idx == 0:
                                # El primer comentario es la descripción
                                description_comment = comment_text
                                print(f"Descripción: {description_comment}")
                            else:
                                # El resto son comentarios
                                comments.append(comment_text)
                                print(f"Comentario {idx}: {comment_text}")

                        except Exception as e:
                            print(f"Error al extraer el comentario {idx}: {e}")
                    # Expresión regular para extraer el número de "Me gusta" y el texto del comentario
                    pattern = r"(\d+)\s*h.*?Me gusta|(?<=Me gusta).*"  # Busca el número de "Me gusta" y el texto

                    cleaned_comments = []
                    
                    for comment in comments:
                        # Buscar número de "Me gusta" y texto del comentario
                        match = re.search(pattern, comment)
                        if match:
                            likes = match.group(1) if match.group(1) else '0'  # Si no hay número, asigna '0'
                            text = comment.split('Me gusta')[0].strip()  # Todo antes de "Me gusta" es el comentario
                            cleaned_comments.append(f"{likes} Me gusta: {text}")
                    # Mostrar los comentarios limpios
                    for cleaned_comment in cleaned_comments:
                        print(cleaned_comment)
                except Exception as e:
                    print(f"Error al hacer clic en la publicación: {e}")
        reacctionPublic = soup.find_all('span', {'x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs xt0psk2 x1i0vuye xvs91rp x1s688f x5n08af x10wh9bi x1wdrske x8viiok x18hxmgj'})

        for span in accountName:
            if "Me gusta" in span.text:
                nameAccount = span.text

        output_file = "Cuentas.csv"
        
        #Escribe el CSV para las cuentas
        with open(output_file, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)

            # Escribir encabezados
            writer.writerow(["Descripcion","Reacciones", "Comentarios"])

            # Verificar que las variables están definidas
            try:
                # Escribir los datos obtenidos
                writer.writerow([
                    description_comment,
                    reacctionPublic,
                    cleaned_comments,
                ])
                print(f"Datos guardados en {output_file}")
            except NameError as e:
                print(f"Error: {e}. Variables sin datos.")

        # Intentar encontrar el campo de búsqueda usando los selectores
        search_box = None
        
        css_search = ['xrvj5dj x1ec4g5p xl463y0 xwy3nlu xdj266r xh8yej3']
        
        id_search = ['twotabsearchtextbox', 
                    'cb1-edit', 
                    'autocomplete-0-input']

        for selector in css_search + id_search:
            try:
                search_box = driver.find_element(By.CSS_SELECTOR, selector) if "data" in selector else driver.find_element(By.ID, selector)
                if search_box:
                    break
            except:
                continue

        if search_box:
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.RETURN)
        else:
            print("No se encontró un campo de búsqueda.")

        time.sleep(5)

        if "exito" in url:
            time.sleep(5)

        print(f"Título de la página: {driver.title}")


        if "facebook" in url:
            print("face")
            #amazonGetResources(page_source)
        elif "instagram" in url:
            #exitoGetRources(page_source)
            print("insta")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        print("Es toda mano")

# https://www.mercadolibre.com.co
# Ejemplo de uso
url = "https://www.instagram.com/ubisoft/"

#url = "https://www.exito.com"
#url = "https://www.alkosto.com"
search_query = "celuweb"
scrape_prices_safari(url, search_query)