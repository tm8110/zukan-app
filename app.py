import streamlit as st
import gspread
import datetime
import json

# ==========================================
# 0. ログイン機能（記憶領域の準備）
# ==========================================
# ログイン状態を記憶するメモ帳（session_state）を準備
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "emp_code" not in st.session_state:
    st.session_state.emp_code = ""

# --- ログインしていない場合の画面 ---
if not st.session_state.logged_in:
    st.title("🔐 ログイン")
    
    # 入力フォーム
    input_code = st.text_input("従業員コード")
    input_pass = st.text_input("パスワード", type="password") # type="password"で伏字になります
    
    if st.button("ログイン"):
        # 金庫（Secrets）から名簿を取り出す
        users_db = st.secrets["users"]
        
        # 従業員コードが名簿に存在し、かつパスワードが一致するか確認
        if input_code in users_db and users_db[input_code] == input_pass:
            # 合格なら、記憶領域に「ログイン中」と「従業員コード」を記録
            st.session_state.logged_in = True
            st.session_state.emp_code = input_code
            st.rerun() # 画面をリロードして図鑑画面へ！
        else:
            st.error("従業員コードまたはパスワードが間違っています。")
            
    # ログインしていない人はここでプログラムを止める（図鑑を見せない）
    st.stop()


# ==========================================
# 1. スプレッドシートとの連携設定 (ログイン成功後)
# ==========================================
creds_dict = json.loads(st.secrets["google_creds"])
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
gc = gspread.service_account_from_dict(creds_dict)

sh = gc.open("入会数記録アプリ") 
worksheet = sh.sheet1

# ==========================================
# アプリの画面作り
# ==========================================
# タイトルにログイン中の人のコードを表示
st.title(f"🏆 入会数記録＆キャラクター図鑑 ({st.session_state.emp_code}さん)")

# ログアウトボタン
if st.button("ログアウト"):
    st.session_state.logged_in = False
    st.session_state.emp_code = ""
    st.rerun()

st.header("📝 今日の入会数を記録")
daily_count = st.number_input("入会数を入力してください", min_value=0, step=1)

if st.button("記録する"):
    today_str = datetime.date.today().strftime("%Y/%m/%d")
    
    # 【変更点】日付、入会数に加えて「従業員コード」も一緒に書き込む！
    worksheet.append_row([today_str, daily_count, st.session_state.emp_code])
    
    st.success(f"スプレッドシートに {daily_count}件 記録しました！")

st.markdown("---")
st.header("📖 あなたの図鑑")

# ==========================================
# 2. スプレッドシートから自分のデータだけを読み込んで合計を計算
# ==========================================
# 【変更点】B列だけではなく、シートの全データを一度取得する
all_data = worksheet.get_all_values() 

total = 0
# 1行目（見出し）を飛ばしてループを回す
for row in all_data[1:]:
    # row（行）のデータが3列以上あり、かつ、3列目（row[2]）が自分の従業員コードと同じなら足す
    if len(row) >= 3 and row[2] == st.session_state.emp_code:
        if row[1].isdigit(): # 入会数が数字なら
            total += int(row[1])

st.write(f"あなたの合計入会数: **{total} 件**")

# ==========================================
# 3. キャラクターアンロックの仕組み
# ==========================================
if total >= 20:
    st.subheader("🎉 レベル3: ドラゴンをアンロック！")
    st.info("ドラゴンの画像")
elif total >= 10:
    st.subheader("✨ レベル2: ナイトをアンロック！")
    st.info("ナイトの画像")
elif total >= 1:
    st.subheader("🐣 レベル1: スライムをアンロック！")
    st.image("slime.png", width=300)
else:
    st.write("🔒 まだキャラクターはアンロックされていません。最初の記録を始めましょう！")
