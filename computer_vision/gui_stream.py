# # gui_stream.py  —  Tk front-end + YOLOv8 ESP32-CAM tracker
# import cv2, sys, threading, queue, time
# from pathlib import Path
# from ultralytics import YOLO
# from tkinter import Tk, Label, Entry, Button, Checkbutton, IntVar, StringVar, Canvas, OptionMenu
#
# ESP_IP  = "192.168.4.1"
# URL     = f"http://{ESP_IP}/stream"
# MODEL   = Path("runs/detect/train5/weights/best.pt")  # put your real path here
# IMG_SZ  = 640
# CONF    = 0.30
# THR_PX  = 40               # distance in px to declare “Grab!”
#
# # ────────── worker thread ──────────
# def detect_loop(target_var: StringVar, show_vid: IntVar, q: queue.Queue):
#     model = YOLO(MODEL)
#     cap   = cv2.VideoCapture(URL)
#     if not cap.isOpened():
#         q.put(("err", "Stream open failed")); return
#
#     cX, cY = IMG_SZ // 2, IMG_SZ // 2   # assume square frames
#     while cap.isOpened():
#         ok, frame = cap.read()
#         if not ok:
#             q.put(("err", "Stream lost")); break
#
#         res = model.predict(frame, imgsz=IMG_SZ, conf=CONF, verbose=False)[0]
#         tgt = target_var.get().strip().lower()
#         found = None
#         for b in res.boxes:
#             if model.names[int(b.cls[0])].lower() == tgt:
#                 x1,y1,x2,y2 = map(int, b.xyxy[0])
#                 cx, cy = (x1+x2)//2, (y1+y2)//2
#                 cy += int(IMG_SZ * 0.3)  # approx 4% of image height as 4cm offset
#                 found = (cx, cy)
#                 if show_vid.get():
#                     cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
#                 break
#
#         if show_vid.get():                        # 1️⃣ debug mode
#             if found:
#                 cv2.arrowedLine(frame, (cX,cY), found, (0,0,255), 2, tipLength=.3)
#                 if abs(found[0]-cX)**2 + abs(found[1]-cY)**2 < THR_PX**2:
#                     cv2.putText(frame, "GRAB!", (cX-60,50),
#                                 cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)
#             cv2.imshow("ESP32-YOLO", frame)
#             if cv2.waitKey(1)&0xFF==ord('q'):
#                 show_vid.set(0)            # switch to pointer-only
#                 cv2.destroyAllWindows()
#
#         else:                                       # 2️⃣ pointer-only
#             q.put(("vec", found))
#
#     cap.release()
#     cv2.destroyAllWindows()
#
# # ────────── Tk UI ──────────
# root = Tk(); root.title("Object Finder")
#
# Label(root, text="Target:").grid(row=0, column=0, padx=4, pady=4)
# target = StringVar(value="cube")
# options = ["cube", "cylinder"]
# target = StringVar(value=options[0])
# opt_menu = OptionMenu(root, target, *options)
# opt_menu.grid(row=0, column=1, padx=4)
#
# show_vid = IntVar(value=1)
# Checkbutton(root, text="Show video", variable=show_vid).grid(row=0, column=2)
#
# btn_state = StringVar(value="Start")
# q = queue.Queue()
#
# def toggle():
#     if btn_state.get()=="Start":
#         t = threading.Thread(target=detect_loop, args=(target,show_vid,q), daemon=True)
#         t.start(); btn_state.set("Stop"); start_btn.config(textvariable=btn_state)
#     else:
#         show_vid.set(0); btn_state.set("Start"); start_btn.config(textvariable=btn_state)
#
# start_btn = Button(root, textvariable=btn_state, width=10, command=toggle)
# start_btn.grid(row=0, column=3, padx=6)
#
# # canvas for arrow mode
# CAN = 200; canv = Canvas(root, width=CAN, height=CAN, bg="#eee"); canv.grid(row=1,column=0,columnspan=4,pady=8)
# centre = CAN//2
#
# def ui_loop():
#     while not q.empty():
#         tag, data = q.get()
#         if tag=="err":
#             root.title(f"Error: {data}")
#         elif tag=="vec":
#             canv.delete("all")
#             if data:
#                 dx, dy = data[0]-IMG_SZ//2, data[1]-IMG_SZ//2
#                 d2 = dx*dx+dy*dy
#                 if d2 < THR_PX*THR_PX:
#                     canv.create_text(centre, 20, text="GRAB!", fill="red", font=("Arial", 18, "bold"))
#                 # normalise arrow length
#                 if d2>0:
#                     scale = (0.8*centre) / (d2**0.5)
#                     ex, ey = centre + dx*scale, centre + dy*scale
#                     canv.create_line(centre,centre,ex,ey,arrow="last",width=3,fill="red")
#             else:
#                 canv.create_text(centre, centre, text="–", font=("Arial", 24))
#     root.after(30, ui_loop)
#
# root.after(100, ui_loop)
# root.mainloop()

import cv2
import threading
import queue
from pathlib import Path
from tkinter import *
from ultralytics import YOLO

ESP_IP  = "192.168.4.1"
URL     = f"http://{ESP_IP}/stream"
MODEL   = Path("runs/detect/train5/weights/best.pt")
IMG_SZ  = 640
CONF    = 0.30
THR_PX  = 40

# ────────── worker thread ──────────
def detect_loop(target_var: StringVar, show_vid: IntVar, q: queue.Queue):
    model = YOLO(MODEL)
    cap   = cv2.VideoCapture(URL)
    if not cap.isOpened():
        q.put(("err", "Stream open failed")); return

    cX, cY = IMG_SZ // 2, IMG_SZ // 2
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            q.put(("err", "Stream lost")); break

        res = model.predict(frame, imgsz=IMG_SZ, conf=CONF, verbose=False)[0]
        tgt = target_var.get().strip().lower()
        found = None
        for b in res.boxes:
            if model.names[int(b.cls[0])].lower() == tgt:
                x1,y1,x2,y2 = map(int, b.xyxy[0])
                cx, cy = (x1+x2)//2, (y1+y2)//2
                cy -= int(IMG_SZ * 0.04)  # apply 4cm vertical offset
                found = (cx, cy)
                if show_vid.get():
                    cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)
                break

        if show_vid.get():
            if found:
                cv2.arrowedLine(frame, (cX,cY), found, (255,255,255), 2, tipLength=.3)
                if abs(found[0]-cX)**2 + abs(found[1]-cY)**2 < THR_PX**2:
                    cv2.putText(frame, "GRAB!", (cX-60,50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
            cv2.imshow("ESP32-YOLO", frame)
            if cv2.waitKey(1)&0xFF==ord('q'):
                show_vid.set(0)
                cv2.destroyAllWindows()
        else:
            q.put(("vec", found))

    cap.release()
    cv2.destroyAllWindows()

# ────────── Tkinter UI ──────────
root = Tk()
root.title("Object Grabber")
root.configure(bg="black")

font_cfg = ("Arial", 16)
fg_cfg = {"fg": "white", "bg": "black", "font": font_cfg}

Label(root, text="Target:", **fg_cfg).grid(row=0, column=0, padx=6, pady=6)

options = ["cube", "cylinder"]
target = StringVar(value=options[0])
opt_menu = OptionMenu(root, target, *options)
opt_menu.config(**fg_cfg, highlightthickness=0)
opt_menu["menu"].config(bg="black", fg="white", font=font_cfg)
opt_menu.grid(row=0, column=1, padx=6)

show_vid = IntVar(value=1)
Checkbutton(root, text="Show video", variable=show_vid, selectcolor="black", **fg_cfg).grid(row=0, column=2, padx=6)

btn_state = StringVar(value="Start")
q = queue.Queue()

def toggle():
    if btn_state.get() == "Start":
        t = threading.Thread(target=detect_loop, args=(target, show_vid, q), daemon=True)
        t.start()
        btn_state.set("Stop")
        start_btn.config(textvariable=btn_state)
    else:
        show_vid.set(0)
        btn_state.set("Start")
        start_btn.config(textvariable=btn_state)

bottom_frame = Frame(root, bg="black")
bottom_frame.grid(row=2, column=0, columnspan=4, pady=10)

start_btn = Button(bottom_frame, textvariable=btn_state, width=12, command=toggle, **fg_cfg)
start_btn.pack()

# Canvas for pointer
CAN = 250
canv = Canvas(root, width=CAN, height=CAN, bg="black", highlightthickness=0)
canv.grid(row=1, column=0, columnspan=4, pady=12)
centre = CAN // 2

def ui_loop():
    while not q.empty():
        tag, data = q.get()
        if tag == "err":
            root.title(f"Error: {data}")
        elif tag == "vec":
            canv.delete("all")
            if data:
                dx, dy = data[0] - IMG_SZ // 2, data[1] - IMG_SZ // 2
                d2 = dx * dx + dy * dy
                if d2 < THR_PX * THR_PX:
                    canv.create_text(centre, 30, text="GRAB!", fill="red", font=("Arial", 24, "bold"))
                elif d2 > 0:
                    scale = (0.8 * centre) / (d2 ** 0.5)
                    ex, ey = centre + dx * scale, centre + dy * scale
                    canv.create_line(centre, centre, ex, ey, arrow="last", width=4, fill="white")
            else:
                canv.create_text(centre, centre, text="–", fill="white", font=("Arial", 24))
    root.after(30, ui_loop)

root.after(100, ui_loop)
root.mainloop()
