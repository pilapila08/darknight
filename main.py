"""黑暗之夜 - 主程序"""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, ENABLE_TEST_MODE
from ui import draw_start_screen, handle_start_screen_input, get_font
from game import NormalGame, TestGame


def _ensure_pygame_ready():
    """确保 pygame 已正确初始化"""
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("暗夜求生  |  F11 全屏")
    clock = pygame.time.Clock()

    font = get_font(24)
    big_font = get_font(48)
    small_font = get_font(14)

    running = True
    game_mode = None
    test_code_buffer = ""  # 测试模式密码输入缓冲
    test_activated = False  # 测试模式是否已激活

    while running:
        dt = clock.tick(FPS) / 1000.0

        # 确保 pygame 处于可用状态
        _ensure_pygame_ready()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # 处理开始界面输入
            if game_mode is None:
                # 收集密码输入
                if event.type == pygame.TEXTINPUT:
                    char = event.text.lower()
                    test_code_buffer += char
                    # 保持缓冲长度，防止无限增长
                    if len(test_code_buffer) > 20:
                        test_code_buffer = test_code_buffer[-10:]
                    # 检查密码
                    if "yyjbc" in test_code_buffer and ENABLE_TEST_MODE:
                        test_activated = True
                        test_code_buffer = ""

                # 全屏切换（仅在开始界面可用）
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        continue

                btn_rect, test_btn_rect = draw_start_screen(
                    screen, big_font, font, small_font, test_activated)
                selected = handle_start_screen_input(
                    event, btn_rect, test_btn_rect, test_activated)
                if selected in ("normal", "test"):
                    game_mode = selected
                    break

        # 绘制开始界面
        if game_mode is None:
            draw_start_screen(screen, big_font, font, small_font, test_activated)
            pygame.display.flip()
            continue

        # 运行选定的游戏模式
        pygame.display.flip()

        if game_mode == "normal":
            NormalGame().run()
        elif game_mode == "test":
            TestGame().run()

        # 游戏结束后返回主菜单，重新初始化 pygame
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_mode = None
        test_activated = False  # 重置测试模式激活状态
        test_code_buffer = ""   # 清空密码缓冲

    pygame.quit()


if __name__ == "__main__":
    main()
