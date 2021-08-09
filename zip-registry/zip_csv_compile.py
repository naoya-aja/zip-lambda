"""郵便番号データ変換処理

以下の変換処理を行う。
・全角ひらがな、全角カタカナ変換
・都道府県JISコード
・町域名の修正
・項目の並べ替え

"""
import csv
import pprint
import jaconv

# 都道府県コード
PREF_JIS_CODES = {
    '北海道'    : '01',
    '青森県'    : '02',
    '岩手県'    : '03',
    '宮城県'    : '04',
    '秋田県'    : '05',
    '山形県'    : '06',
    '福島県'    : '07',
    '茨城県'    : '08',
    '栃木県'    : '09',
    '群馬県'    : '10',
    '埼玉県'    : '11',
    '千葉県'    : '12',
    '東京都'    : '13',
    '神奈川県'  : '14',
    '新潟県'    : '15',
    '富山県'    : '16',
    '石川県'    : '17',
    '福井県'    : '18',
    '山梨県'    : '19',
    '長野県'    : '20',
    '岐阜県'    : '21',
    '静岡県'    : '22',
    '愛知県'    : '23',
    '三重県'    : '24',
    '滋賀県'    : '25',
    '京都府'    : '26',
    '大阪府'    : '27',
    '兵庫県'    : '28',
    '奈良県'    : '29',
    '和歌山県'  : '30',
    '鳥取県'    : '31',
    '島根県'    : '32',
    '岡山県'    : '33',
    '広島県'    : '34',
    '山口県'    : '35',
    '徳島県'    : '36',
    '香川県'    : '37',
    '愛媛県'    : '38',
    '高知県'    : '39',
    '福岡県'    : '40',
    '佐賀県'    : '41',
    '長崎県'    : '42',
    '熊本県'    : '43',
    '大分県'    : '44',
    '宮崎県'    : '45',
    '鹿児島県'  : '46',
    '沖縄県'    : '47',
}

ZEN_DEL_WORD = '以下に掲載がない場合'
HALF_DEL_WORD = 'ｲｶﾆｹｲｻｲｶﾞﾅｲﾊﾞｱｲ'
ZEN_ST = '（'
ZEN_END = '）'
HALF_ST = '('

def zenkaku(halfkata):
    """全角ひらがな、カタカナ変換
    
    Args:
        halfkata (str): 半角カタカナ

    Returns:
        list: 変換された全角ひらがなと全角カタカナ

    """
    kata = jaconv.h2z(halfkata, digit=True, ascii=True)
    hira = jaconv.kata2hira(kata)
    return [hira, kata]

def ken_make(in_csv, out_csv):
    """住所の郵便番号の変換処理

    Args:
        in_csv (str): CSVファイル（変換元）
        out_csv (str): CSVファイル（変換後出力先）

    """
    del_mode = False
    with open(in_csv) as fi, open(out_csv, 'a') as fw:
        reader = csv.reader(fi)
        writer = csv.writer(fw)

        for row in reader:
            town = row[8]       # 町域名（漢字）
            if del_mode == True:
                ei = town.find(ZEN_END)
                if ei >= 0: del_mode = False
                continue

            # 変換処理
            town_halfkana = row[5]  # 町域名（半角カタカナ）
            if town_halfkana == HALF_DEL_WORD: town_halfkana = ''
            if town == ZEN_DEL_WORD: town = ''
            si = town_halfkana.find(HALF_ST)
            if si >= 0: town_halfkana = town_halfkana[:si]
            si = town.find(ZEN_ST)
            ei = town.find(ZEN_END)
            if si >= 0: town = town[:si]
            if si >= 0 and ei < 0: del_mode = True

            for i in range(7): row.append('')

            row += zenkaku(row[3])          # 都道府県名（半角カタカナ）
            row += zenkaku(row[4])          # 市区町村名（半角カタカナ）
            row += zenkaku(town_halfkana)   # 町域名（半角カタカナ）

            for i in range(2): row.append('')

            row.append(PREF_JIS_CODES[row[6]])  # 都道府県コード
            row.append(town)                    # 町域名（漢字）
            writer.writerow(row)

def jigyosyo_make(in_csv, out_csv):
    """事業所の個別郵便番号の変換処理

    Args:
        in_csv (str): CSVファイル（変換元）
        out_csv (str): CSVファイル（変換後出力先）

    """
    del_mode = False
    with open(in_csv) as fi, open(out_csv, 'a') as fw:
        reader = csv.reader(fi)
        writer = csv.writer(fw)

        for row in reader:
            town = row[5]       # 町域名（漢字）
            if del_mode == True:
                ei = town.find(ZEN_END)
                if ei >= 0: del_mode = False
                continue

            # 変換処理
            if town == ZEN_DEL_WORD: town = ''
            si = town.find(ZEN_ST)
            ei = town.find(ZEN_END)
            if si >= 0: town = town[:si]
            if si >= 0 and ei < 0: del_mode = True

            out_row = [''] * 32
            chenge_tbl = [0, 15, 16, 6, 7, 8, 17, 2, 1, 18, 19, 20, 21]

            for i, j in enumerate(chenge_tbl):
                out_row[j] = row[i]

            out_row[28:30] = zenkaku(out_row[15])       # 大口事業所名（半角カタカナ）
            out_row[30] = PREF_JIS_CODES[out_row[6]]    # 都道府県コード
            out_row[31] = town                          # 町域名（漢字）
            writer.writerow(out_row)
