import streamlit as st
import gspread
import datetime
import json
import random
import pandas as pd  # ★ グラフ描画のために追加！

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
# 1. スプレッドシートとの連携設定（通信節約版）
# ==========================================
@st.cache_resource
def init_connection():
    creds_dict = json.loads(st.secrets["google_creds"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    gc = gspread.service_account_from_dict(creds_dict)
    sh = gc.open("入会数記録アプリ") 
    
    return sh.sheet1, sh.worksheet("図鑑データ"), sh.worksheet("目標データ")

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
# ★ タブを3つに増やす！
# ------------------------------------------
tab_record, tab_zukan, tab_graph = st.tabs(["📝 記録画面", "📚 キャラクター図鑑", "📈 実績グラフ"])

# ------------------------------------------
# 【タブ1】記録画面の中身
# ------------------------------------------
with tab_record:
    st.header("📝 今日の記録")

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
    joining_rate = st.number_input("入会率（％）を入力してください", min_value=0, max_value=100, step=1)

    st.write(f"（入会数：次のガチャまであと **{5 - (latest_total % 5)} 件**！）")
    st.write("（入会率：**15%以上**の記録でガチャ1回追加！）")

    if st.button("記録する"):
        if daily_count > 0 or joining_rate > 0:
            today_str = datetime.date.today().strftime("%Y/%m/%d")
            
            worksheet.append_row([today_str, daily_count, st.session_state.emp_code, joining_rate])
            
            new_total = latest_total + daily_count
            count_gacha = (new_total // 5) - (latest_total // 5)
            rate_gacha = 1 if joining_rate >= 15 else 0
            total_gacha = count_gacha + rate_gacha
            
            st.session_state.success_msg = f"入会数:{daily_count}件 / 入会率:{joining_rate}％ を記録しました！"
            
            if total_gacha > 0:
                gacha_reason = []
                if count_gacha > 0:
                    gacha_reason.append(f"入会数達成で {count_gacha} 回")
                if rate_gacha > 0:
                    gacha_reason.append(f"入会率15%以上で 1 回")
                reason_text = "、".join(gacha_reason)
                
                st.session_state.gacha_msg = f"🎉 {reason_text}！合計ガチャを {total_gacha} 回引きました！"
                
                gacha_results = []
                details = []
                for _ in range(total_gacha):
                    get_char_id = random.randint(1, 100)
                    gacha_results.append([st.session_state.emp_code, get_char_id, today_str])
                    details.append(f"✨ キャラクター No.{get_char_id} をゲット！")
                
                zukan_sheet.append_rows(gacha_results)
                st.session_state.gacha_details = details
            
            st.rerun()
            
        else:
            st.warning("記録する数値（入会数 または 入会率）を入力してください。")

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

# ------------------------------------------
# 【タブ3】実績グラフの中身（★新機能）
# ------------------------------------------
with tab_graph:
    st.header("📈 あなたの実績グラフ")

    all_data = worksheet.get_all_values()
    
    # グラフ用にデータを日ごとにまとめる
    graph_data = {}
    for row in all_data[1:]:
        if len(row) >= 3 and row[2] == st.session_state.emp_code:
            date_str = row[0]
            # 入会数
            count = int(row[1]) if row[1].isdigit() else 0
            # 入会率（過去のデータでD列が無い場合のエラー防止）
            rate = 0
            if len(row) >= 4 and row[3].isdigit():
                rate = int(row[3])
                
            if date_str in graph_data:
                graph_data[date_str]["入会数"] += count
                graph_data[date_str]["入会率"] = rate # 1日に複数回入力した場合は最新を反映
            else:
                graph_data[date_str] = {"入会数": count, "入会率": rate}

    if len(graph_data) > 0:
        # 辞書データをpandasの表（DataFrame）に変換
        df = pd.DataFrame.from_dict(graph_data, orient='index')
        
        st.subheader("📊 入会数の推移")
        st.line_chart(df["入会数"])
        
        st.subheader("📊 入会率(%)の推移")
        st.line_chart(df["入会率"])
    else:
        st.info("まだ記録データがありません。")
