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
# 1. スプレッドシートとの連携設定（★通信節約版）
# ==========================================
# @st.cache_resource をつけると、この中の作業は最初の1回だけ実行されます！
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_creds"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("入会数記録アプリ") 
    
    # 3つのシートをまとめて取得して返す
    return sh.sheet1, sh.worksheet("図鑑データ"), sh.worksheet("目標データ")

# 記憶しておいた接続を呼び出して使う
worksheet, zukan_sheet, target_sheet = init_connection()

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

# ------------------------------------------
# ★ 進捗ゲージの表示
# ------------------------------------------
current_ym = datetime.date.today().strftime("%Y/%m")
latest_total = get_monthly_total()

target_data = target_sheet.get_all_values()
target_count = 0
for row in target_data[1:]:
    if len(row) >= 3 and row[0] == current_ym and row[1] == st.session_state.emp_code:
        if row[2].isdigit():
            target_count = int(row[2])
            break

st.markdown("---")
if target_count > 0:
    st.subheader(f"🎯 今月の目標達成まで: {latest_total} / {target_count} 件")
    progress_ratio = min(latest_total / target_count, 1.0)
    st.progress(progress_ratio)
    
    if progress_ratio == 1.0:
        st.success("✨ 今月の目標を達成しました！素晴らしいです！")
else:
    st.info("※今月の目標がまだ設定されていません。（管理者に確認してください）")
st.markdown("---")

# ------------------------------------------
# タブの作成
# ------------------------------------------
tab_record, tab_zukan = st.tabs(["📝 記録画面", "📚 キャラクター図鑑"])

# ------------------------------------------
# 【タブ1】記録画面の中身
# ------------------------------------------
with tab_record:
    st.header("📝 今日の入会数を記録")

    if "success_msg" in st.session_state:
        st.success(st.session_state.success_msg)
        del st.session_state.success_msg
        
    if "gacha_msg" in st.session_state:
        st.success(st.session_state.gacha_msg)
        del st.session_state.gacha_msg
        
    if "gacha_details" in st.session_state:
        for msg in st.session_state.gacha_details:
            st.info(msg)
        del st.session_state.gacha_details

    daily_count = st.number_input("入会数を入力してください", min_value=0, step=1)
    st.write(f"（次のガチャまであと **{5 - (latest_total % 5)} 件**！）")

    if st.button("記録する"):
        if daily_count > 0:
            today_str = datetime.date.today().strftime("%Y/%m/%d")
            
            worksheet.append_row([today_str, daily_count, st.session_state.emp_code])
            
            new_total = latest_total + daily_count
            gacha_times = (new_total // 5) - (latest_total // 5)
            
            st.session_state.success_msg = f"スプレッドシートに {daily_count}件 記録しました！"
            
            if gacha_times > 0:
                st.session_state.gacha_msg = f"🎉 目標達成！ガチャを {gacha_times} 回引きました！"
                
                gacha_results = []
                details = []
                for _ in range(gacha_times):
                    get_char_id = random.randint(1, 100)
                    gacha_results.append([st.session_state.emp_code, get_char_id, today_str])
                    details.append(f"✨ キャラクター No.{get_char_id} をゲット！")
                
                zukan_sheet.append_rows(gacha_results)
                st.session_state.gacha_details = details
            
            st.rerun()
            
        else:
            st.warning("1件以上を入力してください。")

# ------------------------------------------
# 【タブ2】図鑑画面の中身
# ------------------------------------------
with tab_zukan:
    st.header("📚 あなたのキャラクター図鑑（全100種）")

    zukan_data = zukan_sheet.get_all_values()
    my_characters = set() 
    for row in zukan_data[1:]:
        if len(row) >= 2 and row[0] == st.session_state.emp_code:
            if row[1].isdigit():
                my_characters.add(int(row[1]))

    st.write(f"現在の収集率: **{len(my_characters)} / 100**")

    cols = st.columns(5)
    for i in range(1, 101):
        col = cols[(i - 1) % 5]
        with col:
            if i in my_characters:
                st.success(f"No.{i}\n\nゲット!")
            else:
                st.error(f"No.{i}\n\n???")
