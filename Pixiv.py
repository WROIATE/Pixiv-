import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import os, re, time


class Pixiv:
    def __init__(self):
        self.url = {
            'daily': 'https://www.pixiv.net/ranking.php?mode=daily',
            'weekly': 'https://www.pixiv.net/ranking.php?mode=weekly',
            'monthly': 'https://www.pixiv.net/ranking.php?mode=monthly',
            'collection': 'https://www.pixivision.net',
            'pic_url': 'https://i.pximg.net/img-original/img/'
        }
        self.header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36'
        }
        self.p_header = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
            'referer': ''}
        self.html = ""
        self.id = []
        self.data_src = []
        self.id_url = {}
        self.PATH = ""
        self.mode = self.menu()
        self.make_path(self.mode)
        self.main()

    def get_html(self):
        r = requests.get(self.url['daily'], headers=self.header)
        self.html = r.content

    async def select_id(self, data_src):
        pa = r'(\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2}/)(\d{8})_(\w+)(\.\w{3})'
        list = re.search(pa, data_src).groups()
        self.id_url[list[1]] = self.url['pic_url'] + list[0] + list[1] + "_" + 'p0'
        self.id.append(list[1])

    def get_src(self):
        html = BeautifulSoup(self.html, 'lxml')
        tag = html.select("section.ranking-item div.ranking-image-item a div img")
        for i in tag:
            self.data_src.append(i.get("data-src"))

    async def create_url(self):
        task = [asyncio.create_task(self.select_id(i)) for i in self.data_src]
        tasks = asyncio.gather(*task)
        await tasks

    async def download(self, session, url, id):
        head = self.p_header
        try:
            head['referer'] = url + ".png"
            async with session.get(head['referer'], headers=head) as response:
                assert response.status == 200
                print("%s download start" % id)
                await self.save(await response.read(), id, ".png")
        except:
            try:
                head['referer'] = url + ".jpg"
                async with session.get(head['referer'], headers=head) as response:
                    assert response.status == 200
                    print("id=%s download start" % id)
                    await self.save(await response.read(), id, ".jpg")
            except:
                print("%s connect error" % id)

    async def save(self, data, id, last):
        with open(os.path.join(self.PATH, id + last), 'ab') as f:
            f.write(data)
            print("id=%s download completed" % id)

    def make_path(self, mode):
        date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        self.PATH = os.path.join(os.path.abspath('.'), mode + '-' + date)
        if not os.path.exists(self.PATH):
            os.mkdir(self.PATH)

    async def connect(self):
        async with aiohttp.ClientSession() as session:
            task = [asyncio.create_task(self.download(session, self.id_url[i], i)) for i in self.id]
            tasks = asyncio.gather(*task)
            await tasks

    def menu(self):
        i = input("which mode do you desire to download?(d;w;m):")
        if i == "d":
            return "daily"
        elif i == "w":
            return "weekly"
        elif i == "m":
            return "monthly"
        else:
            print("input error,try again!")
            return self.menu()

    def main(self):
        t = time.time()
        self.get_html()
        self.get_src()
        asyncio.run(self.create_url())
        asyncio.run(self.connect())
        print("used time:", round((time.time() - t), 2), "s")
        os.system("explorer.exe %s" % self.PATH)
        input("Press <enter>")


if __name__ == "__main__":
    p = Pixiv()
