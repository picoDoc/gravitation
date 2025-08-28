import asyncio
import pygame

pygame.init()
screen = pygame.display.set_mode((320, 240))
clock = pygame.time.Clock()


async def main():
    count = 60

    while True:
        print(f"{count}: Hello from Pygame")
        screen.fill((255, 255, 255))
        pygame.display.update()
        await asyncio.sleep(0)  # You must include this statement in your main loop. Keep the argument at 0.

        if not count:
            pygame.quit()
            return
        
        count -= 1
        clock.tick(60)

asyncio.run(main())
