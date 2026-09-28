import streamlit as st
import gspread
import datetime
import json
import random  # ← ガチャ機能（ランダム抽選）のために追加！

# ==========================================
# 0. ログイン機能（記憶領域の準備）
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "emp_code" not in st.session_state:
    st.session_state.emp_code = ""

if not st.session_state.logged_in:
    st.title("🔐 ログイン")
    input_code = st.text_input("従業員コード")
    input_pass = st.text_input("パスワード", type="password")
    
    if st.button("ログイン"):
        users_db = st.secrets["users"]
        if input_code in users_db and users_db[input_code] == input_pass:
            st.session_state.logged_in = True
            st.session_state.emp_code = input_code
            st.rerun()
        else:
            st.error("従業員コードまたはパスワードが間違っています。")
    st.stop()

# ==========================================
# 1. スプレッドシートとの連携設定
# ==========================================
creds_dict = json.loads(st.secrets["google_creds"])
creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
gc = gspread.service_account_from_dict(creds_dict)

sh = gc.open("入会数記録アプリ") 
worksheet = sh.sheet1
zukan_sheet = sh.worksheet("図鑑データ") # ← 【追加】新しく作った図鑑シートを読み込む！

# ==========================================
# 今月の合計を計算する専用の仕組み
# ==========================================
def get_monthly_total():
    all_data = worksheet.get_all_values()
    current_ym = datetime.date.today().strftime("%Y/%m")
    total = 0
    for row in all_data[1:]:
        if len(row) >= 3 and row[2] == st.session_state.emp_code:
            if row[0].startswith(current_ym):
                if row[1].isdigit():
                    total += int(row[1])
    return total

# ==========================================
# アプリの画面作り
# ==========================================
st.title(f"🏆 入会数記録＆キャラクター図鑑 ({st.session_state.emp_code}さん)")

if st.button("ログアウト"):
    st.session_state.logged_in = False
    st.session_state.emp_code = ""
    st.rerun()

st.header("📝 今日の入会数を記録")
daily_count = st.number_input("入会数を入力してください", min_value=0, step=1)

# 今記録する「前」の、今月の合計件数をチェック
current_total = get_monthly_total()

if st.button("記録する"):
    if daily_count > 0:
        today_str = datetime.date.today().strftime("%Y/%m/%d")
        
        # 1. シート1に入会数を記録
        worksheet.append_row([today_str, daily_count, st.session_state.emp_code])
        st.success(f"スプレッドシートに {daily_count}件 記録しました！")
        
        # 2. ガチャの計算（5件達成ごとに1回ガチャ）
        new_total = current_total + daily_count
        # 例えば記録前が3件、今回3件なら合計6件。「6÷5の商(1) - 3÷5の商(0)」で1回ガチャが引ける！
        gacha_times = (new_total // 5) - (current_total // 5)
        
        if gacha_times > 0:
            st.balloons() # 画面に風船を飛ばす演出！
            st.success(f"🎉 目標達成！ガチャを {gacha_times} 回引きました！")
            
            # 引ける回数分だけガチャを回して、図鑑シートに保存する
            for _ in range(gacha_times):
                get_char_id = random.randint(1, 100) # 1〜100の中からランダムに1つ決定
                zukan_sheet.append_row([st.session_state.emp_code, get_char_id, today_str])
                st.info(f"✨ キャラクター No.{get_char_id} をゲットしました！")
                
        # 画面を再読み込みして最新の状態にする
        # st.rerun() 
    else:
        st.warning("1件以上を入力してください。")

st.markdown("---")

# 記録した「後」の最新の合計を表示
latest_total = get_monthly_total()
current_ym = datetime.date.today().strftime("%Y/%m")
st.write(f"あなたの今月（{current_ym}）の合計入会数: **{latest_total} 件**")
st.write(f"（次のガチャまであと **{5 - (latest_total % 5)} 件**！）")


# ==========================================
# 3. キャラクター図鑑（コレクション画面）
# ==========================================
st.markdown("---")
st.header("📚 あなたのキャラクター図鑑（全100種）")

# 図鑑データシートから「自分が獲得したキャラクター」の番号をすべて取得する
zukan_data = zukan_sheet.get_all_values()
my_characters = set() # set() を使うことで、ダブって獲得したものを1つにまとめます
for row in zukan_data[1:]:
    if len(row) >= 2 and row[0] == st.session_state.emp_code:
        if row[1].isdigit():
            my_characters.add(int(row[1]))

st.write(f"現在の収集率: **{len(my_characters)} / 100**")

# 100個の枠を横5列でズラッと並べる
cols = st.columns(5)
for i in range(1, 101): # 1〜100まで繰り返す
    col = cols[(i - 1) % 5]
    with col:
        if i in my_characters:
            # 獲得済みの枠は緑色で表示！
            st.success(f"No.{i}\n\nゲット!")
        else:
            # 未獲得の枠は赤色で表示
            st.error(f"No.{i}\n\n???")
