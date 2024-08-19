import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, UnidentifiedImageError
import numpy as np
import cv2
import os
import pytesseract
class ImageApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Viewer")
        self.root.configure(bg="#2C3E50")

        self.img = None  
        self.original_img = None  
        self.img_tk = None
        self.img_with_drawings = None
        self.drawing = False
        self.paint_color = "black"
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_end_x = None
        self.crop_end_y = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # نوار منو
        self.menu_bar = tk.Menu(root)
        #self.menu_bar.configure(bg="#D3D3D3")
        root.config(menu=self.menu_bar)

        # منوی فایل
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#34495E", fg="white")
        self.menu_bar.add_cascade(label="فایل", menu=self.file_menu)
        self.file_menu.add_command(label="باز کردن تصویر", command=self.open_image)
        self.file_menu.add_command(label="ذخیره تصویر", command=self.save_image)
        self.file_menu.add_command(label="اطلاعات تصویر", command=self.show_image_info)
        self.file_menu.add_command(label="بازگشت به حالت اولیه", command=self.reset_to_original)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="خروج", command=root.quit)

        # منوی ویرایش
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#34495E", fg="white")
        self.menu_bar.add_cascade(label="ویرایش", menu=self.edit_menu)
        self.edit_menu.add_command(label="چرخاندن به چپ", command=self.rotate_left)
        self.edit_menu.add_command(label="چرخاندن به راست", command=self.rotate_right)
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="کراپ تصویر", command=self.start_crop)

        # منوی بهسازی تصویر
        self.enhance_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#34495E", fg="white")
        self.menu_bar.add_cascade(label="بهسازی تصویر", menu=self.enhance_menu)
        self.enhance_menu.add_command(label="histogram_stretching", command=self.histogram_stretching)
        self.enhance_menu.add_command(label="histogram_equalization", command=self.histogram_equalization)
        self.enhance_menu.add_command(label="CLAHE", command=self.clahe)
        self.enhance_menu.add_command(label="افزایش وضوح", command=self.sharpness_enhancement)
        self.enhance_menu.add_command(label="smoothing", command=self.smoothing)

        # منوی نقاشی
        self.paint_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#34495E", fg="white")
        self.menu_bar.add_cascade(label="نقاشی", menu=self.paint_menu)
        self.paint_menu.add_command(label="فعال کردن نقاشی", command=self.toggle_drawing)
        self.paint_menu.add_command(label="انتخاب رنگ", command=self.choose_color)
        self.paint_menu.add_command(label="پاک کردن نقاشی", command=self.clear_drawing)  # اضافه کردن گزینه پاک کردن
        # منوی افکت
        self.effect_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#34495E", fg="white")
        self.menu_bar.add_cascade(label="افکت", menu=self.effect_menu)
        self.effect_menu.add_command(label="افزایش کنتراست", command=self.contrast_enhancement)
        self.effect_menu.add_command(label="افزایش روشنایی", command=self.brightness_enhancement)
        self.effect_menu.add_command(label="تبدیل به سیاه و سفید", command=self.convert_to_grayscale)

        self.ai_menu = tk.Menu(self.menu_bar, tearoff=0, bg="#34495E", fg="white")
        self.menu_bar.add_cascade(label="تشخیص", menu=self.ai_menu)
        self.ai_menu.add_command(label="تشخیص چهره", command=self.detect_faces)
        #self.ai_menu.add_command(label="تشخیص چهره", command=self.detect_faces)
        self.ai_menu.add_command(label="لبه یابی,", command=self.detect_edges)
        self.ai_menu.add_command(label="تشخیص متن", command=self.detect_text)


        # محل نمایش تصویر
        self.canvas = tk.Canvas(root, bg="white", bd=0, highlightthickness=0)
        self.canvas.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        # اتصال ماوس به متدهای نقاشی و کراپ
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        self.canvas.bind("<Button-1>", self.start_crop_point)

    def toggle_drawing(self):
        self.drawing = not self.drawing
        if self.drawing:
            self.paint_menu.entryconfig("فعال کردن نقاشی", label="غیرفعال کردن نقاشی")
            self.canvas.bind("<B1-Motion>", self.paint)
        else:
            self.paint_menu.entryconfig("غیرفعال کردن نقاشی", label="فعال کردن نقاشی")
            self.canvas.bind("<B1-Motion>", self.reset)
        
    def choose_color(self):
        color_code = colorchooser.askcolor(title="انتخاب رنگ نقاشی")
        if color_code:
            self.paint_color = color_code[1]

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")])
        if file_path:
            try:
                self.img = Image.open(file_path)
                self.original_img = self.img.copy()  # ذخیره تصویر اصلی
                self.img_with_drawings = self.img.copy()
                self.resize_canvas_to_image()
                self.display_image()
                self.image_path = file_path  # ذخیره مسیر فایل برای گرفتن اطلاعات فایل
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except UnidentifiedImageError:
                print(f"Cannot identify image file: {file_path}")

    def reset_to_original(self):
        if self.original_img:
            self.img = self.original_img.copy()  # بازگرداندن تصویر به حالت اصلی
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def resize_canvas_to_image(self):
        if self.img:
            width, height = self.img.size
            self.canvas.config(width=width, height=height)

    def display_image(self):
        if self.img:
            img_resized = self.img.resize((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.LANCZOS)
            self.img_tk = ImageTk.PhotoImage(img_resized)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

    def rotate_left(self):
        if self.img:
            self.img = self.img.rotate(90, expand=True)
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def rotate_right(self):
        if self.img:
            self.img = self.img.rotate(-90, expand=True)
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def start_crop(self):
        if self.img:
            self.canvas.bind("<Button-1>", self.start_crop_point)
            self.canvas.bind("<B1-Motion>", self.update_crop_rectangle)
            self.canvas.bind("<ButtonRelease-1>", self.crop_image)

    def start_crop_point(self, event):
        self.crop_start_x = event.x
        self.crop_start_y = event.y
        self.canvas.delete("crop_rectangle")

    def update_crop_rectangle(self, event):
        if self.crop_start_x is not None and self.crop_start_y is not None:
            self.crop_end_x = event.x
            self.crop_end_y = event.y
            self.canvas.delete("crop_rectangle")
            self.canvas.create_rectangle(
                self.crop_start_x,
                self.crop_start_y,
                self.crop_end_x,
                self.crop_end_y,
                outline="red",
                width=2,
                tags="crop_rectangle"
            )

    def crop_image(self, event):
        if self.img and self.crop_start_x is not None and self.crop_start_y is not None and self.crop_end_x is not None and self.crop_end_y is not None:
            left = min(self.crop_start_x, self.crop_end_x)
            top = min(self.crop_start_y, self.crop_end_y)
            right = max(self.crop_start_x, self.crop_end_x)
            bottom = max(self.crop_start_y, self.crop_end_y)
            img_cropped = self.img.crop((left, top, right, bottom))
            self.img = img_cropped
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()
            self.canvas.unbind("<Button-1>")
            self.canvas.unbind("<B1-Motion>")
            self.canvas.unbind("<ButtonRelease-1>")

    def paint(self, event):
        if self.drawing and self.img_with_drawings:
            # شبیه‌سازی رسم خط پیوسته با استفاده از نقاط کوچک
            x1, y1 = (event.x - 1), (event.y - 1)
            x2, y2 = (event.x + 1), (event.y + 1)
            self.canvas.create_line(x1, y1, x2, y2, fill=self.paint_color, width=10)  # افزایش عرض خط
            draw = ImageDraw.Draw(self.img_with_drawings)
            draw.line([x1, y1, x2, y2], fill=self.paint_color, width=10)  # افزایش عرض خط


    def reset(self, event):
        pass

    def save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("JPEG files", "*.jpg"),
                                                            ("All files", "*.*")])
        if file_path:
            try:
                if self.img_with_drawings:
                    img_resized = self.img_with_drawings.resize((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.LANCZOS)
                    img_resized.save(file_path)
                else:
                    final_image = Image.new("RGB", (self.canvas.winfo_width(), self.canvas.winfo_height()), "white")
                    final_image.save(file_path)
                print(f"Image saved to: {file_path}")
            except Exception as e:
                print(f"Error saving image: {e}")

    def show_image_info(self):
        if self.img:
            width, height = self.img.size
            format = self.img.format if self.img.format else "نامشخص"
            size = os.path.getsize(self.image_path) / 1024  # محاسبه اندازه فایل به کیلوبایت
            info = f"ابعاد: {width}x{height}\nفرمت: {format}\nاندازه فایل: {size:.2f} کیلوبایت"
            messagebox.showinfo("اطلاعات تصویر", info)
        else:
            messagebox.showwarning("اطلاعات تصویر", "تصویری بارگذاری نشده است.")

    def histogram_stretching(self):
        if self.img:
            img_cv = np.array(self.img.convert('L'))
            p2, p98 = np.percentile(img_cv, (2, 98))
            img_rescaled = np.clip((img_cv - p2) / (p98 - p2) * 255, 0, 255).astype(np.uint8)
            img_stretched = Image.fromarray(img_rescaled)
            self.img = img_stretched
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def histogram_equalization(self):
        if self.img:
            img_cv = cv2.cvtColor(np.array(self.img), cv2.COLOR_RGB2GRAY)
            img_eq = cv2.equalizeHist(img_cv)
            img_eq_rgb = cv2.cvtColor(img_eq, cv2.COLOR_GRAY2RGB)
            img_equalized = Image.fromarray(img_eq_rgb)
            self.img = img_equalized
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def clahe(self):
        if self.img:
            img_cv = cv2.cvtColor(np.array(self.img), cv2.COLOR_RGB2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            img_clahe = clahe.apply(img_cv)
            img_clahe_rgb = cv2.cvtColor(img_clahe, cv2.COLOR_GRAY2RGB)
            img_clahe_img = Image.fromarray(img_clahe_rgb)
            self.img = img_clahe_img
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def sharpness_enhancement(self):
        if self.img:
            enhancer = ImageEnhance.Sharpness(self.img)
            img_sharp = enhancer.enhance(2.0)
            self.img = img_sharp
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def smoothing(self):
        if self.img:
            img_cv = np.array(self.img)
            img_smoothed = cv2.GaussianBlur(img_cv, (5, 5), 0)
            img_smoothed_pil = Image.fromarray(img_smoothed)
            self.img = img_smoothed_pil
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    # افکت‌های جدید
    def contrast_enhancement(self):
        if self.img:
            enhancer = ImageEnhance.Contrast(self.img)
            img_contrast = enhancer.enhance(2.0)
            self.img = img_contrast
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def brightness_enhancement(self):
        if self.img:
            enhancer = ImageEnhance.Brightness(self.img)
            img_bright = enhancer.enhance(1.5)
            self.img = img_bright
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def convert_to_grayscale(self):
        if self.img:
            img_gray = self.img.convert("L")
            img_gray_rgb = Image.merge("RGB", (img_gray, img_gray, img_gray))
            self.img = img_gray_rgb
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()

    def detect_faces(self):
        if self.img:
            img_cv = np.array(self.img)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            for (x, y, w, h) in faces:
                cv2.rectangle(img_cv, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            img_with_faces = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
            self.img = img_with_faces
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()
    def detect_edges(self):
        if self.img:
            img_cv = np.array(self.img)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            self.img = Image.fromarray(cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB))
            self.img_with_drawings = self.img.copy()
            self.resize_canvas_to_image()
            self.display_image()
    def clear_drawing(self):
        if self.img_with_drawings:
            # پاک کردن نقاشی‌ها از تصویر
            self.img_with_drawings = self.img.copy()
            self.display_image()
    def detect_text(self):
        messagebox.showwarning("اطلاعات تصویر", "انشالله در بروزرسانی بعدی منتظر حضور شما سرور گرامی هستیم:))))))"   )
    #     if self.img:
    #         try:

    #             # تبدیل تصmessagebox.showwarning("اطلاعات تصویر", "تصویری بارگذاری نشده است.")ویر به متن
    #             img_text = pytesseract.image_to_string(self.img, lang='eng')  # می‌توانید زبان‌های مختلف را تنظیم کنید
    #             messagebox.showinfo("تشخیص متن", img_text)
    #         except Exception as e:
    #             messagebox.showerror("خطا", f"خطا در تشخیص متن: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageApp(root)
    root.mainloop()
