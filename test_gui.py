import unittest
import io
import sys
from tkinter import Tk, Text, Scrollbar, Button, END, Label, filedialog


# A helper class to capture unittest output
class TestRunner:
    def __init__(self):
        self.output = ""

    def run_tests(self, test_suite):
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(test_suite)
        self.output = stream.getvalue()
        return result


# GUI Application
class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Test Runner")

        # Add a label
        self.label = Label(root, text="Run Unit Tests", font=("Arial", 16))
        self.label.pack(pady=10)

        # Text widget with a scrollbar for output
        self.text = Text(root, wrap="word", width=80, height=20)
        self.scrollbar = Scrollbar(root, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        self.text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.scrollbar.pack(side="right", fill="y")

        # Buttons
        self.run_button = Button(root, text="Run Tests", command=self.run_tests)
        self.run_button.pack(pady=5)

        self.clear_button = Button(root, text="Clear Output", command=self.clear_output)
        self.clear_button.pack(pady=5)

    def run_tests(self):
        # Clear previous output
        self.text.delete(1.0, END)

        # Discover and run tests
        loader = unittest.TestLoader()
        test_suite = loader.discover(
            start_dir=".", pattern="test_app.py"
        )  # Adjust to your test file
        runner = TestRunner()
        runner.run_tests(test_suite)

        # Display output
        self.text.insert(END, runner.output)

    def clear_output(self):
        self.text.delete(1.0, END)


# Main function to run the GUI
if __name__ == "__main__":
    root = Tk()
    app = TestApp(root)
    root.mainloop()
