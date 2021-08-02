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
                _data = json.load(file_f)
                file_f.close()
                return _data

        return self.thread_pool.submit(_i)

    def appendWrite(self, data: dict) -> Future:
        """データの付け足しを行います。
        戻り値からresult()を呼ぶことで処理の同期待ちをします。
        :param data:
        Data in dictionary object to be appended
        :return:
        Future object
        """
        def _o():
            with open(mode='r', file=self.file_path) as file_f:
                old_data = json.load(file_f)
                file_f.close()
            with open(mode='w', file=self.file_path) as file_f:
                for k in data.keys():
                    old_data[k] = data[k]
                json.dump(old_data, file_f, indent=4)
                file_f.close()
                return

        return self.thread_pool.submit(_o)

    def overwrite(self, data: dict) -> Future:
        """データの上書きを行います。
        元々のデータは消えるので１から書き直すときのみ使用します。
        戻り値からresult()を呼ぶことで処理の同期待ちをします。
        :param data:
        Data to be over-written
        :return:
        """
        def _ow():
            with open(mode='w', file=self.file_path) as file_f:
                json.dump(data, file_f, indent=4)
                file_f.close()
                return

        return self.thread_pool.submit(_ow)
