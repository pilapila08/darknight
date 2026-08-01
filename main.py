"""黑暗之夜 - 主程序"""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, ENABLE_TEST_MODE
from ui import (
    draw_start_screen, handle_start_screen_input, get_font,
    draw_character_select, handle_character_select_input, build_character_select_layout,
)
from game import NormalGame, TestGame
from systems.save_data import load_meta, load_unlocks, refresh_unlocks, load_high_score
from i18n import t



def _ensure_pygame_ready():
    """确保 pygame 已正确初始化"""
    if not pygame.get_init():
        pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(t("window_caption"))
    clock = pygame.time.Clock()

    font = get_font(24)
    big_font = get_font(48)
    small_font = get_font(14)

    running = True
    game_mode = None
    # R5：主菜单流程 = 开始界面 → 角色选择 → 游戏
    screen_state = "start"          # "start" | "chars" | None(游戏中)
    pending_mode = "normal"         # 从开始界面选择的是 normal 还是 test
    selected_character = "default"
    meta_cache = {}
    unlocks_cache = {}
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

            if screen_state == "start":
                # 收集密码输入
                if event.type == pygame.TEXTINPUT:
                    char = event.text.lower()
                    test_code_buffer += char
                    # 保持缓冲长度，防止无限增长
                    if len(test_code_buffer) > 20:
                        test_code_buffer = test_code_buffer[-10:]
                    # 检查密码
                    if "yygbc" in test_code_buffer and ENABLE_TEST_MODE:
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
                    # 进入角色选择层：刷新解锁 + 载入统计
                    refresh_unlocks()
                    meta_cache = load_meta()
                    meta_cache["high_score"] = load_high_score()
                    unlocks_cache = load_unlocks()
                    pending_mode = selected
                    selected_character = "default"
                    screen_state = "chars"
                    break

            elif screen_state == "chars":
                card_rects, start_btn_rect, back_btn_rect = build_character_select_layout(
                    screen.get_width(), screen.get_height())
                action = handle_character_select_input(
                    event, card_rects, start_btn_rect, back_btn_rect,
                    selected_character, unlocks_cache)
                if action == "back":
                    screen_state = "start"
                    continue
                elif action and action.startswith("select:"):
                    ch = action.split(":", 1)[1]
                    if unlocks_cache.get(ch, True):
                        selected_character = ch
                elif action == "start":
                    # 防御：锁定角色不允许启动（正常流程不会选中锁定角色）
                    if unlocks_cache.get(selected_character, True):
                        game_mode = pending_mode
                        screen_state = None
                        break

        # 绘制开始界面
        if screen_state == "start":
            draw_start_screen(screen, big_font, font, small_font, test_activated)
            pygame.display.flip()
            continue

        # 绘制角色选择层
        if screen_state == "chars":
            card_rects, start_btn_rect, back_btn_rect = build_character_select_layout(
                screen.get_width(), screen.get_height())
            draw_character_select(
                screen, big_font, font, small_font, selected_character,
                meta_cache, unlocks_cache, card_rects, start_btn_rect, back_btn_rect)
            pygame.display.flip()
            continue

        # 运行选定的游戏模式
        pygame.display.flip()

        if game_mode == "normal":
            NormalGame(selected_character).run()
        elif game_mode == "test":
            TestGame(selected_character).run()

        # 游戏结束后返回主菜单，重新初始化 pygame
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        game_mode = None
        screen_state = "start"
        selected_character = "default"
        test_activated = False  # 重置测试模式激活状态
        test_code_buffer = ""   # 清空密码缓冲

    pygame.quit()


if __name__ == "__main__":
    main()
