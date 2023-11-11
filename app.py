import os
import openai
import pandas as pd
from PIL import Image
import streamlit as st
from gsheetsdb import connect
from wordcloud import WordCloud
from janome.tokenizer import Tokenizer
import matplotlib.pyplot as plt
import settings

CATNAME_URL = settings.CATNAME_URL
CATLOG_URL = settings.CATLOG_URL
GOOGLE_FORM = settings.GOOGLE_FORM
CAT_WEIGHT_URL = settings.CAT_WEIGHT_URL

openai.organization = os.environ.get("OPENAI_ORGANIZATION")
openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_CatName(sheet_url): 
    query = f'SELECT * FROM "{sheet_url}"'
    conn = connect()
    rows = conn.execute(query, headers=1) 
    row_list = []
    for row in rows:
        row_list.append(row.Cat_Name)
    return row_list

# ネコの体重計をプロットする
def plot_CatWeight(sheet_url): 
    query = f'SELECT * FROM "{sheet_url}"'
    conn = connect()
    rows = conn.execute(query, headers=3) 
    
    data_frame = pd.DataFrame(columns=["timestamp","weight_diff","weight"])

    data = []
    for row in rows:
        return_data = {
            "timestamp": row._0,
            "weight_diff": row._1,
            "weight": row._2
        }
        data.append(return_data)

    data_frame = pd.concat([data_frame, pd.DataFrame(data)])
    data_frame = data_frame.dropna()
    data_frame = data_frame[:1000]
    return data_frame

def get_Catlog(sheet_url):
    query = f'SELECT * FROM "{sheet_url}"'
    conn = connect()
    rows = conn.execute(query, headers=0) 

    data_frame = pd.DataFrame(columns=["timestamp","catname","ymd","hhmm","place","action_type","food_type","food_amount","data1","data2","comment","is_athletic"])

    data = []
    for row in rows:
        return_data = {
            "timestamp": row.タイムスタンプ,
            "catname": row._1,
            "ymd": row._2,
            "hhmm": row._3,
            "place": row._4,
            "action_type": row._5,
            "food_type": row._6,
            "food_amount": row._7,
            "data1": row._8,
            "data2": row._9,
            "comment": row.特記事項,
            "is_athletic": row.運動会,
        }
        data.append(return_data)

    data_frame = pd.concat([data_frame, pd.DataFrame(data)])

    return data_frame

# 猫の名前取得
cat_name = get_CatName(CATNAME_URL)
cat_dataframe = get_Catlog(CATLOG_URL)

# ヘッダー
img = Image.open('./images/brand_logo.png')
st.image(img, width= 200)
st.markdown("##### ダッシュボード")

# ネコセレクター
option_cat_name = st.selectbox(
   "ネコを選択してください",
   tuple(cat_name),
   placeholder="Select contact method...",
)

left_col, right_col = st.columns(2)

with left_col:
    # アイコン・名前
    cat_icon, cat_name = st.columns(2)
    with cat_icon:
        img = Image.open('./images/icon_cat.jpg')
        img = img.resize((200, 200))
        st.image(img)
    with cat_name:
        st.markdown("### {}".format(option_cat_name))

    # 気になること
    st.markdown("### 気になること")
    ## 今気になっていることラジオボタン選択式
    genre = st.radio(
        "今、気になっていることは何ですか?",
        [
            "食事をよく残すので、食欲不振か心配だ", 
            "特定の食材を避けているので、アレルギーがあるかもしれない", 
            "トイレの回数が減って心配だ", 
            "いつもと違う場所で過ごしている"
        ],
        index=None,
    )
    ## 他のペットオーナーの気になっているワードクラウド
    st.markdown("##### 他のペットオーナーは\n##### こんなことが気になっています")
    text_data = cat_dataframe['place'].tolist() + cat_dataframe['action_type'].tolist() + cat_dataframe['food_amount'].tolist() +  cat_dataframe['comment'].tolist() + cat_dataframe['is_athletic'].tolist()
    tk = Tokenizer(wakati=True)
    text_data = ''.join(str(text_data))
    text_data = text_data.replace("None","")
    tokens = tk.tokenize(text_data)
    words = " ".join(list(tokens))
    wordcloud = WordCloud(font_path=r"/System/Library/Fonts/Hiragino Sans GB.ttc").generate(words)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    plt.axis("off")
    plt.tight_layout()
    plt.imshow(wordcloud, interpolation='bilinear')
    st.pyplot()


observation = ""
with right_col:
    # 直近のアクション
    st.markdown("### 直近のアクション")
    # st.code(f"""
    # 11/11 11:30ごろ
    # いつものネコ用ベッドで
    # クッションをモミモミしていた
    # """)
    ## ネコのアクション記録フォームから取得
    concern_thing_text = cat_dataframe[cat_dataframe['catname'] == option_cat_name]
    concern_thing_text = concern_thing_text.reset_index()
    if len(concern_thing_text) !=0:
        observation = concern_thing_text['comment'][len(concern_thing_text)-1]
        if observation is not None:
            recent_action =  str(concern_thing_text['ymd'][len(concern_thing_text)-1]) + "に\n" + str(concern_thing_text['place'][len(concern_thing_text)-1]) + "で\n" + observation
            st.code(recent_action)
        else:
            st.code(None)
        st.link_button("アクションを記録する", GOOGLE_FORM)

    # グラフ
    st.markdown("### グラフ")
    ## ネコの体重計
    data = plot_CatWeight(CAT_WEIGHT_URL)
    st.line_chart(data, x = 'timestamp', y = 'weight') 

# ワンポイントアドバイス（直近のアクションより生成）
# observation = "11/11 11:30ごろ　いつものネコ用ベッドで　クッションをモミモミしていた。"
if observation is not None:
    input_text = observation + 'この文章はネコの観察日記です。この文章を元にペットのオーナーさんにワンポイントアドバイスを簡潔にしてください。句読点ごとに\nを付けてください。'
    res = openai.chat.completions.create(
        # model="gpt-3.5-turbo",
        model="gpt-4",
        messages=[
            {"role": "user", "content": input_text}
        ],
    )
    st.markdown("### ワンポイントアドバイス（AIによる生成）")
    st.code(res.choices[0].message.content)