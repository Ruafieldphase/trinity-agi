"""
Image Comparison Utility
Phase 2.5 Week 2 Day 12

이미지 유사도 비교 (SSIM, MSE, Histogram)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import logging

import numpy as np
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import cv2

logger = logging.getLogger(__name__)


@dataclass
class ComparisonResult:
    """이미지 비교 결과"""
    method: str                    # 비교 방법 (SSIM, MSE, HISTOGRAM)
    similarity: float             # 유사도 (0.0 ~ 1.0, 높을수록 유사)
    difference: float             # 차이도 (0.0 ~, 낮을수록 유사)
    is_similar: bool              # 유사 여부
    threshold: float              # 사용된 임계값
    metadata: dict                # 추가 정보
    
    def __str__(self) -> str:
        return (
            f"{self.method}: "
            f"similarity={self.similarity:.4f}, "
            f"difference={self.difference:.4f}, "
            f"is_similar={self.is_similar}"
        )


class ImageComparator:
    """
    이미지 비교 유틸리티
    
    Methods:
    - SSIM: Structural Similarity Index (구조적 유사도)
    - MSE: Mean Squared Error (평균 제곱 오차)
    - Histogram: 히스토그램 비교
    
    Features:
    - 다양한 비교 알고리즘
    - 자동 크기 조정
    - 임계값 기반 판정
    """
    
    def __init__(
        self,
        ssim_threshold: float = 0.95,
        mse_threshold: float = 100.0,
        histogram_threshold: float = 0.9
    ):
        """
        Args:
            ssim_threshold: SSIM 임계값 (0.95 = 95% 유사)
            mse_threshold: MSE 임계값 (작을수록 유사)
            histogram_threshold: 히스토그램 유사도 임계값
        """
        self.ssim_threshold = ssim_threshold
        self.mse_threshold = mse_threshold
        self.histogram_threshold = histogram_threshold
    
    def compare_ssim(
        self,
        img1: Union[Image.Image, np.ndarray, Path, str],
        img2: Union[Image.Image, np.ndarray, Path, str],
        grayscale: bool = True
    ) -> ComparisonResult:
        """
        SSIM (Structural Similarity Index)로 비교
        
        구조적 유사도를 측정 (사람 눈에 보이는 유사도와 비슷함)
        
        Args:
            img1, img2: 비교할 이미지
            grayscale: 그레이스케일로 변환할지 여부
        
        Returns:
            ComparisonResult
        """
        logger.debug("Comparing images with SSIM...")
        
        # 이미지 로드 및 정규화
        arr1 = self._load_and_normalize(img1, grayscale=grayscale)
        arr2 = self._load_and_normalize(img2, grayscale=grayscale)
        
        # 크기 확인 및 조정
        if arr1.shape != arr2.shape:
            logger.warning(
                f"Image sizes differ: {arr1.shape} vs {arr2.shape}, "
                "resizing img2 to match img1..."
            )
            arr2 = self._resize_to_match(arr2, arr1.shape)
        
        # SSIM 계산
        # data_range 지정 (float이므로 0~1)
        if grayscale:
            score, diff = ssim(arr1, arr2, full=True, data_range=1.0)
        else:
            # 컬러 이미지는 채널별로 계산
            score, diff = ssim(arr1, arr2, full=True, channel_axis=2, data_range=1.0)
        
        # 0 ~ 1 범위 정규화 (SSIM은 원래 -1 ~ 1)
        similarity = (score + 1) / 2 if score < 0 else score
        
        is_similar = similarity >= self.ssim_threshold
        
        return ComparisonResult(
            method="SSIM",
            similarity=similarity,
            difference=1.0 - similarity,
            is_similar=is_similar,
            threshold=self.ssim_threshold,
            metadata={
                "grayscale": grayscale,
                "shape": arr1.shape,
                "raw_ssim": score
            }
        )
    
    def compare_mse(
        self,
        img1: Union[Image.Image, np.ndarray, Path, str],
        img2: Union[Image.Image, np.ndarray, Path, str],
        grayscale: bool = True
    ) -> ComparisonResult:
        """
        MSE (Mean Squared Error)로 비교
        
        픽셀 단위 차이의 평균
        
        Args:
            img1, img2: 비교할 이미지
            grayscale: 그레이스케일로 변환할지 여부
        
        Returns:
            ComparisonResult
        """
        logger.debug("Comparing images with MSE...")
        
        # 이미지 로드 및 정규화
        arr1 = self._load_and_normalize(img1, grayscale=grayscale)
        arr2 = self._load_and_normalize(img2, grayscale=grayscale)
        
        # 크기 확인 및 조정
        if arr1.shape != arr2.shape:
            arr2 = self._resize_to_match(arr2, arr1.shape)
        
        # MSE 계산
        mse = np.mean((arr1 - arr2) ** 2)
        
        # 유사도 계산 (MSE를 0~1로 정규화, 낮을수록 유사)
        # MSE 범위: 0 (완전 동일) ~ 255^2 (완전 다름, 8비트 이미지 기준)
        max_mse = 255.0 ** 2
        similarity = 1.0 - min(mse / max_mse, 1.0)
        
        is_similar = mse <= self.mse_threshold
        
        return ComparisonResult(
            method="MSE",
            similarity=similarity,
            difference=mse,
            is_similar=is_similar,
            threshold=self.mse_threshold,
            metadata={
                "grayscale": grayscale,
                "shape": arr1.shape,
                "raw_mse": float(mse)
            }
        )
    
    def compare_histogram(
        self,
        img1: Union[Image.Image, np.ndarray, Path, str],
        img2: Union[Image.Image, np.ndarray, Path, str]
    ) -> ComparisonResult:
        """
        히스토그램 비교 (색상 분포 유사도)
        
        이미지의 색상 분포가 얼마나 유사한지 측정
        
        Args:
            img1, img2: 비교할 이미지
        
        Returns:
            ComparisonResult
        """
        logger.debug("Comparing images with Histogram...")
        
        # 이미지 로드 (컬러)
        arr1 = self._load_and_normalize(img1, grayscale=False)
        arr2 = self._load_and_normalize(img2, grayscale=False)
        
        # OpenCV는 BGR 순서 사용
        if arr1.shape[2] == 3:  # RGB → BGR
            arr1 = cv2.cvtColor((arr1 * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
            arr2 = cv2.cvtColor((arr2 * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
        
        # 히스토그램 계산
        hist1 = cv2.calcHist([arr1], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([arr2], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        # 정규화
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        
        # 비교 (Correlation)
        similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # 0 ~ 1 범위로 정규화
        similarity = (similarity + 1) / 2 if similarity < 0 else similarity
        
        is_similar = similarity >= self.histogram_threshold
        
        return ComparisonResult(
            method="HISTOGRAM",
            similarity=similarity,
            difference=1.0 - similarity,
            is_similar=is_similar,
            threshold=self.histogram_threshold,
            metadata={
                "histogram_bins": "8x8x8",
                "comparison_method": "CORREL"
            }
        )
    
    def compare_all(
        self,
        img1: Union[Image.Image, np.ndarray, Path, str],
        img2: Union[Image.Image, np.ndarray, Path, str]
    ) -> dict[str, ComparisonResult]:
        """
        모든 방법으로 비교
        
        Args:
            img1, img2: 비교할 이미지
        
        Returns:
            {method_name: ComparisonResult}
        """
        logger.info("Comparing images with all methods...")
        
        results = {
            "SSIM": self.compare_ssim(img1, img2),
            "MSE": self.compare_mse(img1, img2),
            "HISTOGRAM": self.compare_histogram(img1, img2)
        }
        
        return results
    
    def is_similar(
        self,
        img1: Union[Image.Image, np.ndarray, Path, str],
        img2: Union[Image.Image, np.ndarray, Path, str],
        method: str = "SSIM"
    ) -> bool:
        """
        두 이미지가 유사한지 간단히 판정
        
        Args:
            img1, img2: 비교할 이미지
            method: 비교 방법 (SSIM, MSE, HISTOGRAM)
        
        Returns:
            유사 여부
        """
        method = method.upper()
        
        if method == "SSIM":
            result = self.compare_ssim(img1, img2)
        elif method == "MSE":
            result = self.compare_mse(img1, img2)
        elif method == "HISTOGRAM":
            result = self.compare_histogram(img1, img2)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return result.is_similar
    
    # ========================================================================
    # Internal Methods
    # ========================================================================
    
    def _load_and_normalize(
        self,
        img: Union[Image.Image, np.ndarray, Path, str],
        grayscale: bool = True
    ) -> np.ndarray:
        """이미지 로드 및 정규화 (0.0 ~ 1.0)"""
        # 이미 numpy 배열이면 그대로
        if isinstance(img, np.ndarray):
            arr = img
        # PIL Image
        elif isinstance(img, Image.Image):
            arr = np.array(img)
        # 파일 경로
        else:
            pil_img = Image.open(img)
            arr = np.array(pil_img)
        
        # 그레이스케일 변환
        if grayscale and len(arr.shape) == 3:
            # RGB → Grayscale
            if arr.shape[2] == 3:
                arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
            elif arr.shape[2] == 4:
                arr = cv2.cvtColor(arr, cv2.COLOR_RGBA2GRAY)
        
        # 0.0 ~ 1.0 정규화
        if arr.dtype == np.uint8:
            arr = arr.astype(np.float32) / 255.0
        
        return arr
    
    def _resize_to_match(
        self,
        img: np.ndarray,
        target_shape: tuple
    ) -> np.ndarray:
        """이미지 크기를 target_shape에 맞게 조정"""
        if len(target_shape) == 2:  # Grayscale
            target_height, target_width = target_shape
        else:  # Color
            target_height, target_width, _ = target_shape
        
        # OpenCV resize (0.0~1.0 float 배열도 처리 가능)
        resized = cv2.resize(
            img,
            (target_width, target_height),
            interpolation=cv2.INTER_AREA
        )
        
        return resized


# ============================================================================
# Convenience Functions
# ============================================================================

def are_images_similar(
    img1: Union[Image.Image, Path, str],
    img2: Union[Image.Image, Path, str],
    method: str = "SSIM",
    threshold: float = 0.95
) -> bool:
    """
    간편한 이미지 유사도 판정
    
    Args:
        img1, img2: 비교할 이미지
        method: 비교 방법 (SSIM, MSE, HISTOGRAM)
        threshold: 임계값
    
    Returns:
        유사 여부
    """
    if method.upper() == "SSIM":
        comparator = ImageComparator(ssim_threshold=threshold)
    elif method.upper() == "MSE":
        comparator = ImageComparator(mse_threshold=threshold)
    elif method.upper() == "HISTOGRAM":
        comparator = ImageComparator(histogram_threshold=threshold)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return comparator.is_similar(img1, img2, method=method)


def get_similarity_score(
    img1: Union[Image.Image, Path, str],
    img2: Union[Image.Image, Path, str],
    method: str = "SSIM"
) -> float:
    """
    간편한 유사도 점수 계산
    
    Args:
        img1, img2: 비교할 이미지
        method: 비교 방법
    
    Returns:
        유사도 (0.0 ~ 1.0)
    """
    comparator = ImageComparator()
    
    if method.upper() == "SSIM":
        result = comparator.compare_ssim(img1, img2)
    elif method.upper() == "MSE":
        result = comparator.compare_mse(img1, img2)
    elif method.upper() == "HISTOGRAM":
        result = comparator.compare_histogram(img1, img2)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return result.similarity


# ============================================================================
# CLI
# ============================================================================

if __name__ == '__main__':
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    if len(sys.argv) < 3:
        print("Usage: python image_comparator.py <image1> <image2> [method]")
        sys.exit(1)
    
    img1_path = sys.argv[1]
    img2_path = sys.argv[2]
    method = sys.argv[3] if len(sys.argv) > 3 else "all"
    
    comparator = ImageComparator()
    
    print("\n" + "="*60)
    print("  Image Comparison")
    print("="*60)
    print(f"  Image 1: {img1_path}")
    print(f"  Image 2: {img2_path}")
    print("="*60 + "\n")
    
    if method.lower() == "all":
        results = comparator.compare_all(img1_path, img2_path)
        for name, result in results.items():
            print(f"[{name}]")
            print(f"  {result}")
            print()
    else:
        if method.upper() == "SSIM":
            result = comparator.compare_ssim(img1_path, img2_path)
        elif method.upper() == "MSE":
            result = comparator.compare_mse(img1_path, img2_path)
        elif method.upper() == "HISTOGRAM":
            result = comparator.compare_histogram(img1_path, img2_path)
        else:
            print(f"Unknown method: {method}")
            sys.exit(1)
        
        print(f"[{result.method}]")
        print(f"  {result}")
        print()
    
    print("="*60 + "\n")
