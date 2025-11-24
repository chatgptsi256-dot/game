import pygame
import sys
import main_menu
import main_game
import shop
import json

def main():
    pygame.init()
    pygame.display.set_caption("Top-Down Shooter")

    while True:
        choice = main_menu.show_menu()  # → 'start' или 'exit'
        if choice == "start":
            # Передаём режим фуллскрина из меню в игру
            fullscreen = getattr(main_menu, "FULLSCREEN", False)
            # load purchases
            try:
                with open("purchases.json", "r", encoding="utf-8") as f:
                    purchases = json.load(f)
            except Exception:
                purchases = {}
            result = main_game.main(fullscreen=fullscreen, purchases=purchases)   # → 'game_over' или 'quit'
            if result == "quit":
                pygame.quit()
                sys.exit()
            elif result == "game_over":
                continue  # возвращаемся в меню
        elif choice == "shop":
            fullscreen = getattr(main_menu, "FULLSCREEN", False)
            back = shop.show_shop(fullscreen=fullscreen)
            # при возврате — просто снова показать меню
        elif choice == "exit":
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()