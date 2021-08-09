"""共通処理

共通で使用する関数

"""
import os
import pprint
import boto3
import datetime
import configparser

# iniファイル読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
BUCKET_NAME = config_ini.get('S3', 'BUCKET_NAME')
OBJECT_KEY = config_ini.get('S3', 'OBJECT_KEY')

s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

def up_s3(dst_path):
    """S3ファイルアップ処理

    Args:
        dst_path (str): アップするファイルのパス

    """
    fname = os.path.basename(dst_path).lower()
    ext = os.path.splitext(fname)[1]
    if ext == '.csv':
        ctype ='text/csv'
    elif ext == '.zip':
        ctype ='application/zip'
    else:
        raise Exception('Error: up_s3')

    # S3 アップロード
    s3filename = OBJECT_KEY + fname
    with open(dst_path, 'rb') as body_file:
        response = s3.Bucket(BUCKET_NAME).put_object(
            Key = s3filename, Body = body_file, ContentType = ctype)

def get_s3_list():
    """S3ファイルリスト取得

    Returns:
        list: ファイルリスト

    """
    result = s3_client.list_objects(Bucket=BUCKET_NAME, Prefix=OBJECT_KEY)
    try:
        keys = [content['Key'] for content in result['Contents']]
    except KeyError:
        keys = []
    return keys

def lastmonth():
    """先月の年月取得

    Returns:
        str: 先月の年月

    """
    today = datetime.datetime.today()
    thismonth = datetime.datetime(today.year, today.month, 1)
    lastmonth = thismonth + datetime.timedelta(days=-1)
    return lastmonth.strftime("%y%m")
