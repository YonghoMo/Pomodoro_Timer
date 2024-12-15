# 필요한 모듈 임포트
import winsound  # Windows 시스템의 알림음 재생을 위한 모듈
from tkinter import messagebox  # 팝업 메시지 표시를 위한 모듈
import tkinter as tk  # GUI 구현을 위한 기본 모듈

# GUI 기본 설정 상수 정의
FONT_NAME = 'Roboto'  # 프로그램에서 사용할 기본 폰트
LABEL_SIZE = 10   # 일반 텍스트(버튼, 상태 표시 등)의 폰트 크기
TIME_SIZE = 26    # 타이머 시간 표시용 큰 폰트 크기

# GUI 색상 테마 설정
TIMER_ACTIVE_COLOUR = 'black'     # 타이머 실행 중일 때 사용할 색상
TIMER_INACTIVE_COLOUR = 'gray'    # 타이머 정지 상태일 때 사용할 색상

# 뽀모도로 타이머 기본 설정 값 (모두 초 단위로 변환)
POMODORO_WORK = 25 * 60         # 작업 시간 (25분)
POMODORO_SHORT_BREAK = 5 * 60    # 짧은 휴식 시간 (5분)
POMODORO_LONG_BREAK = 15 * 60    # 긴 휴식 시간 (15분)
POMODORO_CYCLES = 4              # 긴 휴식까지의 작업 사이클 수

# 가상 클릭 이벤트 객체 생성
# type() 함수로 동적으로 클래스를 생성하고 num 속성이 1인 이벤트 객체 생성
# 이는 실제 마우스 클릭을 시뮬레이션하기 위한 것
CLICK_EVENT = type('FauxEvent', (), {'num': 1})()

# 두 상태를 전환할 수 있는 토글 클래스
class Toggle:
    def __init__(self, init, other):
        self._init = (init, other)  # 초기 상태값을 튜플로 저장
        self.other = other          # 대체 상태값 저장
        self.value = init           # 현재 상태값 저장

    # 현재 상태를 반대 상태로 전환하는 메서드
    def flip(self):
        self.value, self.other = self.other, self.value

    # 초기 상태로 되돌리는 메서드
    def reset(self):
        self.value, self.other = self._init

# 메인 타이머 GUI 클래스
class Timer(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)  # 부모 클래스 초기화
        self.wm_title('뽀모도로 타이머')  # 윈도우 제목 설정
        
        # 윈도우 아이콘 설정 (실패해도 계속 진행)
        try:
            self.iconbitmap('tomato.ico')
        except:
            pass
        
        # 창 레이아웃 설정 (그리드 시스템)
        self.grid_rowconfigure(0, weight=1)  # 행 가중치 설정
        self.grid_columnconfigure(0, weight=1)  # 열 가중치 설정
        
        # 메인 프레임 설정
        # 전체 UI를 담을 기본 프레임 생성 및 배치
        self.frame = tk.Frame(self)
        self.frame.grid(row=0, column=0, sticky='NSEW')  # NSEW로 프레임을 창 전체에 확장
        self.frame.grid_rowconfigure(0, weight=1)  # 프레임 내부 행 가중치 설정
        self.frame.grid_columnconfigure(0, weight=1)  # 프레임 내부 열 가중치 설정
        
        # 타이머 카운터 생성 및 배치
        # Counter 클래스의 인스턴스를 생성하고 메인 프레임에 배치
        self.counter = Counter(self.frame)
        self.counter.frame.grid(row=0, column=0, sticky='NSEW')
        
        # 버튼 프레임 설정
        self._setup_button_frame()  # 버튼들을 담을 프레임 설정
        
        # 창 크기 및 위치 설정
        self.setup_window()  # 윈도우 크기와 화면 중앙 배치 설정
        
        # 타이머 업데이트 시작
        self.ticker()  # 주기적인 타이머 업데이트 시작

    def _setup_button_frame(self):
        # 버튼 프레임 생성 및 설정
        # 모든 제어 버튼들을 담을 프레임
        self.button_frame = tk.Frame(self)
        self.button_frame.grid(row=1, column=0, sticky='EW', padx=10, pady=5)
        
        # 버튼 프레임의 열 설정 (3개의 동일한 너비)
        # 각 열의 가중치를 1로 설정하여 균등 분할
        for i in range(3):
            self.button_frame.grid_columnconfigure(i, weight=1)
        
        # 버튼 생성
        self._create_buttons()  # 실제 버튼들을 생성하고 배치

    def _create_buttons(self):
        # 시작/일시정지 버튼 생성 및 설정
        self.button_start = tk.Button(
            self.button_frame,
            text='시작/일시정지',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.toggle_timer  # 클릭 시 타이머 시작/정지 전환
        )
        # 버튼을 프레임의 첫 두 열에 걸쳐 배치
        self.button_start.grid(row=0, column=0, columnspan=2, sticky='EW', padx=2, pady=2)
        
        # 초기화 버튼 생성 및 설정
        self.button_reset = tk.Button(
            self.button_frame,
            text='초기화',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.reset_timer  # 클릭 시 타이머 초기화
        )
        # 버튼을 프레임의 마지막 열에 배치
        self.button_reset.grid(row=0, column=2, sticky='EW', padx=2, pady=2)
        
        # 모드 전환 버튼들 생성
        self._create_mode_buttons()  # 작업/휴식 모드 전환 버튼들 생성

    def _create_mode_buttons(self):
        # 작업 시간 버튼 생성 및 설정
        self.button_work = tk.Button(
            self.button_frame,
            text='작업 시간',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.switch_to_work  # 작업 모드로 전환
        )
        # 첫 번째 열에 버튼 배치
        self.button_work.grid(row=1, column=0, sticky='EW', padx=2, pady=2)
        
        # 짧은 휴식 버튼 생성 및 설정
        self.button_short = tk.Button(
            self.button_frame,
            text='짧은 휴식',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.switch_to_short  # 짧은 휴식 모드로 전환
        )
        # 두 번째 열에 버튼 배치
        self.button_short.grid(row=1, column=1, sticky='EW', padx=2, pady=2)
        
        # 긴 휴식 버튼 생성 및 설정
        self.button_long = tk.Button(
            self.button_frame,
            text='긴 휴식',
            font=(FONT_NAME, LABEL_SIZE),
            command=self.switch_to_long  # 긴 휴식 모드로 전환
        )
        # 세 번째 열에 버튼 배치
        self.button_long.grid(row=1, column=2, sticky='EW', padx=2, pady=2)

    def setup_window(self):
        # 창 크기 변경 비활성화
        self.resizable(False, False)  # 너비, 높이 모두 고정
        
        # 창 크기 설정
        window_width = 300   # 창의 너비
        window_height = 140  # 창의 높이
        
        # 화면 중앙 좌표 계산
        screen_width = self.winfo_screenwidth()   # 화면 전체 너비
        screen_height = self.winfo_screenheight() # 화면 전체 높이
        # 창을 화면 중앙에 배치하기 위한 x, y 좌표 계산
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        
        # 창 위치 및 크기 설정
        # 형식: 너비x높이+x좌표+y좌표
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    def toggle_timer(self, event=None):
        # 타이머 시작/정지 토글
        # 가상 클릭 이벤트를 사용하여 카운터의 상태 전환
        self.counter.clicked(CLICK_EVENT)
        
    def ticker(self):
        # 주기적인 타이머 업데이트 (1초마다)
        self.after(1000, self.ticker)  # 1초 후 다시 실행
        self.counter.tick()  # 카운터 업데이트

    def switch_to_work(self):
        # 작업 시간 모드로 전환
        self.counter.switch_to_work()
        
    def switch_to_short(self):
        # 짧은 휴식 모드로 전환
        self.counter.switch_to_short()
        
    def switch_to_long(self):
        # 긴 휴식 모드로 전환
        self.counter.switch_to_long()

    def reset_timer(self):
        # 현재 모드의 타이머를 초기값으로 재설정
        self.counter.reset_current_mode()

class Counter:
    # 타이머의 핵심 기능을 담당하는 클래스
    def __init__(self, master):
        self.master = master  # 부모 위젯 저장
        self.frame = tk.Frame(master)  # 카운터를 담을 프레임 생성
        
        # 프레임 레이아웃 설정
        self.frame.grid_rowconfigure(0, weight=1)  # 상태 표시줄 행
        self.frame.grid_rowconfigure(1, weight=1)  # 타이머 표시 행
        self.frame.grid_columnconfigure(0, weight=1)  # 단일 열
        
        # 타이머 모드별 시간 설정
        self.work_time = POMODORO_WORK  # 작업 시간
        self.short_break_time = POMODORO_SHORT_BREAK  # 짧은 휴식 시간
        self.long_break_time = POMODORO_LONG_BREAK  # 긴 휴식 시간
        
        # 초기 상태 설정
        self.current_mode = 'work'  # 현재 모드 (work/short_break/long_break)
        self.time = self.work_time  # 현재 남은 시간
        self.paused = True  # 일시정지 상태
        # 타이머 텍스트 색상 토글 객체 생성
        self.text_colour = Toggle(TIMER_INACTIVE_COLOUR, TIMER_ACTIVE_COLOUR)
        
        # GUI 레이블 생성
        self._create_labels()
        
        # 뽀모도로 사이클 관리 변수
        self.pomodoro_cycle = 0  # 완료한 작업 사이클 수
        self.is_break = False    # 현재 휴식 시간 여부

    def _create_labels(self):
        # 상태 표시 레이블 생성
        self.status_label = tk.Label(
            self.frame,
            text="작업 시간",  # 초기 상태 텍스트
            font=(FONT_NAME, LABEL_SIZE),
            anchor='center'  # 중앙 정렬
        )
        self.status_label.grid(column=0, row=0, sticky='NSEW')
        
        # 시간 표시 레이블 생성
        self.time_label = tk.Label(
            self.frame,
            text=self.format_time(),  # 시간을 MM:SS 형식으로 표시
            font=(FONT_NAME, TIME_SIZE),
            fg=TIMER_INACTIVE_COLOUR,  # 초기 색상은 비활성 상태
            anchor='center'  # 중앙 정렬
        )
        self.time_label.grid(column=0, row=1, sticky='NSEW')

    def reset_current_mode(self):
        # 현재 모드에 따른 시간 초기화
        if self.current_mode == 'work':
            self.time = POMODORO_WORK
        elif self.current_mode == 'short_break':
            self.time = POMODORO_SHORT_BREAK
        else:  # long_break
            self.time = POMODORO_LONG_BREAK
            
        # 상태 초기화
        self.paused = True  # 일시정지 상태로 설정
        self.text_colour.reset()  # 색상을 초기 상태로 복원
        self.refresh()  # 화면 갱신

    def tick(self):
        # 타이머 시간 갱신 (1초마다 호출됨)
        if not self.paused:  # 일시정지 상태가 아닐 때만
            self.time -= 1  # 1초 감소
            if self.time <= 0:  # 시간이 모두 경과했을 때
                self.handle_timer_completion()  # 타이머 완료 처리
            self.refresh()  # 화면 갱신

    def handle_timer_completion(self):
        # 타이머 완료 시 동작을 처리하는 메서드
        if not self.is_break:
            # 작업 시간이 완료된 경우
            self.pomodoro_cycle += 1  # 작업 사이클 카운트 증가
            if self.pomodoro_cycle % POMODORO_CYCLES == 0:
                # 설정된 사이클 수에 도달하면 긴 휴식으로 전환
                self.switch_to_long()
            else:
                # 그렇지 않으면 짧은 휴식으로 전환
                self.switch_to_short()
        else:
            # 휴식 시간이 완료된 경우 작업 모드로 전환
            self.switch_to_work()
        
        # 알림음 직접 재생
        try:
            winsound.PlaySound('alarm.wav', winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            pass  # 알림음 재생 실패 시 무시
        
        # 타이머 완료 메시지 표시
        self._show_completion_message()
        
        # 다음 타이머 자동 시작을 위한 설정
        self.paused = False  # 일시정지 해제
        self.text_colour.value = TIMER_ACTIVE_COLOUR  # 활성 상태 색상으로 변경
        self.refresh()  # 화면 갱신

    def _show_completion_message(self):
        # 타이머 완료시 현재 모드에 따른 메시지 표시
        messages = {
            'work': "작업 시작!",
            'short_break': "짧고 달콤한 휴식 시간~",
            'long_break': "수고하셨어요! 충분한 휴식을 취하세요!"
        }
        # 현재 모드에 해당하는 메시지를 팝업으로 표시
        messagebox.showinfo("알림", messages.get(self.current_mode, "타이머 완료!"))

    def format_time(self):
        # 남은 시간을 MM:SS 형식의 문자열로 변환
        minutes = self.time // 60  # 분 계산
        seconds = self.time % 60   # 초 계산
        return f"{minutes:02d}:{seconds:02d}"  # 두 자리 숫자로 포맷팅

    def refresh(self):
        # 화면 갱신 - 타이머 표시 업데이트
        self.time_label.config(
            text=self.format_time(),  # 시간 표시 업데이트
            fg=self.text_colour.value  # 색상 업데이트
        )

    def clicked(self, event):
        # 타이머 시작/정지 토글 처리
        self.paused = not self.paused  # 일시정지 상태 전환
        self.text_colour.flip()  # 색상 상태 전환
        self.refresh()  # 화면 갱신

    def switch_to_work(self):
        # 작업 시간 모드로 전환
        self.time = POMODORO_WORK  # 작업 시간으로 설정
        self.current_mode = 'work'  # 현재 모드 변경
        self.status_label.config(text="작업 시간")  # 상태 표시 업데이트
        self.is_break = False  # 휴식 상태 해제
        self.refresh()  # 화면 갱신
        
    def switch_to_short(self):
        # 짧은 휴식 모드로 전환
        self.time = POMODORO_SHORT_BREAK  # 짧은 휴식 시간으로 설정
        self.current_mode = 'short_break'  # 현재 모드 변경
        self.status_label.config(text="짧은 휴식 시간")  # 상태 표시 업데이트
        self.is_break = True  # 휴식 상태로 설정
        self.refresh()  # 화면 갱신
        
    def switch_to_long(self):
        # 긴 휴식 모드로 전환
        self.time = POMODORO_LONG_BREAK  # 긴 휴식 시간으로 설정
        self.current_mode = 'long_break'  # 현재 모드 변경
        self.status_label.config(text="긴 휴식 시간")  # 상태 표시 업데이트
        self.is_break = True  # 휴식 상태로 설정
        self.refresh()  # 화면 갱신

def main():
    # 메인 함수: 애플리케이션 실행
    app = Timer()  # 타이머 인스턴스 생성
    app.mainloop()  # 메인 이벤트 루프 시작


main()