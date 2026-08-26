import streamlit as st
import gspread
import datetime

# ==========================================
# 1. スプレッドシートとの連携設定
# ==========================================
# さきほど名前を変更した鍵ファイル（secret.json）を使って接続
gc = gspread.service_account(filename=r"C:\Users\BB1131\Desktop\app\secret.json")

# 自分が作成したスプレッドシートの名前を正確に入力してください！
# （例："入会数記録アプリ" など）
sh = gc.open("入会数記録アプリ") 

# 1つ目のシートを選択
worksheet = sh.sheet1

# ==========================================
# アプリの画面作り
# ==========================================
st.title("🏆 入会数記録＆キャラクター図鑑")

st.header("📝 今日の入会数を記録")
daily_count = st.number_input("入会数を入力してください", min_value=0, step=1)

if st.button("記録する"):
    # 今日の日付を取得（例：2024/05/20）
    today_str = datetime.date.today().strftime("%Y/%m/%d")
    
    # スプレッドシートの末尾に、日付と入会数を「新しい行」として追加！
    worksheet.append_row([today_str, daily_count])
    
    st.success(f"スプレッドシートに {daily_count}件 記録しました！")

st.markdown("---")
st.header("📖 あなたの図鑑")

# ==========================================
# 2. スプレッドシートからデータを読み込んで合計を計算
# ==========================================
# B列（入会数）のデータをすべて取得してリストにする
# 例：['入会数', '10', '5', '3'] のような形になります
all_values = worksheet.col_values(2) 

# 1行目は見出し（'入会数'）の文字なので除外して、数字だけを足し算する
total = 0
for val in all_values[1:]:
    if val.isdigit(): # もし中身が数字なら
        total += int(val)

st.write(f"スプレッドシートの合計入会数: **{total} 件**")

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
    # ↓ 画像のパスは、ご自身のパソコンのものに合わせてください
    st.image(r"C:\Users\BB1131\Desktop\app\slime.png", width=300)
else:
    st.write("🔒 まだキャラクターはアンロックされていません。最初の記録を始めましょう！")