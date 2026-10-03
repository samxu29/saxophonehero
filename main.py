import sys

from visualizer import SaxophoneVisualizer


def main():
    midi_file = sys.argv[1] if len(sys.argv) > 1 else "test.mid"
    try:
        visualizer = SaxophoneVisualizer(midi_file)
        visualizer.run()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
