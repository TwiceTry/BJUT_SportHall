import json
from pathlib import Path
import logging


def getlogger(level=logging.DEBUG, format="%(asctime)s %(name)s %(levelname)s %(message)s", dateformat='%Y-%m-%d  %H:%M:%S %a ', logfile="log.txt"):
    mylog = logging.RootLogger(level)  # logging.Logger(name='my',level='INFO')
    if format:
        LOG_FORMAT = format
    if dateformat:
        DATE_FORMAT = dateformat
    if logfile:
        LOG_FILE = logfile
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    mylog.addHandler(fh)
    mylog.addHandler(ch)
    return mylog


class HTMLFileStorage:
    def __init__(self, directory: str):
        self.directory = Path(directory)

    def is_existed(self, filename: str) -> bool:
        file_path = self.directory / filename
        return file_path.exists()

    def getOrderIds(self):
        OrderIdList = [self.nameToOderId(fileName.name)
                       for fileName in self.directory.glob('*.html')]
        OrderIdList.sort()
        return OrderIdList

    def mkName(self, OrderId: str) -> str:
        return f'order_{OrderId}.html'

    def nameToOderId(self, fileName: str) -> str:
        return fileName.split('_')[1].split('.')[0]

    def save_html(self, OrderId: str, html_content: str):
        filename = self.mkName(OrderId)
        # 创建目录（如果不存在）
        self.directory.mkdir(parents=True, exist_ok=True)

        # 构建文件路径
        file_path = self.directory / filename

        # 将 HTML 内容写入文件
        with open(file_path, 'w') as file:
            file.write(html_content)

    def get_html(self, OrderId: str):
        filename = self.mkName(OrderId)
        file_path = self.directory / filename
        if file_path.exists():
            return file_path.read_text()
        else:
            return None


class JSONHandler:
    def __init__(self, file_path, default={}):
        self.file_path = Path(file_path)
        # 检查文件是否存在，如果不存在则创建新文件
        if not self.file_path.exists():
            self.write_json({})

    def read_json(self):
        with self.file_path.open('r') as file:
            data = json.load(file)
        return data

    def write_json(self, data):
        with self.file_path.open('w') as file:
            json.dump(data, file, indent=4, ensure_ascii=False, sort_keys=True)

    def get_value(self, key):
        data = self.read_json()
        return data.get(key)

    def set_value(self, key, value):
        data = self.read_json()
        data[key] = value
        self.write_json(data)

    def delete_key(self, key):
        data = self.read_json()
        if key in data:
            del data[key]
            self.write_json(data)
