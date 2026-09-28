import streamlit as st
import gspread
import datetime
import json
import random

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
zukan_sheet = sh.worksheet("図鑑データ")

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
st.title(f"🏆 入会数記録＆キャラクター ({st.session_state.emp_code}さん)")

if st.button("ログアウト"):
    st.session_state.logged_in = False
    st.session_state.emp_code = ""
    st.rerun()

# ★ ここでタブを作成！（左が記録用、右が図鑑用）
tab_record, tab_zukan = st.tabs(["📝 記録画面", "📚 キャラクター図鑑"])

# ------------------------------------------
# 【タブ1】記録画面の中身
# ------------------------------------------
with tab_record:
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
            
            # 2. ガチャの計算
            new_total = current_total + daily_count
            gacha_times = (new_total // 5) - (current_total // 5)
            
            if gacha_times > 0:
                st.balloons() # 風船を飛ばす！
                st.success(f"🎉 目標達成！ガチャを {gacha_times} 回引きました！")
                
                # 📦 書き込むデータを一度リスト（段ボール）にまとめる
                gacha_results = []
                
                for _ in range(gacha_times):
                    get_char_id = random.randint(1, 100)
                    gacha_results.append([st.session_state.emp_code, get_char_id, today_str])
                    st.info(f"✨ キャラクター No.{get_char_id} をゲットしました！\n（「キャラクター図鑑」タブで確認してね！）")
                
                # 🚚 準備したリストを、スプレッドシートに「一気に」書き込む！（エラー回避）
                zukan_sheet.append_rows(gacha_results)
                
        else:
            st.warning("1件以上を入力してください。")

    st.markdown("---")

    # 記録した「後」の最新の合計を表示
    latest_total = get_monthly_total()
    current_ym = datetime.date.today().strftime("%Y/%m")
    st.write(f"あなたの今月（{current_ym}）の合計入会数: **{latest_total} 件**")
    st.write(f"（次のガチャまであと **{5 - (latest_total % 5)} 件**！）")

# ------------------------------------------
# 【タブ2】図鑑画面の中身
# ------------------------------------------
with tab_zukan:
    st.header("📚 あなたのキャラクター図鑑（全100種）")

    # 図鑑データシートから「自分が獲得したキャラクター」の番号を取得
    zukan_data = zukan_sheet.get_all_values()
    my_characters = set() 
    for row in zukan_data[1:]:
        if len(row) >= 2 and row[0] == st.session_state.emp_code:
            if row[1].isdigit():
                my_characters.add(int(row[1]))

    st.write(f"現在の収集率: **{len(my_characters)} / 100**")

    # 100個の枠を横5列で並べる
    cols = st.columns(5)
    for i in range(1, 101):
        col = cols[(i - 1) % 5]
        with col:
            if i in my_characters:
                # 獲得済みの枠
                st.success(f"No.{i}\n\nゲット!")
            else:
                # 未獲得の枠
                st.error(f"No.{i}\n\n???")
