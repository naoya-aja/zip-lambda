"""郵便番号検索JavaScript

郵便番号検索で使用するJavaScriptを返却

"""
import json
import configparser

# iniファイル読み込み
config_ini = configparser.ConfigParser()
config_ini.read('config.ini', encoding='utf-8')
API_URL = config_ini.get('DEFAULT', 'API_URL')

def lambda_handler(event, context):
    """関数ハンドラー
    
    Lambda 関数ハンドラー

    """
    if 'resource' in event:
        if event['resource'] == '/zip-js':
            with open('zip-js.tmpl', 'r', encoding='UTF-8') as f:
                data = f.read()
                data = data.replace('***api_url***', API_URL)
            return {
                'statusCode': 200,
                'body': data,
                'headers': {
                    'Content-Type': 'text/javascript; charset=UTF-8',
                },
            }

    return {
        'statusCode': 404,
        'body': json.dumps({'message': '404 Not Found'})
    }
