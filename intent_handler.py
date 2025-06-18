
import re
import pandas as pd

def extract_time_from_question(question):
    month_match = re.search(r"tháng\s*(\d{1,2})", question, re.IGNORECASE)
    year_match = re.search(r"năm\s*(\d{4})", question, re.IGNORECASE)
    month = int(month_match.group(1)) if month_match else None
    year = int(year_match.group(1)) if year_match else None
    return year, month

def recognize_intent(question):
    q = question.lower()
    if "khách" in q and "gửi nhiều" in q:
        return {"intent": "top_customer", "params": {}}
    if "sản phẩm" in q and ("lỗi nhiều" in q or "gửi nhiều" in q):
        return {"intent": "top_product", "params": {}}
    if "ktv" in q or "kỹ thuật viên" in q:
        return {"intent": "top_ktv", "params": {}}
    return {"intent": "unknown", "params": {}}

def filter_by_time(df, question):
    year, month = extract_time_from_question(question)
    df_filtered = df.copy()
    if year and "nam" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["nam"] == year]
    if month and "thang" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["thang"] == month]
    return df_filtered

def handle_top_customer(df, question):
    df_filtered = filter_by_time(df, question)
    for col in ["ten_khach_hang", "khach_hang"]:
        if col in df_filtered.columns:
            top = df_filtered[col].value_counts().idxmax()
            count = df_filtered[col].value_counts().max()
            return df_filtered[df_filtered[col] == top], f"Khách hàng gửi nhiều nhất là **{top}** với tổng cộng {count} lượt gửi."
    return df_filtered, "Không tìm thấy dữ liệu khách hàng trong bảng."

def handle_top_product(df, question):
    df_filtered = filter_by_time(df, question)
    for col in ["san_pham", "model", "ten_san_pham"]:
        if col in df_filtered.columns:
            top = df_filtered[col].value_counts().idxmax()
            count = df_filtered[col].value_counts().max()
            return df_filtered[df_filtered[col] == top], f"Sản phẩm lỗi nhiều nhất là **{top}** với tổng cộng {count} lượt gửi."
    return df_filtered, "Không tìm thấy dữ liệu sản phẩm trong bảng."

def handle_top_ktv(df, question):
    df_filtered = filter_by_time(df, question)
    for col in ["ktv", "ten_ky_thuat_vien"]:
        if col in df_filtered.columns:
            top = df_filtered[col].value_counts().idxmax()
            count = df_filtered[col].value_counts().max()
            return df_filtered[df_filtered[col] == top], f"Kỹ thuật viên xử lý nhiều nhất là **{top}** với tổng cộng {count} lượt xử lý."
    return df_filtered, "Không tìm thấy dữ liệu kỹ thuật viên trong bảng."

def handle_intent(question, df):
    intent_info = recognize_intent(question)
    intent = intent_info["intent"]

    if intent == "top_customer":
        return handle_top_customer(df, question)
    elif intent == "top_product":
        return handle_top_product(df, question)
    elif intent == "top_ktv":
        return handle_top_ktv(df, question)
    else:
        return df, "Không xác định được ý định từ câu hỏi."
