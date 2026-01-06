
def safe_divide(a, b):
    # 의도적인 버그: 0으로 나누기 예외 처리가 없음
    return a / b

if __name__ == "__main__":
    print(safe_divide(10, 0))
