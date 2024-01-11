# Imports
import random

import requests
import os
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import pymongo
import time
import base64
from datetime import datetime
from colorama import Back, Style
from urllib.parse import urlparse, parse_qs

# PAYRE2FB TARGET
TARGET = "http://papyrefb53cki34wumjh2yokayxiunzmmrabpxvinfjauwm5az25snid.tor2web.it/onion_2/index.php?ax=1"
# http://9fx.us/papyrefb2_1
DOMAIN = "http://papyrefb53cki34wumjh2yokayxiunzmmrabpxvinfjauwm5az25snid.tor2web.it"


def main(dataGrid_page: int):
    print('\n\n--------------------------- STARTING WEB SCRAPING  -----------------------------\n\n')
    response_soup = None

    try:

        # With this payload change the number of books in page
        payload = {
            'dataGrid_page': dataGrid_page,
            'dataGrid_sortfield': 'anyo',
            'dataGrid_sortdirection': 'desc',
            'dataGrid_recordsOnPage': 50,
        }

        # Scrapping with Pages
        request_response = requests.post(TARGET,  data=payload, headers={'User-Agent': getRandomUserAgent()})

        # Latest books publishing
        #request_response = requests.post(TARGET, headers={'User-Agent': getRandomUserAgent()})

        if request_response.status_code == 200:
            html_content = request_response.text
            response_soup = BeautifulSoup(html_content, 'html.parser')
        else:
            print('Error to load website')
    except urllib.error.URLError as e:
        print("Error to access URL:", str(e))
    except Exception as ex:
        print("Other app error:", str(ex))

    row_books = response_soup.find_all('tr', class_=["grid-row-odd", "grid-row-even"])
    print('Total row books found: ', len(row_books))

    for index_book, tr_element in enumerate(row_books, 1):
        td_elements = tr_element.find_all('td')
        if len(td_elements) >= 2:
            print('--- BOOK Nº ', index_book, ' PROCESSING -------------------------------------------------')
            book_author = td_elements[0].get_text()
            book_title = td_elements[1].get_text()
            book_year = td_elements[2].get_text()
            book_gender = td_elements[3].get_text()
            book_theme = td_elements[4].get_text()

            ref_link = td_elements[1].get('onclick')
            ref_link = ref_link.replace("javascript:document.location.href='..", "")
            ref_link = ref_link.replace("'", "")
            ref_link = DOMAIN + ref_link

            book_cover = {
                'book_cover': getBookImage(ref_link)
            }

            customSleep()
            url_book_sheet = urllib.request.urlopen(ref_link)
            book_sheep_soup = BeautifulSoup(url_book_sheet, 'html.parser')
            book_summary = book_sheep_soup.find('p', class_='capitalLetter').get_text()

            # Obtenemos el enlace para descargar el fichero .mobi
            button_element = None

            for link in book_sheep_soup.find_all('a', class_='myButton'):
                if link.text == 'Mobi':
                    button_element = link
                    break
            ref_mobi = None
            ref_download = None
            ref_binary = None
            if button_element:
                ref_mobi = button_element.get('href')
                ref_mobi = ref_mobi.replace("./", "/")
                ref_mobi = DOMAIN + ref_mobi
                ref_mobi = getMobiUrl(ref_mobi)
                ref_download = extractUrlDownloadEbook(getMobiId(ref_mobi))
                ref_binary = getBookBinary(ref_download)

            papyro_book = {
                'book': book_title,
                'author': book_author,
                'year': book_year,
                'gender': book_gender,
                'theme': book_theme,
                'summary': book_summary,
                'ref_download': ref_download,
                'cover_reference': '',
                'saved_date': datetime.now(),
                'ref_binary': ref_binary,
            }

            print('--- BOOK DATA -----------------------------------------------')
            for clave, valor in papyro_book.items():
                customPrint(clave, valor)

            print('--- BOOK SAVE -----------------------------------------------')
            saveBook(papyro_book, book_cover)

            print('---------------------------------------------------\n\n')
        customSleep()


def getMobiUrl(url):
    customSleep()
    request = urllib.request.Request(url, headers={'User-Agent': getRandomUserAgent()})
    response = urllib.request.urlopen(request)
    nueva_url = response.geturl()
    return nueva_url


def getMobiId(url):
    customSleep()
    request = urllib.request.Request(url, headers={'User-Agent': getRandomUserAgent()})
    response = urllib.request.urlopen(request)
    # Tratamiento de la respuesta
    book_soup = BeautifulSoup(response, 'html.parser')
    book_id = book_soup.find('a', class_='myButton', string='Mobi')['href']
    book_id = book_id.replace("https://ashnk.com/OTQwMDY=/", "")
    book_id = book_id.replace(
        "https://anzalweb.ir/wp-content/uploads/2019/10/what-is-error-509-bandwidth-limit-exceeded-and-how-to-fix-it.jpg?",
        "")
    return book_id


def extractUrlDownloadEbook(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    url_param_value = query_params.get('url', [])[0]
    return url_param_value


def getBookImage(cover_url):
    cover_url = cover_url.replace("/ficha2.php?a=", "/ficha/includes/")
    cover_url = cover_url.replace("&aws=", ".jpg")
    try:
        request = urllib.request.Request(cover_url, headers={'User-Agent': getRandomUserAgent()})
        response = urllib.request.urlopen(request)
        image_content = response.read()
        book_image = base64.b64encode(image_content).decode('utf-8')
    except Exception as e:
        print('Error E: ', e)
        book_image = ""
    return book_image


def saveBook(book, book_cover):

    if book["ref_binary"] != "":
        client = pymongo.MongoClient("localhost:27017")
        database = client["ikawe"]
        collection = database["books"]
        collection_covers = database["books_cover"]
        existing_book = collection.find_one({"book": book["book"]})
        if existing_book:
            if existing_book["ref_download"] == book["ref_download"]:
                print("El libro ya existe y el campo 'url_download' es el mismo.")
            else:
                result = collection.update_one(
                    {"book": book["book"]},
                    {"$set": {"ref_download": book["ref_download"]}}
                )
                print("El libro ya existe pero el campo 'ref_download' fue actualizado:", result.modified_count,
                      "actualizaciones.")
        else:
            result_cover = collection_covers.insert_one(book_cover)
            print(f"Inserted Coover Book with ID: {result_cover.inserted_id}")
            book["cover_reference"] = result_cover.inserted_id
            result = collection.insert_one(book)
            print(f"Inserted Book: {book['book']} with ID {result.inserted_id}")
        client.close()
    else:
        print(f'ERROR - Not boook downloaded')


def getBookBinary(book_uri):
    print(f'Start downloading: {book_uri}')
    book_name = book_uri.split("/")[-1]
    response = requests.get(book_uri)
    if response.status_code == 200:
        ruta_archivo = os.path.join("../IkaWeb/static/ebooks/", book_name)
        with open(ruta_archivo, 'wb') as archivo_local:
            archivo_local.write(response.content)
        print(f'eBook has been download in:  {ruta_archivo}')
        return book_name
    else:
        print(f'Error to download ebook from: {book_uri} - Status Code: {response.status_code}')
        return ""


# -------------------------  FUNCIONES DE REFUERZO ---------------------


def getRandomUserAgent():
    user_agent_list = [
        "Mozilla/5.0",
        "Chrome/91.0.4472.124",
        "Safari/537.36",
        "Edge/91.0.864.59",
        "Opera/75.0.3969.149",
        "Firefox/89.0",
    ]
    random_user_agent = random.choice(user_agent_list)
    # print("User-Agent: " + random_user_agent)
    return random_user_agent


def customSleep():
    sleep_time = random.uniform(3, 7)
    time.sleep(sleep_time)


def customPrint(key, value):
    print(Back.GREEN + key + Style.RESET_ALL, value)


# Ultimo Pagina 1, Libro 21
for page in range(1, 3):
    print('Init Scraping Page: ', page)
    main(page)
