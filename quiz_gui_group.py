import os
import tkinter as tk
from tkinter import ttk, messagebox
import csv
import random
from collections import defaultdict

# ==========================================
# ★ グループごとの出題数設定
# 合計が「40」になるように設定してください。
# 例: グループ"1"から15問、"2"から15問、"3"から10問
# ==========================================
GROUP_SETTINGS = {
    "1" : 2,
    "2" : 2,
    "3" : 5,
    "4" : 6,
    "5" : 6,
    "6" : 2,
    "7" : 2,
    "8" : 4,
    "9" : 2,
    "10": 4,
    "11": 3,
    "12": 2,
    "13": 200,
}

# 問題集アプリの幅と高さ
screen_width = "1100"
screen_height = "960"

class QuizApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python3 基礎問題集アプリ")
        self.root.geometry(screen_width + "x" + screen_height)
        self.root.resizable(False, False)

        # グループ別に分類された問題データを読み込む
        csvname = 'quiz_gui_group.csv'
        filename = os.path.dirname(__file__) + '\\' + csvname
        self.questions_by_group = self.load_questions_by_group(filename)
        if not self.questions_by_group:
            messagebox.showerror("エラー", csvname + " が見つからないか、有効な問題がありません。")
            self.root.destroy()
            return

        # 各グループから設定された数だけ問題を抽出
        self.selected_questions = self.select_questions_by_group()
        self.sample_size = len(self.selected_questions)

        if self.sample_size == 0:
            messagebox.showerror("エラー", "設定されたグループの問題がCSV内に見つかりませんでした。")
            self.root.destroy()
            return

        self.current_q_index = 0
        self.score = 0
        self.timer_id = None
        
        # タイマーの設定（60秒 = 60000ミリ秒。プログレスバーを滑らかにするため600分割）
        self.time_max = 600  
        self.time_left = self.time_max

        self.setup_ui()
        self.show_question()

    def load_questions_by_group(self, filename):
        """CSVから問題を読み込み、グループ別にリスト化して辞書に格納する"""
        # { "1": [[問題1], [問題2]], "2": [[問題3]...] } のような形にする
        questions_by_group = defaultdict(list)
        try:
            with open(filename, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーをスキップ
                for row in reader:
                    # グループ列が加わり、全6列になっているか確認
                    if len(row) == 6:
                        group_name = row[0]
                        # グループ名を除いた「問題, 正解, ダミー1~3」を保存
                        q_data = row[1:]
                        q_data.append(row[0]) #yama
                        questions_by_group[group_name].append(q_data)
        except FileNotFoundError:
            pass
        return questions_by_group

    def select_questions_by_group(self):
        """設定に基づいて、グループごとにランダム抽出して合算する"""
        final_list = []
        for group, count in GROUP_SETTINGS.items():
            group_pool = self.questions_by_group.get(group, [])
            
            # CSV内の実際の持ち数と、設定された出題数のうち小さい方を採用（エラー防止）
            extract_count = min(count, len(group_pool))
            if extract_count > 0:
                sampled = random.sample(group_pool, extract_count)
                final_list.extend(sampled)
        
        # 抽出した全ての問題を最後にランダムシャッフルして、グループ順をバラバラにする
        # （グループ順に並んだまま出題したい場合は、下の行をコメントアウトしてください）
        random.shuffle(final_list)
        return final_list

    def setup_ui(self):
        """画面パーツ（ウィジェット）の配置"""
        # 問題番号
        self.lbl_qnum = tk.Label(self.root, text="", font=("Meiryo UI", 12))
        self.lbl_qnum.pack(pady=(15, 5))

        # 問題文
        # self.lbl_question = tk.Label(self.root, text="", font=("Helvetica", 14, "bold"), wraplength=int(screen_width)-50, justify="left")
        self.lbl_question = tk.Label(self.root, text="", font=("Meiryo UI", 14), wraplength=int(screen_width), justify="left")
        self.lbl_question.pack(pady=10)

        # 時間プログレスバー
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress["maximum"] = self.time_max
        self.progress.pack(pady=10)

        # 選択肢ボタン
        self.buttons = []
        for i in range(4):
            btn = tk.Button(self.root, text="", font=("Meiryo UI", 11), width=105, justify="left", background="SlateGray1",
                            command=lambda idx=i: self.check_answer(idx))
            btn.pack(pady=5)
            self.buttons.append(btn)

        # 解答
        self.lbl_feedback = tk.Label(self.root, text="", font=("Meiryo UI", 12, "bold"))
        self.lbl_feedback.pack(pady=15)

    def show_question(self):
        """問題を表示し、タイマーをリセットする"""
        if self.current_q_index >= self.sample_size:
            self.show_result()
            return

        self.lbl_feedback.config(text="")
        for btn in self.buttons:
            btn.config(state=tk.NORMAL)

        q_data = self.selected_questions[self.current_q_index]
        self.current_correct_answer = q_data[1]
        
        choices = [q_data[1], q_data[2], q_data[3], q_data[4]]
        random.shuffle(choices)
        self.current_choices = choices

        self.lbl_qnum.config(text=f"第 {self.current_q_index + 1} 問 / 全 {self.sample_size} 問    第 {q_data[5]} 章から出題")
        self.lbl_question.config(text=q_data[0])
        for i in range(4):
            self.buttons[i].config(text=choices[i])

        self.time_left = self.time_max
        self.progress["value"] = self.time_left
        self.update_timer()

    def update_timer(self):
        """タイマーの更新"""
        if self.time_left > 0:
            self.time_left -= 1
            self.progress["value"] = self.time_left
            self.timer_id = self.root.after(100, self.update_timer)
        else:
            self.handle_timeout()

    def handle_timeout(self):
        """時間切れ"""
        self.disable_buttons()
        self.lbl_feedback.config(text=f"⏰ タイムアウト！\n正解は:\n {self.current_correct_answer}", fg="red")
        #self.root.after(1500, self.go_next)
        self.wait_for_click()

    def check_answer(self, btn_index):
        """回答判定"""
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

        self.disable_buttons()
        selected_answer = self.current_choices[btn_index]

        if selected_answer == self.current_correct_answer:
            self.lbl_feedback.config(text="⭕ 正解！", fg="green")
            self.score += 1
            self.root.after(1500, self.go_next)
            #self.wait_for_click()
        else:
            self.lbl_feedback.config(text=f"❌ 不正解\n正解は:\n {self.current_correct_answer}", fg="red")
            self.wait_for_click()

    def wait_for_click(self):
        """マウスクリックを一時的に待機するイベントを設定"""
        # <Button-1> はマウスの左クリックを意味します
        self.root.bind("<Button-1>", self.on_click_next)

    def on_click_next(self, event):
        """クリックされたときに呼ばれる関数"""
        # 二重クリック防止のため、イベントのバインド（紐付け）を解除
        self.root.unbind("<Button-1>")
        self.go_next()

    def disable_buttons(self):
        for btn in self.buttons:
            btn.config(state=tk.DISABLED)

    def go_next(self):
        self.current_q_index += 1
        self.show_question()

    def show_result(self):
        """結果発表"""
        for widget in self.root.winfo_children():
            widget.pack_forget()

        rate = (self.score / self.sample_size) * 100

        tk.Label(self.root, text="【結果発表】", font=("Helvetica", 20, "bold")).pack(pady=(50, 20))
        tk.Label(self.root, text=f"{self.sample_size}問中、{self.score}問正解！", font=("Helvetica", 16)).pack(pady=10)
        tk.Label(self.root, text=f"正答率: {rate:.1f}%", font=("Helvetica", 16)).pack(pady=10)
        
        btn_close = tk.Button(self.root, text="終了する", font=("Helvetica", 12), width=15, command=self.root.destroy)
        btn_close.pack(pady=30)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuizApp(root)
    root.mainloop()
