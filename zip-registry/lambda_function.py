"""関数ハンドラー

イベントから一括更新処理か差分更新処理を実行する

"""
import os
import json
import tempfile
import zip_main

def lambda_handler(event, context):
    """関数ハンドラー
    
    Lambda 関数ハンドラー

    """
    # 一時ディレクトリ作成
    tmpdir = tempfile.TemporaryDirectory()
    dst_dir = tmpdir.name

    if 'all' in event:
        zip_main.all(dst_dir)   # 一括更新
    else:
        zip_main.diff(dst_dir)  # 差分更新

    # print(os.listdir(dst_dir))

    tmpdir.cleanup()
