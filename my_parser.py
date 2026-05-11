import pycurl
import re
from bs4 import BeautifulSoup
from io import BytesIO
import json
import threading


class Parser():
    def __init__(self):
        self.dict_quality = {}
        self.sorted_result = ()
        self.parsed_pages = []
        self.count_parsed_pages = 0
        self.lock_search = threading.Lock()
        
    def download_page(self, page_url):
        try:
            buffer = BytesIO()
            c = pycurl.Curl()
            c.setopt(c.URL, page_url)
            c.setopt(c.WRITEDATA, buffer)
            c.perform()
            c.close()
            html_bytes = buffer.getvalue()
            html_content = html_bytes.decode('utf-8')
            return BeautifulSoup(html_content, 'html.parser')
        except Exception:
            print("Ошибка при загрузке страницы")
        
    def parse_vacancy_page(self, page_url):
            if page_url not in self.parsed_pages:
                self.parsed_pages.append(page_url)
                page = self.download_page(page_url)
                try:
                    skill_list = page.find('ul', class_='vacancy-skill-list--JsTYRZ5o6dsoavK7')
                    items = skill_list.find_all('div', class_='magritte-tag__label___YHV-o_5-2-2')
                    for item in items:
                        if item.text not in self.dict_quality.keys():
                            self.dict_quality[item.text] = 1
                        else:
                            self.dict_quality[item.text] += 1
                except Exception:
                    pass
                
    def parse_vacancies_page(self, page_url):
        with self.lock_search:
                page = self.download_page(page_url)
                try:
                    threads = []
                    items = page.find_all('div', class_='loading-target--I1Dlz1LKeYSUDaFk')
                    for item in items: 
                        name_vacancy = item.find('span', class_="magritte-text___tkzIl_7-1-17")
                        #print("VACANCY NAME:", name_vacancy.text, end="\n")
                        name_link = item.find('a', class_="magritte-link___b4rEM_7-1-17")
                        self.parse_vacancy_page(name_link.get('href'))
                    self.count_parsed_pages += 1
                    print("COUNT PARCED PAGES", self.count_parsed_pages, end="\r")
                except Exception:
                    print("Ошибка при парсинге поисковой страницы\n", page_url)
        
    def parse_main_page(self, page_url):
        threads = []
        page = self.download_page(page_url)
        
        pattern = re.compile(r'search/vacancy')
        links = page.find_all('a', href=pattern)
        link_length = len(links)
        for item0 in range(link_length):
            print(f"NUMBER OF LINKS {len(links)}", end='\r')
            deep_items0 = self.download_page("https://vladimir.hh.ru" + links[item0].get('href')).find_all('a', href=pattern)
            deep_items0_length = len(deep_items0)
            for item1 in range(deep_items0_length):
                deep_items1 = self.download_page("https://vladimir.hh.ru" + deep_items0[item1].get('href')).find_all('a', href=pattern)
                deep_items0 += deep_items1
            links += deep_items0
        links = list(set(links))
        print(f"FINAL NUMBER OF LINKS {len(links)}", end='\n')
        
        for item in links:
            t = threading.Thread(target=self.parse_vacancies_page, args=("https://vladimir.hh.ru" + item.get('href'),))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        print()
        print("COUNT OF PARCED VACANCIES", len(self.parsed_pages))
        self.sort_result()
        self.save_result()
        self.load_result()
            
    def sort_result(self):
        self.sorted_result = tuple(sorted(self.dict_quality.items(), key=lambda x: x[1], reverse=True)[:10])
    def save_result(self):
        with open('sorted_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.sorted_result, f, ensure_ascii=False, indent=2)
    def load_result(self):
        with open('sorted_data.json', 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            loaded_tuple = tuple(loaded_data)
            print("RESULT TABLE:")
            for i in loaded_tuple:
                print(i[1], i[0])


if __name__ == "__main__":
    parser = Parser()
    parser.parse_main_page("https://vladimir.hh.ru/")
