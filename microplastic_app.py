"""
웹 인터페이스 (Streamlit Web App)
마이크로플라스틱 검출 시스템 시뮬레이션을 웹 브라우저에서 실행합니다.
"""

import streamlit as st
import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import io
from PIL import Image

import config
from processor import SpectrumAnalyzer


class FluorescenceImageGenerator:
    """
    Nile Red 형광 이미지 생성기
    """

    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height

    def generate_image(self, num_particles=5, intensity_level='medium'):
        """
        합성 형광 이미지 생성

        Args:
            num_particles (int): 마이크로플라스틱 입자 개수
            intensity_level (str): 형광 강도 ('low', 'medium', 'high')

        Returns:
            np.ndarray: RGB 이미지 (H, W, 3)
        """
        # 검은 배경 생성
        image = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # 강도 레벨 설정
        intensity_map = {
            'low': (80, 120),
            'medium': (150, 220),
            'high': (200, 255)
        }
        min_intensity, max_intensity = intensity_map.get(intensity_level, (150, 220))

        # 형광 영역 중심 위치
        center_x = self.width // 2
        center_y = self.height // 2
        region_width = 400
        region_height = 200

        # 여러 개의 형광 스팟 생성
        for i in range(num_particles):
            x = center_x + np.random.randint(-region_width//2, region_width//2)
            y = center_y + np.random.randint(-region_height//2, region_height//2)
            radius = np.random.randint(20, 60)
            intensity = np.random.randint(min_intensity, max_intensity)

            # 노란색-주황색 색상
            hue = np.random.randint(20, 30)
            color_hsv = np.array([[[hue, 255, intensity]]], dtype=np.uint8)
            color_rgb = cv2.cvtColor(color_hsv, cv2.COLOR_HSV2RGB)[0, 0]

            # 가우시안 블러로 자연스러운 형광 효과
            temp_image = np.zeros_like(image)
            cv2.circle(temp_image, (x, y), radius, color_rgb.tolist(), -1)
            blurred = cv2.GaussianBlur(temp_image, (51, 51), 20)
            image = cv2.add(image, blurred)

        # 노이즈 추가
        noise = np.random.randint(0, 15, image.shape, dtype=np.uint8)
        image = cv2.add(image, noise)

        return image


def create_visualization(image, analyzer, scenario_name):
    """
    전체 처리 파이프라인 시각화

    Args:
        image (np.ndarray): 입력 이미지
        analyzer: SpectrumAnalyzer 인스턴스
        scenario_name (str): 시나리오 이름

    Returns:
        matplotlib figure
    """
    # Figure 생성
    fig = plt.figure(figsize=(18, 10))
    fig.suptitle(f'Microplastic Detection Pipeline - {scenario_name}',
                 fontsize=16, fontweight='bold')

    # 1. 원본 이미지
    ax1 = plt.subplot(2, 3, 1)
    ax1.imshow(image)
    ax1.set_title('1. Original Image', fontsize=12, fontweight='bold')
    ax1.axis('off')

    # 2. HSV 마스크
    ax2 = plt.subplot(2, 3, 2)
    hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(hsv_image, config.HSV_LOWER, config.HSV_UPPER)
    ax2.imshow(mask, cmap='gray')
    ax2.set_title('2. HSV Masking', fontsize=12, fontweight='bold')
    ax2.axis('off')

    # 3. ROI 검출
    ax3 = plt.subplot(2, 3, 3)
    roi = analyzer.detect_fluorescence_roi(image)

    if roi is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        image_with_roi = image.copy()
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            cv2.rectangle(image_with_roi, (x, y), (x+w, y+h), (0, 255, 0), 3)

        ax3.imshow(image_with_roi)
        ax3.set_title(f'3. ROI Detection ({roi.shape[1]}x{roi.shape[0]})',
                     fontsize=12, fontweight='bold', color='green')
    else:
        ax3.imshow(image)
        ax3.set_title('3. ROI Detection Failed', fontsize=12, fontweight='bold', color='red')

    ax3.axis('off')

    # 4. 크롭된 ROI
    ax4 = plt.subplot(2, 3, 4)
    if roi is not None:
        ax4.imshow(roi)
        ax4.set_title('4. Cropped ROI', fontsize=12, fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No ROI', ha='center', va='center', fontsize=14, color='red')
        ax4.set_title('4. No ROI', fontsize=12, fontweight='bold')
    ax4.axis('off')

    # 5. 1D 스펙트럼
    ax5 = plt.subplot(2, 3, 5)

    if roi is not None:
        spectrum = analyzer.image_to_spectrum(roi)
        result = analyzer.analyze_peaks(spectrum)

        x_axis = np.arange(len(spectrum))
        ax5.plot(x_axis, spectrum, color='blue', linewidth=1.5, label='Spectrum')
        ax5.fill_between(x_axis, spectrum, alpha=0.3, color='blue')

        if result['peak_count'] > 0:
            peak_positions = result['peak_positions']
            peak_heights = result['peak_heights']
            ax5.plot(peak_positions, peak_heights, 'ro', markersize=10,
                    label=f"Peaks ({result['peak_count']})")

            for pos, height in zip(peak_positions, peak_heights):
                ax5.annotate(f'{int(height)}', xy=(pos, height), xytext=(0, 10),
                           textcoords='offset points', ha='center', fontsize=9,
                           color='red', fontweight='bold')

        ax5.axhline(y=config.PEAK_HEIGHT, color='orange', linestyle='--',
                   linewidth=1, label=f'Min Height ({config.PEAK_HEIGHT})')
        ax5.set_xlabel('Pixel Position (X-axis)', fontsize=10)
        ax5.set_ylabel('Intensity', fontsize=10)
        ax5.set_title('5. 1D Spectrum Analysis', fontsize=12, fontweight='bold')
        ax5.legend(loc='upper right')
        ax5.grid(True, alpha=0.3)
    else:
        ax5.text(0.5, 0.5, 'No Spectrum', ha='center', va='center', fontsize=14, color='red')
        ax5.set_title('5. No Spectrum', fontsize=12, fontweight='bold')

    # 6. 분석 결과
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')

    if roi is not None:
        result = analyzer.process_image(image)

        result_text = f"""
Analysis Results

Peak Count: {result['peak_count']}

Peak Positions: {result['peak_positions'][:5]}{'...' if len(result['peak_positions']) > 5 else ''}

Mean Intensity: {result['mean_intensity']:.2f}

Concentration: {result['concentration']:.2f}

{'Detected!' if result['peak_count'] > 0 else 'Not Detected'}
        """

        if result['concentration'] > 100:
            bgcolor = '#ffcccc'
            status = 'High Concentration'
        elif result['concentration'] > 50:
            bgcolor = '#fff4cc'
            status = 'Medium Concentration'
        elif result['concentration'] > 0:
            bgcolor = '#ccffcc'
            status = 'Low Concentration'
        else:
            bgcolor = '#f0f0f0'
            status = 'Not Detected'

        ax6.text(0.5, 0.5, result_text, ha='center', va='center',
                fontsize=11, family='monospace',
                bbox=dict(boxstyle='round', facecolor=bgcolor, alpha=0.8))
        ax6.set_title(f'6. Results - {status}', fontsize=12, fontweight='bold')
    else:
        ax6.text(0.5, 0.5, 'Analysis Failed\nNo fluorescence region found',
                ha='center', va='center', fontsize=14, color='red')
        ax6.set_title('6. Analysis Failed', fontsize=12, fontweight='bold', color='red')

    plt.tight_layout()
    return fig


def main():
    """
    Streamlit 메인 앱
    """
    # 페이지 설정
    st.set_page_config(
        page_title="Microplastic Detection System",
        page_icon="🔬",
        layout="wide"
    )

    # 타이틀
    st.title("🔬 Microplastic Detection System Simulator")
    st.markdown("### Real-time Detection Using Nile Red Fluorescence Dye")
    st.markdown("---")

    # 사이드바 설정
    st.sidebar.header("⚙️ Simulation Settings")

    # 입자 개수 선택
    num_particles = st.sidebar.slider(
        "Number of Microplastic Particles",
        min_value=0,
        max_value=15,
        value=5,
        step=1,
        help="Number of fluorescent particles to generate"
    )

    # 형광 강도 선택
    intensity_level = st.sidebar.selectbox(
        "Fluorescence Intensity",
        options=['low', 'medium', 'high'],
        index=1,
        format_func=lambda x: x.capitalize(),
        help="Intensity of Nile Red fluorescence"
    )

    # 이미지 생성 버튼
    if st.sidebar.button("🎲 Generate New Image", type="primary"):
        st.session_state['generate_new'] = True

    # 시뮬레이션 실행
    if 'generate_new' not in st.session_state:
        st.session_state['generate_new'] = True

    if st.session_state['generate_new']:
        with st.spinner('Generating image and analyzing...'):
            # 이미지 생성
            generator = FluorescenceImageGenerator()
            image = generator.generate_image(num_particles, intensity_level)

            # 분석 실행
            analyzer = SpectrumAnalyzer()

            # 시나리오 이름
            scenario_name = f"{num_particles} particles, {intensity_level.capitalize()} intensity"

            # 시각화
            fig = create_visualization(image, analyzer, scenario_name)

            # Streamlit에 표시
            st.pyplot(fig)

            # 분석 결과 표시
            result = analyzer.process_image(image)

            st.markdown("---")
            st.subheader("📊 Detailed Analysis Results")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Peak Count", f"{result['peak_count']}")

            with col2:
                st.metric("Mean Intensity", f"{result['mean_intensity']:.2f}")

            with col3:
                st.metric("Concentration", f"{result['concentration']:.2f}")

            with col4:
                if result['peak_count'] > 0:
                    st.success("✅ Detected")
                else:
                    st.error("❌ Not Detected")

            # 피크 상세 정보
            if result['peak_count'] > 0:
                st.markdown("### 🔍 Peak Details")
                peak_data = {
                    "Peak #": list(range(1, result['peak_count'] + 1)),
                    "Position (px)": result['peak_positions'],
                    "Height": [f"{h:.2f}" for h in result['peak_heights']]
                }
                st.table(peak_data)

        st.session_state['generate_new'] = False

    # 정보 섹션
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 📖 System Information")
        st.markdown("""
        **Operating Principle:**
        1. Nile Red-stained microplastics
        2. Blue LED illumination
        3. Yellow-orange fluorescence emission
        4. HSV color space masking
        5. ROI detection and cropping
        6. 1D spectrum conversion
        7. Peak analysis & concentration estimation

        **Project:** High School Science Fair
        **Hardware:** Raspberry Pi 5 + Camera Module 3
        """)


if __name__ == "__main__":
    main()
