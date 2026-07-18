"""
이미지 처리 및 스펙트럼 분석 모듈 (Image Processing & Spectrum Analysis)
Nile Red 형광 영역을 검출하고 스펙트럼 피크를 분석합니다.
"""

import logging
import numpy as np
import cv2
from scipy.signal import find_peaks
from typing import Tuple, Dict, Optional
import config


class SpectrumAnalyzer:
    """
    이미지 처리 및 스펙트럼 분석 클래스
    - HSV 색공간에서 형광 영역(ROI) 검출
    - 2D 이미지를 1D 스펙트럼으로 변환
    - 피크 분석을 통한 마이크로플라스틱 검출
    """

    def __init__(self):
        """
        분석기 초기화
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("스펙트럼 분석기 초기화 완료")

    def detect_fluorescence_roi(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Nile Red 형광 영역(ROI) 검출

        Args:
            image (np.ndarray): RGB 이미지 배열 (H, W, 3)

        Returns:
            Optional[np.ndarray]: 크롭된 ROI 이미지, 검출 실패 시 None
        """
        try:
            # 1. RGB → HSV 색공간 변환
            hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

            # 2. HSV 범위로 마스크 생성 (노란색-주황색 형광 영역)
            mask = cv2.inRange(hsv_image, config.HSV_LOWER, config.HSV_UPPER)

            # 3. 모폴로지 연산으로 노이즈 제거
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # 구멍 메우기
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # 작은 노이즈 제거

            # 4. 윤곽선 검출
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if not contours:
                self.logger.warning("형광 영역을 찾을 수 없습니다.")
                return None

            # 5. 가장 큰 윤곽선 선택 (면적 기준)
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)

            # 6. 최소 면적 확인
            if area < config.MIN_ROI_AREA:
                self.logger.warning(f"ROI 면적이 너무 작습니다: {area} < {config.MIN_ROI_AREA}")
                return None

            # 7. 바운딩 박스 추출 및 마진 추가
            x, y, w, h = cv2.boundingRect(largest_contour)
            margin = config.ROI_MARGIN

            # 이미지 경계를 벗어나지 않도록 조정
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(image.shape[1], x + w + margin)
            y2 = min(image.shape[0], y + h + margin)

            # 8. ROI 크롭
            roi = image[y1:y2, x1:x2]

            self.logger.debug(f"ROI 검출 완료: 위치=({x1},{y1}), 크기=({x2-x1}x{y2-y1})")
            return roi

        except Exception as e:
            self.logger.error(f"ROI 검출 중 오류 발생: {e}")
            return None

    def image_to_spectrum(self, roi: np.ndarray) -> np.ndarray:
        """
        2D 이미지를 1D 스펙트럼 데이터로 변환

        Args:
            roi (np.ndarray): ROI 이미지 (H, W, 3)

        Returns:
            np.ndarray: 1D 스펙트럼 배열 (각 열의 밝기 합)
        """
        try:
            # 1. RGB를 그레이스케일로 변환 (밝기 정보만 사용)
            # 공식: Y = 0.299*R + 0.587*G + 0.114*B (표준 Luma 변환)
            gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)

            # 2. 세로 방향으로 합산 (axis=0: 행 방향 합산 → 각 열의 합)
            # 예: [[4, 10], [1, 10]] → [5, 20]
            spectrum = np.sum(gray, axis=0, dtype=np.float64)

            self.logger.debug(f"스펙트럼 변환 완료: 길이={len(spectrum)}, "
                            f"최대값={np.max(spectrum):.1f}, 평균={np.mean(spectrum):.1f}")

            return spectrum

        except Exception as e:
            self.logger.error(f"스펙트럼 변환 중 오류 발생: {e}")
            return np.array([])

    def analyze_peaks(self, spectrum: np.ndarray) -> Dict[str, any]:
        """
        스펙트럼에서 피크를 분석하여 마이크로플라스틱 검출

        Args:
            spectrum (np.ndarray): 1D 스펙트럼 배열

        Returns:
            Dict: 분석 결과 딕셔너리
                - peak_count (int): 검출된 피크 개수
                - peak_positions (list): 피크 위치 (인덱스)
                - peak_heights (list): 피크 높이 값
                - mean_intensity (float): 스펙트럼 평균 강도
                - concentration (float): 추정 농도
        """
        try:
            if spectrum.size == 0:
                return self._empty_result()

            # 1. scipy.signal.find_peaks로 피크 검출
            peaks, properties = find_peaks(
                spectrum,
                height=config.PEAK_HEIGHT,        # 최소 높이
                distance=config.PEAK_DISTANCE,    # 최소 간격
                prominence=config.PEAK_PROMINENCE  # 돌출도
            )

            # 2. 통계 정보 계산
            peak_count = len(peaks)
            peak_positions = peaks.tolist()
            peak_heights = spectrum[peaks].tolist() if peak_count > 0 else []
            mean_intensity = float(np.mean(spectrum))

            # 3. 농도 추정 (간단한 선형 모델)
            # 농도 = (피크 개수 × 계수) + (평균 강도 × 가중치)
            concentration = (peak_count * config.CONCENTRATION_COEFFICIENT +
                           mean_intensity * config.INTENSITY_WEIGHT)

            self.logger.debug(f"피크 분석 완료: 피크={peak_count}개, 농도={concentration:.2f}")

            return {
                "peak_count": peak_count,
                "peak_positions": peak_positions,
                "peak_heights": peak_heights,
                "mean_intensity": mean_intensity,
                "concentration": concentration
            }

        except Exception as e:
            self.logger.error(f"피크 분석 중 오류 발생: {e}")
            return self._empty_result()

    def process_image(self, image: np.ndarray) -> Dict[str, any]:
        """
        전체 이미지 처리 파이프라인
        ROI 검출 → 스펙트럼 변환 → 피크 분석

        Args:
            image (np.ndarray): 원본 RGB 이미지

        Returns:
            Dict: 분석 결과 딕셔너리
        """
        # 1단계: ROI 검출
        roi = self.detect_fluorescence_roi(image)
        if roi is None:
            return self._empty_result()

        # 2단계: 스펙트럼 변환
        spectrum = self.image_to_spectrum(roi)
        if spectrum.size == 0:
            return self._empty_result()

        # 3단계: 피크 분석
        result = self.analyze_peaks(spectrum)

        return result

    @staticmethod
    def _empty_result() -> Dict[str, any]:
        """
        검출 실패 시 반환할 빈 결과 딕셔너리
        """
        return {
            "peak_count": 0,
            "peak_positions": [],
            "peak_heights": [],
            "mean_intensity": 0.0,
            "concentration": 0.0
        }
