"""郵便番号DB処理

CSVデータからDynamoDBに登録、削除を行う。

"""
import csv
import json
import sys
import datetime
import boto3
from boto3.dynamodb.conditions import Key, Attr
import uuid
import configparser

# iniファイル読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
DYNAMODB_TABLE = config_ini.get('DynamoDB', 'TABLE')

DB_KEY = [
    'jiscode',
    'zipcode_old',
    'zipcode',
    'prefecture_halfkata',
    'city_halfkata',
    'town_halfkana',
    'prefecture',
    'city',
    'town_org',
    'flag1',
    'flag2',
    'flag3',
    'flag4',
    'flag5',
    'flag6',
    'company_halfkana',
    'company',
    'house_number',
    'post_office',
    'flag7',
    'flag8',
    'flag9',
    'prefecture_hira',
    'prefecture_kata',
    'city_hira',
    'city_kata',
    'town_hira',
    'town_kata',
    'company_hira',
    'company_kata',
    'pref_code_JIS',
    'town',
]

dynamodb = boto3.resource('dynamodb')
ziptable = dynamodb.Table(DYNAMODB_TABLE)

def del_items(in_csv):
    """削除処理

    Args:
        in_csv (str): CSVファイルパス

    """
    with open(in_csv) as fi:
        reader = csv.reader(fi)
        for row in reader:
            item = dict(zip(DB_KEY, row))
            zipcode = item['zipcode']
            town_org = item['town_org'].strip()
            if town_org == '': town_org = None

            options = {
                'KeyConditionExpression': Key('pkey').eq(zipcode[:3]) & Key('skey').begins_with(zipcode),
                'FilterExpression': Attr('town_org').eq(town_org),
            }
            response = ziptable.query(**options)
            items = response['Items']
            for item in items:
                pkey = item['pkey']
                skey = item['skey']
                # print('** del_item pkey: %s, skey: %s' % (pkey, skey))
                ziptable.delete_item(Key={'pkey': pkey, 'skey': skey})

def put_items(in_csv):
    """登録処理

    Args:
        in_csv (str): CSVファイルパス

    """
    with open(in_csv) as fi, ziptable.batch_writer() as batch:
        for row in csv.reader(fi):
            item = dict(zip(DB_KEY, row))
            zipcode = item['zipcode']
            item['pkey'] = zipcode[:3]
            item['skey'] = "%s-%s" % (zipcode, str(uuid.uuid4()))

            for k, v in item.items():
                item[k] = v.strip()
                if v == '': item[k] = None

            # print('** put_items pkey: %s, skey: %s' % (item['pkey'], item['skey']))
            batch.put_item(Item=item)
