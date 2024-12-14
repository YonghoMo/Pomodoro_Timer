# 운영체제별 기능 사용을 위한 필수 모듈 임포트
import platform  # 운영체제 식별용 모듈
import winsound  # Windows 시스템의 알림음 재생용 모듈
from threading import Thread  # 알림음 비동기 재생을 위한 쓰레드 처리용 모듈
from tkinter import messagebox  # 팝업 메시지 표시용 모듈

# Python 버전 호환성을 위한 Tkinter 임포트 처리
import tkinter as tk

# GUI 기본 설정 상수
FONT_NAME = 'Roboto'  # 기본 폰트 설정

# GUI 요소별 폰트 크기 설정
LABEL_SIZE = 10   # 일반 텍스트용 폰트 크기
TIME_SIZE = 26    # 타이머 숫자 표시용 폰트 크기

# GUI 색상 테마 설정
TIMER_ACTIVE_COLOUR = 'black'     # 타이머 작동 중 색상
TIMER_INACTIVE_COLOUR = 'gray'    # 타이머 정지 상태 색상

# 뽀모도로 타이머 기본 설정 값
POMODORO_WORK = 25 * 60        # 작업 시간 (25분)
POMODORO_SHORT_BREAK = 5 * 60  # 짧은 휴식 시간 (5분)
POMODORO_LONG_BREAK = 15 * 60  # 긴 휴식 시간 (15분)
POMODORO_CYCLES = 4            # 긴 휴식까지의 작업 사이클 수

# 가상 클릭 이벤트 객체 생성
CLICK_EVENT = type('FauxEvent', (), {'num': 1})()

class Toggle:
    """
    두 상태를 전환할 수 있는 토글 클래스
    타이머의 활성/비활성 상태 관리에 사용
    """
    def __init__(self, init, other):
        """
        토글 객체 초기화
        
        Args:
            init: 초기 상태 값
            other: 대체 상태 값
        """
        self._init = (init, other)  # 초기 상태 저장
        self.other = other         # 대체 상태 저장
        self.value = init          # 현재 상태 저장

    def flip(self):
        """현재 상태를 반대 상태로 전환"""
        self.value, self.other = self.other, self.value

    def reset(self):
        """초기 상태로 복원"""
        self.value, self.other = self._init

class Timer(tk.Tk):
    """
    메인 타이머 GUI 클래스
    전체 애플리케이션의 창과 기본 레이아웃을 관리
    """
    def __init__(self):
        """타이머 창 초기화 및 기본 설정"""
        tk.Tk.__init__(self)
        self.wm_title('뽀모도로 타이머')
        
        # 윈도우 아이콘 설정
        try:
            self.iconbitmap('tomato.ico')
        except:
            pass
        
        # 창 레이아웃 설정
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 메인 프레임 설정
        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky='NSEW')
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # 타이머 카운터 생성
        self.counter = Counter(self.frame)
        self.counter.frame.grid(row=0, column=0, sticky='NSEW')
        
        # 버튼 프레임 설정
        self._setup_button_frame()
        
        # 창 크기 및 위치 설정
        self.setup_window()
        
        # 타이머 업데이트 시작
        self.ticker()

    def _setup_button_frame(self):
        """버튼 프레임 설정 및 버튼 생성"""
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=1, column=0, sticky='EW', padx=10, pady=5)
        
        # 버튼 프레임 열 설정
        for i in range(3):
            self.button_frame.grid_columnconfigure(i, weight=1)
        
        # 버튼 생성 및 배치
        self._create_buttons()

    def _create_buttons(self):
        """타이머 제어 버튼 생성"""
        # 시작/일시정지 버튼
        self.button_start = tk.Button(
            self.button_frame,
            text='시작/일시정지',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.toggle_timer
        )
        self.button_start.grid(row=0, column=0, columnspan=2, sticky='EW', padx=2, pady=2)
        
        # 초기화 버튼
        self.button_reset = tk.Button(
            self.button_frame,
            text='초기화',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.reset_timer
        )
        self.button_reset.grid(row=0, column=2, sticky='EW', padx=2, pady=2)
        
        # 모드 전환 버튼들
        self._create_mode_buttons()

    def _create_mode_buttons(self):
        """타이머 모드 전환 버튼 생성"""
        # 작업 시간 버튼
        self.button_work = tk.Button(
            self.button_frame,
            text='작업 시간',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.switch_to_work
        )
        self.button_work.grid(row=1, column=0, sticky='EW', padx=2, pady=2)
        
        # 짧은 휴식 버튼
        self.button_short = tk.Button(
            self.button_frame,
            text='짧은 휴식',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.switch_to_short
        )
        self.button_short.grid(row=1, column=1, sticky='EW', padx=2, pady=2)
        
        # 긴 휴식 버튼
        self.button_long = tk.Button(
            self.button_frame,
            text='긴 휴식',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.switch_to_long
        )
        self.button_long.grid(row=1, column=2, sticky='EW', padx=2, pady=2)

    def setup_window(self):
        """창 크기 및 위치 설정"""
        # 창 크기 변경 비활성화
        self.resizable(False, False)
        
        # 창 크기 설정
        window_width = 300
        window_height = 140
        
        # 화면 중앙 좌표 계산
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        # 창 위치 및 크기 설정
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    def toggle_timer(self, event=None):
        """타이머 시작/정지 토글"""
        self.counter.clicked(CLICK_EVENT)
        
    def ticker(self):
        """주기적인 타이머 업데이트 (1초마다)"""
        self.after(1000, self.ticker)
        self.counter.tick()

    def switch_to_work(self):
        """작업 시간 모드로 전환"""
        self.counter.switch_to_work()
        
    def switch_to_short(self):
        """짧은 휴식 모드로 전환"""
        self.counter.switch_to_short()
        
    def switch_to_long(self):
        """긴 휴식 모드로 전환"""
        self.counter.switch_to_long()

    def reset_timer(self):
        """현재 모드의 타이머를 초기값으로 재설정"""
        self.counter.reset_current_mode()

class Counter:
    """
    타이머의 핵심 기능을 담당하는 클래스
    시간 계산, 모드 전환, 화면 갱신 등을 처리
    """
    def __init__(self, master):
        """
        카운터 객체 초기화
        
        Args:
            master: 부모 GUI 컨테이너
        """
        self.master = master
        self.frame = tk.Frame(master)
        
        # 프레임 레이아웃 설정
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # 타이머 모드별 시간 설정
        self.work_time = POMODORO_WORK
        self.short_break_time = POMODORO_SHORT_BREAK
        self.long_break_time = POMODORO_LONG_BREAK
        
        # 초기 상태 설정
        self.current_mode = 'work'
        self.time = self.work_time
        self.paused = True
        self.text_colour = Toggle(TIMER_INACTIVE_COLOUR, TIMER_ACTIVE_COLOUR)
        
        # GUI 레이블 생성
        self._create_labels()
        
        # 뽀모도로 사이클 관리 변수
        self.pomodoro_cycle = 0
        self.is_break = False

    def _create_labels(self):
        """타이머 표시를 위한 레이블 생성"""
        # 상태 표시 레이블
        self.status_label = tk.Label(
            self.frame,
            text="작업 시간",
            font=(FONT_NAME, LABEL_SIZE),
            anchor='center'
        )
        self.status_label.grid(column=0, row=0, sticky='NSEW')
        
        # 시간 표시 레이블
        self.time_label = tk.Label(
            self.frame,
            text=self.format_time(),
            font=(FONT_NAME, TIME_SIZE),
            fg=TIMER_INACTIVE_COLOUR,
            anchor='center'
        )
        self.time_label.grid(column=0, row=1, sticky='NSEW')

    def reset_current_mode(self):
        """현재 모드의 타이머를 초기값으로 재설정"""
        if self.current_mode == 'work':
            self.time = POMODORO_WORK
        elif self.current_mode == 'short_break':
            self.time = POMODORO_SHORT_BREAK
        else:  # long_break
            self.time = POMODORO_LONG_BREAK
        self.paused = True
        self.text_colour.reset()
        self.refresh()

    def tick(self):
        """1초마다 호출되어 타이머를 갱신"""
        if not self.paused:
            self.time -= 1
            if self.time <= 0:
                self.handle_timer_completion()
            self.refresh()

    def handle_timer_completion(self):
        """타이머 완료 시의 동작 처리"""
        # 뽀모도로 사이클 관리
        if not self.is_break:
            self.pomodoro_cycle += 1
            if self.pomodoro_cycle % POMODORO_CYCLES == 0:
                self.switch_to_long()
            else:
                self.switch_to_short()
        else:
            self.switch_to_work()
        
        # 알림음 재생 (비동기)
        try:
            Thread(
                target=lambda: winsound.PlaySound('alarm.wav', winsound.SND_FILENAME),
                daemon=True
            ).start()
        except:
            pass
        
        # 완료 메시지 표시
        self._show_completion_message()
        
        # 다음 타이머 자동 시작
        self.paused = False
        self.text_colour.value = TIMER_ACTIVE_COLOUR
        self.refresh()

    def _show_completion_message(self):
        """타이머 완료시 현재 모드에 따른 메시지 표시"""
        messages = {
            'work': "작업 시작!",
            'short_break': "짧고 달콤한 휴식 시간~",
            'long_break': "수고하셨어요! 충분한 휴식을 취하세요!"
        }
        messagebox.showinfo("알림", messages.get(self.current_mode, "타이머 완료!"))

    def format_time(self):
        """시간을 MM:SS 형식으로 포맷팅"""
        minutes = self.time // 60
        seconds = self.time % 60
        return f"{minutes:02d}:{seconds:02d}"

    def refresh(self):
        """화면 갱신"""
        self.time_label.config(
            text=self.format_time(),
            fg=self.text_colour.value
        )

    def clicked(self, event):
        """타이머 시작/정지 토글"""
        self.paused = not self.paused
        self.text_colour.flip()
        self.refresh()

    def switch_to_work(self):
        """작업 시간 모드로 전환"""
        self.time = POMODORO_WORK
        self.current_mode = 'work'
        self.status_label.config(text="작업 시간")
        self.is_break = False
        self.refresh()
        
    def switch_to_short(self):
        """짧은 휴식 모드로 전환"""
        self.time = POMODORO_SHORT_BREAK
        self.current_mode = 'short_break'
        self.status_label.config(text="짧은 휴식 시간")
        self.is_break = True
        self.refresh()
        
    def switch_to_long(self):
        """긴 휴식 모드로 전환"""
        self.time = POMODORO_LONG_BREAK
        self.current_mode = 'long_break'
        self.status_label.config(text="긴 휴식 시간")
        self.is_break = True
        self.refresh()

def main():
    """메인 함수: 애플리케이션 실행"""
    app = Timer()
    app.mainloop()

# 프로그램 시작점
if __name__ == "__main__":
    main()