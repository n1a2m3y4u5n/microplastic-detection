# 마이크로플라스틱 검출 시스템 시뮬레이터

Nile Red 형광 염색을 이용한 마이크로플라스틱 검출 과정을 가상 이미지로 재현하는 Streamlit 웹앱입니다.

- 데모: https://microplastic-detection.fly.dev

## 소개

실제 카메라 대신, Nile Red로 염색한 마이크로플라스틱 입자가 형광을 내는 상황을 합성 이미지로 만들어서
검출 파이프라인 전체를 체험할 수 있게 만든 시뮬레이터입니다. 입자 개수와 형광 강도를 바꿔 가며
HSV 색공간 기반 검출, 1차원 스펙트럼 변환, 피크 분석까지 이어지는 과정을 단계별로 볼 수 있습니다.

## 주요 기능

- 입자 개수(0~15개), 형광 강도(low/medium/high)를 사이드바에서 설정해 합성 형광 이미지 생성
- HSV 색공간에서 형광 영역(ROI) 검출
- 2D 이미지를 1D 스펙트럼으로 변환
- `scipy.signal.find_peaks`로 피크 분석 및 농도 추정
- 피크 개수, 평균 강도, 추정 농도, 검출 여부, 피크별 상세 표 출력

## 기술

Python, Streamlit, OpenCV, NumPy, SciPy, Matplotlib.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run microplastic_app.py
```

## 알아 둘 것

`config.py`에는 실제 Raspberry Pi 5 + Camera Module 3로 촬영하는 것을 가정한 카메라 설정값(해상도, 노출, 게인 등)이 남아 있지만,
이 저장소의 앱은 그 값을 실제 카메라에 적용하지 않고 합성 이미지로 동작을 시뮬레이션합니다.
