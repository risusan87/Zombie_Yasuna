import json
from concurrent.futures import ThreadPoolExecutor, Future


class JsonIO:
    """Jsonファイルの読み込み/書き込みの同期用クラス
    インスタンス時はfileキーにjsonへのパスを拡張子付きで指定します。
    オブジェクトからはread() write()メソッドで読み込み書き込みを行います。
    各メソッドはconcurrent.futures.Futureオブジェクトを戻り値とともに返却します。
    """
    def __init__(self, file: str):
        self.thread_pool = ThreadPoolExecutor(max_workers=1)
        self.file_path = file

    def read(self) -> Future:
        """ファイルの読み込みを行います。
        戻り値からresult()を呼ぶことで処理の同期待ちをすると共に読み込んだデータを辞書として返却します。
        :return:
        Future object containing data as a dictionary object
        """
        def _i():
            with open(mode='r', file=self.file_path) as file_f:
                return json.load(file_f)

        return self.thread_pool.submit(_i)

    def write(self, data: dict) -> Future:
        """ファイルの書き込みを行います。
        戻り値からresult()を呼ぶことで処理の同期待ちをします。
        :param data:
        Data in dictionary object to be over-written
        :return:
        Future object
        """
        def _o():
            with open(mode='w', file=self.file_path) as file_f:
                json.dump(data, file_f, indent=4)

        return self.thread_pool.submit(_o)
