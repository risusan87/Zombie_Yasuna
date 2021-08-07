import json
from itertools import filterfalse
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
                return _data

        return self.thread_pool.submit(_i)

    def write(self, data: dict, removeMode=False, forceWrite=False, overwrite=False) -> Future:
        if overwrite:
            def _ow():
                with open(mode='w', file=self.file_path) as file_f:
                    json.dump(data, file_f, indent=4)
            return self.thread_pool.submit(_ow)

        def _appendThrough(old_data: dict, new_data: dict) -> dict:
            #_=元々あったやつ
            fin_dic = old_data
            for key in new_data:
                if key in old_data and type(old_data[key]) is type(new_data[key]) if not forceWrite else True:
                    if type(new_data[key]) is dict:
                        if removeMode and len(new_data[key]) == 0:
                            del fin_dic[key]
                            continue
                        fin_dic[key] = _appendThrough(old_data[key], new_data[key])
                    elif type(new_data[key]) is list:
                        if removeMode:
                            if len(new_data[key]) == 0:
                                del fin_dic[key]
                                continue
                            else:
                                n_list = []
                                for e in old_data[key]:
                                    if e not in new_data[key]:
                                        n_list.append(e)
                                fin_dic[key] = n_list
                                continue
                        o_list = old_data[key]
                        o_list.extend(new_data[key])
                        fin_dic[key] = o_list
                    else:
                        if removeMode:
                            del fin_dic[key]
                            continue
                        fin_dic[key] = new_data[key] if forceWrite else old_data[key]
                else:
                    if removeMode:
                        continue
                    fin_dic[key] = new_data[key]
            return fin_dic
        def _o():
            with open(mode='r', file=self.file_path) as file_f:
                o_data = json.load(file_f)
            with open(mode='w', file=self.file_path) as file_f:
                json.dump(_appendThrough(old_data=o_data, new_data=data), file_f, indent=4)
        return self.thread_pool.submit(_o)
