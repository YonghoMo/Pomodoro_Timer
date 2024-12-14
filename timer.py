# 운영체제별 기능을 위한 platform 모듈 임포트
import platform

# Python 버전 호환성을 위한 Tkinter 임포트 처리
try:
    import Tkinter as tk
except ImportError:
    import tkinter as tk

from tkinter import messagebox  # 상단에 추가

# GUI 폰트 설정
FONT_NAME = 'Roboto'

# GUI 요소별 폰트 크기 설정
LABEL_SIZE = 10  # 일반 레이블 크기
TIME_SIZE = 26   # 시간 표시 크기
DELETE_SIZE = 16 # 삭제 버튼 크기
ADD_SIZE = 20    # 추가 버튼 크기

# GUI 색상 설정
GRIP_COLOUR = 'orange'           # 드래그 영역 색상
TIMER_ACTIVE_COLOUR = 'black'    # 활성화된 타이머 색상
TIMER_INACTIVE_COLOUR = 'gray'   # 비활성화된 타이머 색상

# 마우스 이벤트를 시뮬레이션하기 위한 가상 이벤트 클래스
class FauxEvent(object):
    def __init__(self, num):
        self.num = num

# 클릭 이벤트 객체 생성
CLICK_EVENT = FauxEvent(1)

# 마우스 스크롤 방향을 판단하는 함수
def scroll_type(event):
    # 아래로 스크롤하는 경우
    if event.num == 5 or event.delta == -120:
        return -1
    # 위로 스크롤하는 경우
    if event.num == 4 or event.delta == 120:
        return 1
    raise RuntimeError('Unknown scroll event, file bugreport: %s' % event)

# 스크롤 이벤트를 객체에 바인딩하는 함수
def bind_scroll(obj, listener):
    def fire_listener(event):
        return listener(event, scroll_type(event))

    # 운영체제별 마우스 휠 이벤트 처리
    if platform.system() == 'Windows':
        obj.bind('<MouseWheel>', fire_listener)
    else:
        obj.bind('<Button-4>', fire_listener)
        obj.bind('<Button-5>', fire_listener)

# 초 단위 시간을 시, 분, 초로 변환하는 함수
def convert(seconds):
    r = seconds
    s = r % 60                    # 초 계산
    m = (r - s) % (60*60)        # 분 계산
    h = (r - s - m) % (60*60*60) # 시간 계산
    return s, int(m/60), int(h/(60*60)), r - (s + m + h)

# 두 상태를 전환할 수 있는 토글 클래스
class Toggle(object):
    def __init__(self, init, other):
        self._init = (init, other)
        self.other = other
        self.value = init

    # 현재 상태를 반대 상태로 전환
    def flip(self):
        self.value, self.other = self.other, self.value

    # 초기 상태로 복원
    def reset(self):
        self.value, self.other = self._init

# 메인 타이머 GUI 클래스
class Timer(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.wm_title('뽀모도로 타이머')
        
        # 단일 타이머만 사용
        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky='WE')
        
        # 컨트롤 버튼 프레임
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(column=0, row=1, sticky='WE')
        
        # 시작/일시정지 버튼만 유지
        self.button_start = tk.Label(self.button_frame, text='시작', font=(FONT_NAME, ADD_SIZE))
        self.button_start.grid(column=0, row=0, sticky='WE')
        self.button_start.bind("<Button-1>", self.toggle_timer)
        
        # 단일 카운터 생성
        self.counter = Counter(self.frame)
        self.counter.frame.grid(row=0, column=0)
        
        # 화면 크기 및 위치 설정
        self.setup_window()
        
        # 타이머 업데이트 시작
        self.ticker()

    def setup_window(self):
        """윈도우 설정"""
        # 창 크기 고정
        self.resizable(False, False)
        
        # 창을 화면 중앙에 위치
        window_width = 300
        window_height = 200
        
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
        """주기적인 타이머 업데이트"""
        self.after(1000, self.ticker)
        self.counter.tick()

# 개별 타이머 카운터 클래스
class Counter(object):
    def __init__(self, master):
        self.frame = tk.Frame(master)
        self.time_frame = tk.Frame(self.frame)
        self.time_frame.grid(column=0, row=1)
        
        # 기본값을 25분(뽀모도로 작업시간)으로 설정
        self.time = POMODORO_WORK
        self.paused = True
        self.text_colour = Toggle(TIMER_INACTIVE_COLOUR, TIMER_ACTIVE_COLOUR)
        
        # 현재 상태 표시 레이블
        self.status_label = tk.Label(
            self.frame,
            text="작업 시간",
            font=(FONT_NAME, LABEL_SIZE)
        )
        self.status_label.grid(column=0, row=0)
        
        # 시간 표시 레이블
        self.time_label = tk.Label(
            self.time_frame,
            text=self.format_time(),
            font=(FONT_NAME, TIME_SIZE)
        )
        self.time_label.grid(column=0, row=0)
        
        self.pomodoro_cycle = 0
        self.is_break = False

    def tick(self):
        """1초마다 호출되어 타이머를 갱신하는 메서드"""
        if not self.paused:
            self.time -= 1
            if self.time <= 0:
                self.handle_timer_completion()
            self.refresh()

    def handle_timer_completion(self):
        """타이머 완료 시 처리"""
        if not self.is_break:
            self.pomodoro_cycle += 1
            if self.pomodoro_cycle % POMODORO_CYCLES == 0:
                self.time = POMODORO_LONG_BREAK
                self.status_label.config(text="긴 휴식 시간")
            else:
                self.time = POMODORO_SHORT_BREAK
                self.status_label.config(text="짧은 휴식 시간")
            self.is_break = True
        else:
            self.time = POMODORO_WORK
            self.status_label.config(text="작업 시간")
            self.is_break = False
        
        messagebox.showinfo("알림", "타이머가 완료되었습니다!")
        self.paused = True

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

# 상단에 Pomodoro 관련 상수 추가
POMODORO_WORK = 25 * 60      # 작업 시간 (25분)
POMODORO_SHORT_BREAK = 5 * 60  # 짧은 휴식 (5분)
POMODORO_LONG_BREAK = 15 * 60  # 긴 휴식 (15분)
POMODORO_CYCLES = 4           # 긴 휴식까지의 사이클 수

# 메인 함수
def main():
    app = Timer()
    app.mainloop()
    app.destroy()

# 프로그램 시작
main()