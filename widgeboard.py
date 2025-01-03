import tkinter as tk
from time import strftime


def make_draggable(widget):
    widget.bind("<Button-1>", on_drag_start)
    widget.bind("<B1-Motion>", on_drag_motion)

def on_drag_start(event):
    widget = event.widget
    widget._drag_start_x = event.x
    widget._drag_start_y = event.y

def on_drag_motion(event):
    widget = event.widget
    x = widget.winfo_x() - widget._drag_start_x + event.x
    y = widget.winfo_y() - widget._drag_start_y + event.y
    widget.place(x=x, y=y)

class DragDropMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        make_draggable(self)

class DnDFrame(DragDropMixin, tk.Frame):
    pass

def time():
    string = strftime('%H:%M:%S %p')
    clockLabel.config(text=string)
    clockLabel.after(1000, time)

window = tk.Tk()
window.geometry("800x800")
window.title("drag'n drop")

notesFrame = DnDFrame(window, bd=10, bg="grey")
notesFrame.place(x=10, y=10)
notes = tk.Text(notesFrame)
notes.pack()

clockFrame = DnDFrame(window, bd=10, bg="grey")
clockFrame.pack()
clockLabel = tk.Label(clockFrame, font=('Calibri', 40, 'bold'), background='purple', foreground='white')
clockLabel.pack(anchor='center')

time()
window.mainloop()
