import traceback

import tcod

import color
import exceptions
import input_handlers
import setup_game


def save_game(handler: input_handlers.BaseEventHandler, filename: str) -> None:
    """ If the current even handler has an active Engine then save it. """
    if isinstance(handler, input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    screen_width = 80  # Width, in pixels, of screen
    screen_height = 50  # Height, in pxels, of screen

    # Load tileset
    # tileset = tcod.tileset.load_tilesheet("dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD)
    tileset = tcod.tileset.load_tilesheet("Md_curses_16x16.png", 16, 16, tcod.tileset.CHARMAP_CP437)

    handler: input_handlers.BaseEventHandler = setup_game.MainMenu()

    with tcod.context.new_terminal(  # Initialize console window
        screen_width,  # Console width, in pixels.
        screen_height,  # Console height, in pixels.
        tileset=tileset,  # Tileset to be used.
        title="Yet Another Roguelike Tutorial",  # Title of console window.
        vsync=True
    ) as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")  # Create console in buffer
        try:
            while True:  # Main loop
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, input_handlers.EventHandler):
                        handler.engine.message_log.add_message(
                            traceback.format_exc(), color.error
                        )
        except exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and exit.
            save_game(handler, "savegame.sav")
            raise
        except BaseException:  # Save on any other unexpected exception.
            save_game(handler, "savegame.sav")
            raise

if __name__ == "__main__":
    main()
