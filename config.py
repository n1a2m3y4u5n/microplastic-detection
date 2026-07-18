"""
설정 파일 (Configuration File)
마이크로플라스틱 검출 시스템의 모든 파라미터를 관리합니다.
"""

# ========================================
# 카메라 설정 (Camera Settings)
# ========================================
CAMERA_RESOLUTION = (1280, 720)  # 해상도: 너비 x 높이
FRAME_RATE = 30  # 초당 프레임 수
EXPOSURE_TIME = 20000  # 노출 시간 (마이크로초 단위, 20ms = 20000μs)
ANALOGUE_GAIN = 8.0  # 아날로그 게인 (신호 증폭)

# ========================================
# HSV 색상 범위 설정 (HSV Color Range for Nile Red Fluorescence)
# ========================================
# Nile Red 형광: 노란색-주황색 스펙트럼
# HSV 색상 공간에서 형광 영역을 검출하기 위한 임계값

# 하한값 (Lower Bound): Hue, Saturation, Value
HSV_LOWER = (15, 100, 100)  # H: 15° (노란색 시작), S: 100, V: 100

# 상한값 (Upper Bound)
HSV_UPPER = (35, 255, 255)  # H: 35° (주황색 끝), S: 255, V: 255

# ========================================
# ROI 검출 설정 (ROI Detection Settings)
# ========================================
MIN_ROI_AREA = 500  # 최소 ROI 면적 (픽셀 단위, 노이즈 제거용)
ROI_MARGIN = 10  # ROI 경계 확장 마진 (픽셀)

# ========================================
# 스펙트럼 분석 설정 (Spectrum Analysis Settings)
# ========================================
# scipy.signal.find_peaks() 파라미터
PEAK_HEIGHT = 50  # 피크 최소 높이 (픽셀 강도 합)
PEAK_DISTANCE = 5  # 피크 간 최소 거리 (픽셀)
PEAK_PROMINENCE = 30  # 피크 돌출도 (주변 대비 높이 차이)

# ========================================
# 농도 추정 설정 (Concentration Estimation)
# ========================================
# 마이크로플라스틱 농도 = (피크 개수) × (계수) + (평균 강도) × (가중치)
CONCENTRATION_COEFFICIENT = 10.0  # 피크당 농도 기여도
INTENSITY_WEIGHT = 0.05  # 평균 강도 가중치

# ========================================
# 로깅 설정 (Logging Settings)
# ========================================
LOG_FILE = "microplastic_detection.log"  # 시스템 로그 파일
CSV_FILE = "detection_results.csv"  # 분석 결과 CSV 파일
LOG_INTERVAL = 1.0  # CSV 기록 주기 (초)

# ========================================
# 시스템 설정 (System Settings)
# ========================================
HEADLESS_MODE = True  # 모니터 없이 실행 (True: 헤드리스, False: GUI)
DEBUG_MODE = False  # 디버그 모드 (True: 이미지 저장 활성화)
