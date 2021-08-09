"""メイン処理

一括更新処理、差分更新処理のメイン処理

"""
import os
import json
import jaconv
import tempfile
import shutil
import boto3
import zip_lib
import zip_csv_download
import zip_csv_compile
import zip_db
import pathlib

def all(dst_dir):
    """一括更新処理
    
    Dynamoテーブルを新規作成し、空の状態で実行する。

    Args:
        dst_dir (str): 一時ディレクトリ

    """
    # ダウンロード
    zip_csv_download.dl_all(dst_dir)
    
    # 変換処理
    out_csv = '%s/%s' % (dst_dir, 'zip_all.csv')

    in_csv = '%s/%s' % (dst_dir,
        '%s.csv' % pathlib.Path(zip_csv_download.KEN_ALL_FN).stem)
    if not os.path.isfile(in_csv): return
    zip_csv_compile.ken_make(in_csv, out_csv)
    os.remove(in_csv)

    in_csv = '%s/%s' % (dst_dir,
        '%s.csv' % pathlib.Path(zip_csv_download.JIGYOSYO_ALL_FN).stem)
    if not os.path.isfile(in_csv): return
    zip_csv_compile.jigyosyo_make(in_csv, out_csv)
    os.remove(in_csv)

    zip_lib.up_s3(out_csv)
    
    # DB登録
    zip_db.put_items(out_csv)

def diff(dst_dir):
    """差分更新処理

    Args:
        dst_dir (str): 一時ディレクトリ

    """
    dl_dir = dst_dir + '/dl'
    out_dir = dst_dir + '/out'
    os.mkdir(dl_dir)
    os.mkdir(out_dir)

    # ダウンロード
    zip_csv_download.dl_diff_data(dl_dir)

    # 変換処理
    list = os.listdir(dl_dir)
    if not list: return
    for fn in list:
        in_csv = '%s/%s' % (dl_dir, fn)
        out_csv = '%s/%s' % (out_dir, fn)
        if fn.startswith('add_') or fn.startswith('del_'):
            zip_csv_compile.ken_make(in_csv, out_csv)
            os.remove(in_csv)
            zip_lib.up_s3(out_csv)
        elif fn.startswith('jadd') or fn.startswith('jdel'):
            zip_csv_compile.jigyosyo_make(in_csv, out_csv)
            os.remove(in_csv)
            zip_lib.up_s3(out_csv)
    shutil.rmtree(dl_dir)

    # DB削除、登録
    list = os.listdir(out_dir)
    if not list: return
    for arr in [['del_', 'add_'], ['jdel', 'jadd']]:
        del_sw, add_sw = arr
        del_fn = add_fn = None
        for fn in list:
            if fn.startswith(del_sw): del_fn = fn
            if fn.startswith(add_sw): add_fn = fn
        if del_fn and add_fn:
            zip_db.del_items('%s/%s' % (out_dir, del_fn))
            zip_db.put_items('%s/%s' % (out_dir, add_fn))
