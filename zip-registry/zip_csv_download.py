"""郵便番号データダウンロード

日本郵便HPより、郵便番号データを取得する。
ZIPファイルの解凍、文字コード変換を行う。

"""
import sys
import os
import pprint
import urllib.error
import urllib.request
import zipfile
import codecs
import tempfile
import boto3
from botocore.exceptions import ClientError
import datetime
import time
import shutil
import pathlib
import configparser
import zip_lib

# iniファイル読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
KEN_URL = config_ini.get('Download', 'KEN_URL')
JIGYOSYO_URL = config_ini.get('Download', 'JIGYOSYO_URL')
KEN_ALL_FN = config_ini.get('Download', 'KEN_ALL_FN')
JIGYOSYO_ALL_FN = config_ini.get('Download', 'JIGYOSYO_ALL_FN')
KEN_ADD_FN = config_ini.get('Download', 'KEN_ADD_FN')
KEN_DEL_FN = config_ini.get('Download', 'KEN_DEL_FN')
JIGYOSYO_ADD_FN = config_ini.get('Download', 'JIGYOSYO_ADD_FN')
JIGYOSYO_DEL_FN = config_ini.get('Download', 'JIGYOSYO_DEL_FN')

def download_file(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file, open(dst_path, 'wb') as local_file:
            local_file.write(web_file.read())
    except urllib.error.URLError as e:
        raise
        # raise Exception('Error: download_file')

def download_file_to_dir(url, dst_dir):
    download_file(url, os.path.join(dst_dir, os.path.basename(url)))

def change_code(shiftjis_csv_path, utf8_csv_path):
    """文字コード変換処理

    cp932 から utf-8 に文字コード変換

    Args:
        shiftjis_csv_path (str): CSVファイルパス（変換元）
        utf8_csv_path (str): CSVファイルパス（変換先）

    """
    # 文字コードを utf-8 に変換して保存
    # fin = codecs.open(shiftjis_csv_path, "r", "shift_jis")
    fin = codecs.open(shiftjis_csv_path, "r", "cp932")
    fout_utf = codecs.open(utf8_csv_path, "w", "utf-8")
    for row in fin:
        fout_utf.write(row)
    fin.close()
    fout_utf.close()

def download(base_url, dst_dir, fname):
    """各ダウンロードメイン

    Args:
        base_url (str): ダウンロードディレクトリ
        dst_dir (str): 出力ディレクトリ
        fname (str): ダウンロードファイル名

    """
    url = base_url + fname
    download_file_to_dir(url, dst_dir)

    dst_path = dst_dir + '/' + fname
    ext_dir = dst_dir + '/ext'

    try:
        with zipfile.ZipFile(dst_path) as existing_zip:
            ext_names = existing_zip.namelist()
            existing_zip.extractall(ext_dir)
    except Exception as e:
        raise

    zip_lib.up_s3(dst_path)
    os.remove(dst_path)

    if len(ext_names) <= 0:
        print('zip file error')
        raise Exception('Error: zip file')

    ext_name = ext_names[0]

    in_csv = ext_dir + '/' + ext_name
    out_csv = dst_dir + '/' + os.path.splitext(fname)[0] + '.csv'

    change_code(in_csv, out_csv)
    shutil.rmtree(ext_dir + '/')

def dl_all(dst_dir):
    """一括データダウンロード処理

    以下一括データの処理
    ・住所の郵便番号（読み仮名データの促音・拗音を小書きで表記するもの）
    ・事業所の個別郵便番号

    Args:
        dst_dir (str): 一時ディレクトリ（作業用）

    """
    title = '一括更新:住所の郵便番号'
    try:
        download(KEN_URL, dst_dir, KEN_ALL_FN)
    except urllib.error.URLError as e:
        print('[%s]ダウンロードできませんでした(%s)' % (title, KEN_ALL_FN))

    title = '一括更新:事業所の個別郵便番号'
    try:
        download(JIGYOSYO_URL, dst_dir, JIGYOSYO_ALL_FN)
    except urllib.error.URLError as e:
        print('[%s]ダウンロードできませんでした(%s)' % (title, JIGYOSYO_ALL_FN))

def dl_diff_data(dst_dir):
    """差分更新ダウンロード処理

    以下先月分差分データの処理
    ・住所の郵便番号（読み仮名データの促音・拗音を小書きで表記するもの）
    ・事業所の個別郵便番号

    Args:
        dst_dir (str): 一時ディレクトリ（作業用）

    """
    ym = zip_lib.lastmonth()
    fn_add = KEN_ADD_FN % ym
    fn_del = KEN_DEL_FN % ym
    fn_jadd = JIGYOSYO_ADD_FN % ym
    fn_jdel = JIGYOSYO_DEL_FN % ym
    kogaki_dir = dst_dir + '/kogaki'
    jigyosyo_dir = dst_dir + '/jigyosyo'

    list = []
    for path in zip_lib.get_s3_list():
        if path[-1] == '/': continue
        p_file = pathlib.Path(path)
        list.append(p_file.name)

    title = '差分更新:住所の郵便番号'
    if fn_add in list or fn_del in list:
        print('[%s]S3ファイルが存在します(%s, %s)' % (title, fn_add, fn_del))
    else:
        try:
            os.mkdir(kogaki_dir)
            download(KEN_URL, kogaki_dir, fn_add)
            download(KEN_URL, kogaki_dir, fn_del)
            for fn in os.listdir(kogaki_dir):
                shutil.move(
                    '%s/%s' % (kogaki_dir, fn),
                    '%s/%s' % (dst_dir, fn)
                )
        except urllib.error.URLError as e:
            print('[%s]ダウンロードできませんでした(%s, %s)'
                % (title, fn_add, fn_del))
        finally:
            shutil.rmtree(kogaki_dir + '/')
            
    title = '差分更新:事業所の個別郵便番号'
    if fn_jadd in list or fn_jdel in list:
        print('[%s]S3ファイルが存在します(%s, %s)'
            % (title, fn_jadd, fn_jdel))
    else:
        try:
            os.mkdir(jigyosyo_dir)
            download(JIGYOSYO_URL, jigyosyo_dir, fn_jadd)
            download(JIGYOSYO_URL, jigyosyo_dir, fn_jdel)
            for fn in os.listdir(jigyosyo_dir):
                shutil.move(
                    '%s/%s' % (jigyosyo_dir, fn),
                    '%s/%s' % (dst_dir, fn)
                )
        except urllib.error.URLError as e:
            print('[%s]ダウンロードできませんでした(%s, %s)'
                % (title, fn_jadd, fn_jdel))
        finally:
            shutil.rmtree(jigyosyo_dir + '/')
    