"""郵便番号データ検索

API Gateway + Lambda + DynamoDB でREST API を構築する

"""
import json
import configparser
import boto3
from boto3.dynamodb.conditions import Key

# iniファイル読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
DYNAMODB_TABLE = config_ini.get('DynamoDB', 'TABLE')
SITE_ID_ZIPCODE = config_ini.get('DEFAULT', 'SITE_ID_ZIPCODE')

def respond(error_code, address=None):
    """レスポンス処理

    Args:
        error_code (str): 5桁のエラーコード
        address (list): 住所一覧

    Returns:
        dic: レスポンス値

    """
    ERROR_CODES = {
        '20000': [200, '20000', '成功', '処理に成功しました'],
        '40000': [400, '40000', 'エラー', 'エラーが発生しました'],
        '40001': [404, '40001', '404エラー', 'リクエストしたリソースが見つかりませんでした'],
        '40003': [400, '40003', 'APIキーエラー', '不正なキーが入力されました'],
        '40004': [403, '40004', 'APIキーエラー', 'APIキーが見つかりませんでした'],
        '40005': [400, '40005', 'ドメインエラー', '許可されていないドメインです'],
        '40006': [403, '40006', 'APIアクセス回数エラー', 'APIキーのアクセスが上限に達しました'],
        '40007': [403, '40007', 'APIアクセス回数エラー', 'アカウント合計のアクセス回数が上限に達しました'],
        '40008': [400, '40008', 'アカウントエラー', 'アカウントが見つかりませんでした'],
        '40009': [400, '40009', 'アカウントエラー', '契約情報が見つかりませんでした'],
        '40010': [403, '40010', 'APIアクセス回数エラー', '短時間でのアクセス回数が多すぎるため制限しました'],
        '40011': [400, '40011', 'アクセス制限', 'アクセスが禁止されています。アクセス方法に問題が無いか確認してください'],
        '40101': [200, '40101', '郵便番号エラー', '郵便番号が入力されておりません'],
        '40102': [200, '40102', '郵便番号エラー', '指定された郵便番号から住所が見つかりません'],
        '40103': [200, '40103', '郵便番号エラー', '郵便番号の形式が正しくありません'],
    }
    ERROR_KEY = ['code', 'title', 'detail']

    error = ERROR_CODES[error_code]
    status_code = error.pop(0)

    if error_code == '40003':
        res = "hide_loading();if(typeof zsResponce=='function') zsResponce({'result':'error','code':'410'});"
    elif error_code == '40004':
        res = "hide_loading();if(typeof zsResponce=='function') zsResponce({'result':'error','code':'412'});"
    elif address and error_code in ['20000']:
        # 成功
        res = "hide_loading();zips({'address':%s});if(typeof zsResponce=='function') zsResponce({'result':'success','code':'200','address':%s});"
        str = json.dumps(address, ensure_ascii=False)
        res = res % (str, str)
    else:
        # エラー
        res = "hide_loading();if(typeof zsResponce=='function') zsResponce({'result':'error','code':'440'});"

    return {
        'statusCode': status_code,
        'body': res,
        'headers': {'Content-Type': 'text/javascript; charset=UTF-8'}
    }

def lambda_handler(event, context):
    """関数ハンドラー
    
    Lambda 関数ハンドラー

    """
    # print("Received event: " + json.dumps(event, indent=2))

    # HTTPメソッドcheck
    operation = event['httpMethod']
    if not operation or operation not in ['POST', 'GET']:
        # 'Unsupported method "{}"'.format(operation)
        return respond('40000')

    # site_idパラメータチェック
    params = event['queryStringParameters']
    if not params or 'site_id' not in params:
        # site_id element is not found
        return respond('40003')
    site_id = params['site_id']
    if len(site_id) == 0:
        return respond('40003')
    elif site_id != SITE_ID_ZIPCODE:
        return respond('40004')

    # zipcodeパラメータ 存在チェック
    if not params or 'zipcode' not in params:
        # zipcode element is not found
        return respond('40101')

    # zipcodeパラメータ 長さチェック
    zipcode = params['zipcode']
    if len(zipcode) == 0:
        return respond('40101')
    elif len(zipcode) < 3 or 7 < len(zipcode):
        # zipcode has format error
        return respond('40103')

    dynamodb = boto3.resource('dynamodb')
    ziptable = dynamodb.Table(DYNAMODB_TABLE)

    # 取得テーブル属性
    COLUMN_NAMES = [
        'zipcode',
        'prefecture',
        'city',
        'town',
        'house_number',
        'company',
        'jiscode',
        'pref_code_JIS',
        'prefecture_hira',
        'prefecture_kata',
        'city_hira',
        'city_kata',
        'town_hira',
        'town_kata',
        'company_hira',
        'company_kata',
    ]
    response = ziptable.query(
        ProjectionExpression=','.join(COLUMN_NAMES),
        KeyConditionExpression=Key('pkey').eq(zipcode[:3]) & Key('skey').begins_with(zipcode)
    )

    items = response['Items']
    if len(items) == 0:
        return respond('40102') # 指定された郵便番号から住所が見つからなかった

    CHG_COLUMN_NAMES = {
        'jiscode': 'city_code', # 属性 jiscode は city_code に置き換える
    }
    for item in items:
        for k in item.keys():
            if isinstance(item[k], str): item[k] = item[k].strip()
            if item[k] is None: item[k] = ''
        for i, j in CHG_COLUMN_NAMES.items():
            item[j] = item.pop(i, None)

    return respond('20000', items)
