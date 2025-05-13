import unittest
import io
import sys
from tkinter import Tk, Text, Scrollbar, Button, END, Label, Entry, filedialog, ttk
from subprocess import Popen, PIPE
from tkinter import messagebox


class TestRunner:
    def __init__(self):
        self.output = ""

    def run_tests(self, test_suite):
        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(test_suite)
        self.output = stream.getvalue()
        return result


class TestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flask App Test Runner")

        self.notebook = ttk.Notebook(root)
        self.unit_test_tab = ttk.Frame(self.notebook)
        self.integration_test_tab = ttk.Frame(self.notebook)
        self.performance_test_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.unit_test_tab, text="Unit Tests")
        self.notebook.add(self.integration_test_tab, text="Integration Tests")
        self.notebook.add(self.performance_test_tab, text="Performance Tests")
        self.notebook.pack(expand=1, fill="both")

        self._create_test_tab(self.unit_test_tab, self.run_unit_tests)
        self._create_test_tab(self.integration_test_tab, self.run_integration_tests)
        self._create_performance_tab()

    def _create_test_tab(self, tab, run_function):
        label = Label(tab, text="Run Tests", font=("Arial", 16))
        label.pack(pady=10)

        text = Text(tab, wrap="word", width=80, height=20)
        scrollbar = Scrollbar(tab, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        Button(tab, text="Run Tests", command=lambda: run_function(text)).pack(pady=5)
        Button(tab, text="Clear Output", command=lambda: text.delete(1.0, END)).pack(pady=5)
        Button(tab, text="Save Results", command=lambda: self.save_results(text)).pack(pady=5)

    def _create_performance_tab(self):
        label = Label(self.performance_test_tab, text="Run Performance Tests", font=("Arial", 16))
        label.pack(pady=10)

        self.locust_users = self._create_input_field("Number of Users:", "10", self.performance_test_tab)
        self.locust_rate = self._create_input_field("Spawn Rate:", "1", self.performance_test_tab)
        self.locust_runtime = self._create_input_field("Run Time:", "1m", self.performance_test_tab)

        text = Text(self.performance_test_tab, wrap="word", width=80, height=20)
        scrollbar = Scrollbar(self.performance_test_tab, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        Button(self.performance_test_tab, text="Run Tests", command=lambda: self.run_performance_tests(text)).pack(pady=5)
        Button(self.performance_test_tab, text="Clear Output", command=lambda: text.delete(1.0, END)).pack(pady=5)

    def _create_input_field(self, label_text, default_value, parent):
        frame = ttk.Frame(parent)
        frame.pack(pady=5)

        Label(frame, text=label_text).pack(side="left")
        entry = Entry(frame)
        entry.insert(0, default_value)
        entry.pack(side="right")
        return entry

    def run_unit_tests(self, output_widget):
        output_widget.delete(1.0, END)
        loader = unittest.TestLoader()
        test_suite = loader.discover(start_dir="./tests", pattern="test_*.py")
        runner = TestRunner()
        runner.run_tests(test_suite)
        self._display_output(output_widget, runner.output)

    def run_integration_tests(self, output_widget):
        output_widget.delete(1.0, END)
        loader = unittest.TestLoader()
        test_suite = loader.discover(start_dir="./tests/integration", pattern="test_*.py")
        runner = TestRunner()
        runner.run_tests(test_suite)
        self._display_output(output_widget, runner.output)

    def run_performance_tests(self, output_widget):
        output_widget.delete(1.0, END)
        locust_file = filedialog.askopenfilename(
            title="Select Locust Test File", filetypes=[("Python Files", "*.py")]
        )
        if not locust_file:
            output_widget.insert(END, "No Locust test file selected.\n")
            return

        users = self.locust_users.get()
        rate = self.locust_rate.get()
        runtime = self.locust_runtime.get()

        command = [
            "locust",
            "-f", locust_file,
            "--headless",
            "-u", users,
            "-r", rate,
            "--run-time", runtime,
        ]
        process = Popen(command, stdout=PIPE, stderr=PIPE, text=True)
        stdout, stderr = process.communicate()

        if stdout:
            output_widget.insert(END, "=== Locust Output ===\n" + stdout)
        if stderr:
            output_widget.insert(END, "\n=== Errors ===\n" + stderr)

    def _display_output(self, widget, output):
        for line in output.splitlines():
            if "OK" in line or "PASS" in line:
                widget.insert(END, line + "\n", "success")
            elif "FAIL" in line or "ERROR" in line:
                widget.insert(END, line + "\n", "error")
            else:
                widget.insert(END, line + "\n")
        widget.tag_config("success", foreground="green")
        widget.tag_config("error", foreground="red")

    def save_results(self, text_widget):
        content = text_widget.get(1.0, END).strip()
        if not content:
            messagebox.showinfo("Save Results", "No results to save!")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text Files", "*.txt")]
        )
        if filepath:
            with open(filepath, "w") as file:
                file.write(content)
            messagebox.showinfo("Save Results", f"Results saved to {filepath}")


if __name__ == "__main__":
    root = Tk()
    app = TestApp(root)
    root.mainloop()
