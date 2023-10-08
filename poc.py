# Imports
import random

import requests
from bs4 import BeautifulSoup
import urllib.request
import urllib.error
import pymongo
import time
import base64
from datetime import datetime
from colorama import Back, Style

# PAYRE2FB TARGET
TARGET = "http://papyrefb53cki34wumjh2yokayxiunzmmrabpxvinfjauwm5az25snid.tor2web.it/onion_2/index.php?ax=1"
DOMAIN = "http://papyrefb53cki34wumjh2yokayxiunzmmrabpxvinfjauwm5az25snid.tor2web.it"


def main():
    print('\n\n--------------------------- STARTING WEB SCRAPING  -----------------------------\n\n')
    response_soup = None

    try:
        # With this payload change the number of books in page
        payload = {
            'dataGrid_page': 1,
            'dataGrid_sortfield': 'anyo',
            'dataGrid_sortdirection': 'desc',
            'dataGrid_recordsOnPage': 100,
        }
        request_response = requests.post(TARGET, data=payload, headers={'User-Agent': getRandomUserAgent()})
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
            print('--- BOOK Nº ', index_book, ' FOUND -------------------------------------------------')
            book_author = td_elements[0].get_text()
            book_title = td_elements[1].get_text()
            book_year = td_elements[2].get_text()
            book_gender = td_elements[3].get_text()
            book_theme = td_elements[4].get_text()

            ref_link = td_elements[1].get('onclick')
            ref_link = ref_link.replace("javascript:document.location.href='..", "")
            ref_link = ref_link.replace("'", "")
            ref_link = DOMAIN + ref_link

            book_cover = getBookImage(ref_link)

            customSleep()
            urlPapyreBookSheet = urllib.request.urlopen(ref_link)
            bookSheetSoup = BeautifulSoup(urlPapyreBookSheet, 'html.parser')
            book_summary = bookSheetSoup.find('p', class_='capitalLetter').get_text()

            # Obtenemos el enlace para descargar el fichero .mobi
            button_element = None

            for link in bookSheetSoup.find_all('a', class_='myButton'):
                if link.text == 'Mobi':
                    button_element = link
                    break
            ref_mobi = None
            ref_download = None
            if button_element:
                ref_mobi = button_element.get('href')
                ref_mobi = ref_mobi.replace("./", "/")
                ref_mobi = DOMAIN + ref_mobi
                ref_mobi = getMobiUrl(ref_mobi)
                ref_download = getMobiId(ref_mobi)

            papyro_book = {
                'book': book_title,
                'author': book_author,
                'year': book_year,
                'gender': book_gender,
                'theme': book_theme,
                'summary': book_summary,
                'cover': book_cover,
                'ref_link': ref_link,
                'ref_mobi': ref_mobi,
                'ref_download': ref_download,
                'saved_date': datetime.now(),
            }
            
            print('--- BOOK DATA -----------------------------------------------')
            for clave, valor in papyro_book.items():
                if clave != 'cover':
                    customPrint(clave, valor)

            saveBook(papyro_book)
            
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


def saveBook(book):
    print('--- BOOK SAVE -----------------------------------------------')
    client = pymongo.MongoClient("localhost:27017")
    database = client["papyre"]
    collection = database["books"]

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
        result = collection.insert_one(book)
        print("ID:", result.inserted_id, "book!")

    client.close()


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


main()
